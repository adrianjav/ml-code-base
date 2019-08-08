from pathlib import Path
import sys
import inspect
import dill
import atexit
from functools import partial, wraps, partialmethod
from typing import Callable

from mlsuite.options import Options
from mlsuite.directories import Directories
from mlsuite import directories as dirs

# TODO check *args, **kwargs on calls to load or not (safe hash of the parameters)


class GlobalOptions(metaclass=Options):
    _opt_inherit_on_creation = False
    _opt_load_on_init = True
    _opt_save_on_del = True
    _opt_remove_on_completion = False
    _opt_failsafe_folder = dirs


# Default functions

def default_remove(path):
    path = Path(path)
    if path.exists() and path.is_file():
        path.unlink()


def default_save(self, path):
    with open(path, 'wb') as file:
        dill.dump(self, file)


def default_load(path):
    path = Path(path)
    if path.exists():
        with path.open('rb') as file:
            return dill.load(file)
    else:
        return None


def default_filename(name=None):
    def __filename__(self, id):
        return f'{name or type(self).__qualname__}_{id}.pickle'
    return __filename__


def default_getstate(self):
    return self.__dict__


def default_setstate(self, state):
    self.__dict__.udpdate(state)


def failsafe_getstate(getstate):
    @wraps(getstate)
    def failsafe_getstate_(self):
        state = getstate(self)
        state.update({'_oid': self._oid})
        return state
    return failsafe_getstate_


def failsafe_setstate(setstate):
    @wraps(setstate)
    def failsafe_setstate_(self, state):
        self._oid = state.pop('_oid')
        setstate(self, state)
    return failsafe_setstate_


class FailSafe(Options):
    """
    Metaclass that ensures to save an object whenever the program finishes and load it at initialization in a
    transparent way. Besides, it can be selected whether or not remove the files once the program has properly
    finished.
    """
    class Guardian(GlobalOptions):
        """
        Class from which everyone with metaclass=FailSafe is going to inherit in a transparent way.
        """

        @staticmethod
        def _atexit_template(self) -> None:
            if sys.exit_code == 0 and self.remove_on_completion.value() and self.save_on_del.value():
                self.remove(self.__path__)
                self.save_on_del.value(False)

            if self.save_on_del.value():
                try:
                    self.save(self.__path__)
                except Exception as e:
                    print(f'{id(self)} An exception happened while saving {self.__path__}: {e}', file=sys.stderr)
                    self.remove(self.__path__)
                    raise

            atexit.unregister(self._atexit)

        @classmethod
        def __reset_id__(cls):
            cls._unique_id = 0

        @property
        def __path__(self):
            assert isinstance(self.failsafe_folder.value(), Directories), f'Expected type: {Directories.__name__}, Actual: {type(self.failsafe_folder.value())}'
            return f'{str(self.failsafe_folder.value())}/{self.__filename__(self._oid)}'

        def __init__(self, *args, **kwargs):
            super(FailSafe.Guardian, self).__init__(*args, **kwargs)

        @staticmethod
        def init_or_load(self, __init__, *args, **kwargs):
            type(self)._unique_id += 1  # For the same version of the code the id should be the same
            self._oid = type(self)._unique_id

            if self.load_on_init.value():
                with GlobalOptions.load_on_init(False), GlobalOptions.save_on_del(False):
                    from .wrapper import FailSafeWrapper
                    if isinstance(self, FailSafeWrapper):
                        if 'func' in kwargs:
                            path = f'{str(self.failsafe_folder.value())}/{kwargs["func"].__name__}_{self._oid}.pickle'
                        else:
                            path = f'{str(self.failsafe_folder.value())}/{args[0].__name__}_{self._oid}.pickle'
                    else:
                        path = self.__path__
                    res = self.load(path)

                if res is not None:
                    type(res).decorate(res)  # depending on the load function this might not be called

                    # As Failsafe.__call__ might not get called I have to force it to inherit the options
                    for attr in [v for v in dir(res) if v.startswith('_opt_')]:
                        setattr(res, attr, getattr(res, attr[len('_opt_'):]).value())

                    self.__dict__.update(res.__dict__)  # TODO slots?
                    object.__setattr__(res, '_atexit', partial(FailSafe.Guardian._atexit_template, res))

                else:
                    __init__(self, *args, **kwargs)
            else:
                __init__(self, *args, **kwargs)

            # assert self_id == self._obj_id, f'{self_id}, {self._obj_id}, {type(self)}'
            object.__setattr__(self, '_atexit', partial(FailSafe.Guardian._atexit_template, self))
            atexit.register(self._atexit)

    def __init__(cls, name, bases, namespace, loader=None, saver=None, remover=None, filename=None):
        super(FailSafe, cls).__init__(name, bases, namespace)

        cls.__init__ = partialmethod(FailSafe.Guardian.init_or_load, cls.__init__)

        if isinstance(filename, str): filename = default_filename(filename)

        setattr(cls, 'save', saver or getattr(cls, 'save', default_save))
        setattr(cls, 'load', staticmethod(loader or getattr(cls, 'load', default_load)))
        setattr(cls, 'remove', staticmethod(remover or getattr(cls, 'remove', default_remove)))
        setattr(cls, '__filename__', partialmethod(filename or getattr(cls, '__filename__', default_filename())))

        setattr(cls, '__getstate__', failsafe_getstate(getattr(cls, '__getstate__', default_getstate)))
        setattr(cls, '__setstate__', failsafe_setstate(getattr(cls, '__setstate__', default_setstate)))

        assert isinstance(cls.load, Callable), 'The "load" property has to be callable.'
        assert not inspect.ismethod(cls.load) or cls.load.__self__ is cls, 'the "load" method has to be of type ' \
                                                                           '"staticmethod" or "classmethod"'

    def __call__(self, *args, **kwargs):
        instance = super(FailSafe, self).__call__(*args, **kwargs)

        if self.inherit_on_creation.value():
            for attr in [v for v in dir(instance) if v.startswith('_opt_')]:
                setattr(instance, attr, getattr(instance, attr[len('_opt_'):]).value())

        return instance

    @classmethod
    def __prepare__(mcs, name, bases, **kwargs):
        if not any([issubclass(cls, FailSafe.Guardian) for cls in bases]):
            bases = (FailSafe.Guardian,) + bases
        namespace = super(FailSafe, mcs).__prepare__(name, bases, **kwargs)
        namespace.update({'_unique_id': 0})
        return namespace

    def __new__(metacls, name, bases, namespace, **kwargs):
        if not any([issubclass(cls, FailSafe.Guardian) for cls in bases]):
            bases = (FailSafe.Guardian,) + bases

        return super(FailSafe, metacls).__new__(metacls, name, bases, namespace)

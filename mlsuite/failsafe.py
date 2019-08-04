from pathlib import Path
import sys
import inspect
import dill
import atexit
from functools import partial, wraps, partialmethod
from typing import Callable

from .options import Options
from .directories import Directories
from mlsuite import directories as dirs


# Code to ensure that there is an exit code that we can check when exiting (an act wrt it)

def exit_hook(func):
    @wraps(func)
    def _exit_hook(code=0):
        sys.exit_code = code
        func(code)
    return _exit_hook


def except_hook(func):  # TODO it breaks when debugging with PyCharm
    @wraps(func)
    def except_hook_(*args, **kwargs):
        sys.exit_code = None
        func(*args, **kwargs)
    return except_hook_


def exit_assert():
    assert hasattr(sys, 'exit_code'), 'Make sure to call "sys.exit" in your program.'  # TODO exit function?


atexit.register(exit_assert)
sys.exit = exit_hook(sys.exit)
sys.excepthook = except_hook(sys.excepthook)

# Until here


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
                    res = self.load(self.__path__)

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


# TODO for now this has the basic options (non-configurable at all)
class FailSafeWrapper(metaclass=FailSafe):
    def __init__(self, func, *args, **kwargs):
        try:
            self.wrapped = func(*args, **kwargs)
        except Exception:
            pass

    def __len__(self): return len(self.wrapped)
    def __iter__(self): return self.wrapped.__iter__()
    def __getitem__(self, item): return self.wrapped.__getitem__(item)

    @staticmethod
    def loadasas(path):
        result = default_load(path)
        if result.wrapper is None:
            return None
        return result

    def __getattr__(self, item):
        if item != 'wrapped':  # This happens if save is called when CPython is already shutting down
            return getattr(self.wrapped, item)
        raise AttributeError(item)

    def __str__(self):
        return str(self.wrapped)


def failsafe_result(func):
    @wraps(func)
    def failsafe_result_wrapper(*args, **kwargs):
        wrapper = FailSafeWrapper(func, *args, **kwargs)
        # wrapper.__filename__ = lambda oid: f'{func.__name__}_{oid}.pickle'
        return wrapper

    return failsafe_result_wrapper


def execute_once(func):
    @failsafe_result
    @wraps(func)
    def execute_once_(*args, **kwargs):
        result = func(*args, **kwargs)
        return result if result is not None else 1
    return execute_once_

# TODO check *args, **kwargs on calls to load or not (safe hash of the parameters)

################
# Example code #
################


if __name__ == '__main__':
    class Prueba(metaclass=FailSafe):
        @classmethod
        def __call__(cls, *args, **kwargs):
            print('call prueba')
            super().__call__(*args, **kwargs)

        def __init__(self, a, b, c):
            print(f'{type(self).__name__}.__init__')
            self.a = a
            self.b = b
            self.c = c

        def __del__(self):
            print(f'{type(self).__name__}.__del__')

        @classmethod
        def load(cls, filename):
            print(f'loading {cls.__name__} object from {filename}...')
            self = cls.__new__(cls)
            self.a = 1
            self.b = 2
            self.c = 4
            return self

        def save(self, filename):
            print(f'saving {type(self).__name__} object to {filename}...', id(self))

        def hola(self):
            print(self.a, self.b, self.c)


    cls = Prueba(1, 2, 3)
    cls.hola()

    def loadme(filename):
        print("loadme")
        cls = AnotherDummyClass
        self = cls.__new__(cls)
        self.a = 1
        self.b = 2
        self.c = 4
        return self

    class DummyClass(metaclass=FailSafe, loader=loadme):
        def __init__(self, a, b, c):
            print(f'{type(self).__name__}.__init__')
            self.a = a
            self.b = b
            self.c = c

        def __del__(self):
            print(f'{type(self).__name__}.__del__')
            pass

        def save(self, filename):
            print(f'saving {type(self).__name__} object to {filename}...', id(self))
            pass

        @classmethod
        def load(cls, filename):
            print(f'loading {cls.__name__} object from {filename}...')
            self = cls.__new__(cls)
            self.a = 1
            self.b = 2
            self.c = 3
            return self

        def __str__(self):
            return f'{self.a} {self.b} {self.c}'


    class AnotherDummyClass(DummyClass):
        def __init__(self, *args, **kwargs):
            super(AnotherDummyClass, self).__init__(*args, **kwargs)

        @classmethod
        def load(cls, filename):
            instance = super(AnotherDummyClass, cls).load(filename)
            instance.a = filename
            return instance

    with GlobalOptions.load_on_init(True):
        a = AnotherDummyClass(1, 2, 3)

    def save(self, path):
        print("saviiiiing")

    @failsafe_result  # (saver=save)
    def foo(p):
        print('ive been called')
        return p

    with GlobalOptions.inherit_on_creation(True), GlobalOptions.remove_on_completion(True):
        my_foo = foo('hola')
        my_foo2 = foo(2)

    print("HAHAH", my_foo, my_foo2)
    raise Exception
    #a.__del__()
    sys.exit(0)
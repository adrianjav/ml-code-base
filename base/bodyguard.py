import sys
import inspect
import atexit
from functools import partial, wraps
from typing import Callable

from base.utils import Options


# Code to ensure that there is an exit code that we can check when exiting (an act wrt it)

def exit_hook(func):
    @wraps(func)
    def _exit_hook(code=0):
        sys.exit_code = code
        func(code)
    return _exit_hook


def except_hook(func):
    @wraps(func)
    def _except_hook(*args, **kwargs):
        sys.exit_code = None
        func(*args, **kwargs)
    return _except_hook


def exit_assert():
    assert hasattr(sys, 'exit_code'), 'Make sure to call "sys.exit" in your program.'  # TODO exit function

atexit.register(exit_assert)
sys.exit = exit_hook(sys.exit)
sys.excepthook = except_hook(sys.excepthook)

# Until here


class GlobalOptions(metaclass=Options):
    _opt_load_on_init = False
    _opt_save_on_del = True
    _opt_remove_on_completion = False


# TODO temporary
def on_remove(self):
    print('removing', self._filename)


class FailSafe(Options):
    """
    Metaclass that ensures to save an object whenever the program finishes and load it at initialization in a
    transparent way. Besides, it can be selected whether or not remove the files once the program has properly
    finished.
    """

    class SafeLoadException(Exception):
        pass

    class Guardian(GlobalOptions):
        """
        Class from which everyone with metaclass=FailSafe is going to inherit in a transparent way.
        """

        @staticmethod
        def _atexit_template(self) -> None:
            if sys.exit_code == 0 and self.remove_on_completion.value():
                self.remove()
            else:
                self.__del__()

        @staticmethod
        def _atexit_completion(self) -> None:
            if sys.exit_code == 0:
                if self.remove_on_completion.value():
                    self.remove()

        def __init__(self, *args, **kwargs):
            type(self)._unique_id += 1  # For the same version of the code the id should be the same
            object.__setattr__(self, '_filename', f'{type(self).__qualname__}_{type(self)._unique_id}')

            if self.load_on_init.value():
                assert isinstance(self.load, Callable), 'The "load" property has to be callable.'
                assert not inspect.ismethod(self.load) or self.load.__self__ is type(self), 'the "load" method has ' \
                                                                                            'to be of type ' \
                                                                                            '"staticmethod" ' \
                                                                                            'or "classmethod"'
                res = self.load(self._filename)
                object.__setattr__(res, '_filename', f'{type(self).__name__}_{type(self)._unique_id}')
                object.__setattr__(res, '_atexit', partial(FailSafe.Guardian._atexit_template, res))
                atexit.register(res._atexit)
                self.save_on_del.value(False)

                for attr in [v for v in dir(self) if v.startswith('_opt_')]:
                    setattr(res, attr, getattr(self, attr))

                e = FailSafe.SafeLoadException()
                e.res = res
                raise e  # I know, but I have to avoid the subclasses to continue their initializations

            object.__setattr__(self, '_atexit', partial(FailSafe.Guardian._atexit_template, self))
            atexit.register(self._atexit)

            super(FailSafe.Guardian, self).__init__(*args, **kwargs)

        def __del__(self):
            if self.save_on_del.value():
                try:
                    self.save(self._filename)
                except Exception:
                    self_id = int(self._filename.split('_')[-1])
                    print(f'An exception happened while backing up the object {type(self).__name__} (id={self_id})')
                    raise

                atexit.unregister(self._atexit)
                atexit.register(partial(FailSafe.Guardian._atexit_completion, self))
                self.save_on_del.value(False)

            getattr(super(FailSafe.Guardian, self), '__del__', lambda: None)()

    def __init__(cls, name, bases, namespace, loader=None, saver=None, remover=None):
        super(FailSafe, cls).__init__(name, bases, namespace)
        if saver: setattr(cls, 'save', saver)
        if loader: setattr(cls, 'load', staticmethod(loader))

        if remover:
            setattr(cls, 'remove', staticmethod(remover))
        elif not hasattr(cls, 'remove'):
            setattr(cls, 'remove', on_remove)

    def __call__(self, *args, **kwargs):
        try:
            return super(FailSafe, self).__call__(*args, **kwargs)
        except FailSafe.SafeLoadException as e:  # Silent load case
            return e.res

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

    # TODO if i dont put this every class has to call super()init
    # def mro(self) -> List[type]:
    #     super_mro = super(Guarded, self).mro()
    #     guardian_mro = Guarded.Guardian.mro()[:-1]
    #
    #     if Guarded.Guardian in super_mro:
    #         super_mro.remove(Guarded.Guardian)
    #
    #     for cls in guardian_mro:
    #         if cls in super_mro:
    #             guardian_mro.remove(cls)
    #
    #     print(f'mro for {self.__name__}: {guardian_mro + super_mro}')
    #     return guardian_mro + super_mro


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

    #a.__del__()
    sys.exit(0)
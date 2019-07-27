import inspect
import atexit
from functools import partial
from typing import List


class Opt(object):
    load = False
    save = True


class Guarded(type):
    _use_mro_trick = False

    class SafeLoadException(Exception):
        pass

    class Guardian(object):
        @staticmethod
        def _atexit_template(self) -> None:
            del self

        def __init__(self, *args, _load=None, _save=None, **kwargs):
            type(self)._unique_id += 1  # For the same code the id should be the same
            object.__setattr__(self, 'filename', f'{type(self).__name__}_{type(self)._unique_id}')

            _load = _load if _load is not None else Opt.load
            _save = _save if _save is not None else Opt.save

            if _load:
                assert not inspect.ismethod(self.load) or self.load.__self__ is type(self), 'the "load" method has ' \
                                                                                            'to be of type ' \
                                                                                            '"staticmethod" ' \
                                                                                            'or "classmethod"'
                res = self.load(self.filename)
                object.__setattr__(res, 'filename', f'{type(self).__name__}_{type(self)._unique_id}')
                object.__setattr__(res, '_atexit', partial(Guarded.Guardian._atexit_template, res))
                atexit.register(res._atexit)

                object.__setattr__(self, '_save', False)
                object.__setattr__(res, '_save', _save)

                e = Guarded.SafeLoadException()
                e.res = res
                raise e  # I know, but I have to avoid the subclasses to continue their initializations

            object.__setattr__(self, '_save', _save)
            object.__setattr__(self, '_atexit', partial(Guarded.Guardian._atexit_template, self))
            atexit.register(self._atexit)

            super(Guarded.Guardian, self).__init__(*args, **kwargs)  # Multiple inheritance case

        def __del__(self):
            if self._save:
                self.save(self.filename)
                atexit.unregister(self._atexit)
            getattr(super(Guarded.Guardian, self), '__del__', lambda: None)()

    def __init__(cls, name, bases, namespace, loader=None, saver=None):
        super(Guarded, cls).__init__(name, bases, namespace)
        if saver:
            setattr(cls, 'save', saver)
        if loader:
            setattr(cls, 'load', loader)

    def __call__(self, *args, **kwargs):
        try:
            return super(Guarded, self).__call__(*args, **kwargs)
        except Guarded.SafeLoadException as e:
            return e.res

    @classmethod
    def __prepare__(mcs, name, bases, **kwargs):
        namespace = super(Guarded, mcs).__prepare__(name, bases, **kwargs)
        namespace.update({'_unique_id': 0})
        return namespace

    def __new__(metacls, name, bases, namespace, **kwargs):
        # assert not any([isinstance(b, Guarded) for b in bases]), f'A base class of {name} is already Guarded.'
        return super(Guarded, metacls).__new__(metacls, name, bases, namespace)

    def mro(self) -> List[type]:
        Guarded._use_mro_trick = not Guarded._use_mro_trick  # TODO commentate
        if Guarded._use_mro_trick:
            return [Guarded.Guardian, ] + super(Guarded, self).mro()  # To ensure that I execute my code the first
        else:
            return super(Guarded, self).mro()

################
# Example code #
################


if __name__ == '__main__':
    Opt.load = True

    class Prueba(metaclass=Guarded):
        def __init__(self, a, b, c):
            print('Prueba.__init__')
            self.a = a
            self.b = b
            self.c = c

        def __del__(self):
            print('Prueba.__del__')

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
        cls = DummyClass
        self = cls.__new__(cls)
        self.a = 1
        self.b = 2
        self.c = 4
        return self

    class DummyClass(metaclass=Guarded, loader=loadme):
        def __init__(self, a, b, c):
            print('Prueba.__init__')
            self.a = a
            self.b = b
            self.c = c

        def __del__(self):
            print('Prueba.__del__')
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

    a = AnotherDummyClass(1, 2, 3)
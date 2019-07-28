import unittest
from mlsuite.failsafe import FailSafe, GlobalOptions


class DummyClass(metaclass=FailSafe):
    def __init__(self, a, b, c):
        super().__init__()
        # print('Prueba.__init__')
        self.a = a
        self.b = b
        self.c = c

    def __del__(self):
        # print('Prueba.__del__')
        pass

    def save(self, filename):
        # print(f'saving {type(self).__name__} object to {filename}...')
        pass

    @classmethod
    def load(cls, filename):
        # print(f'loading {cls.__name__} object from {filename}...')
        self = cls.__new__(cls)
        self.a = 1
        self.b = 2
        self.c = 3
        return self

    def __str__(self):
        return f'{self.a} {self.b} {self.c}'


class AnotherDummyClass(DummyClass):  # It inherits the metaclass flavour
    def __init__(self, *args, **kwargs):
        super(AnotherDummyClass, self).__init__(*args, **kwargs)

    @classmethod
    def load(cls, filename):  # Overriding is possible
        instance = super(AnotherDummyClass, cls).load(filename)
        instance.a = filename
        return instance


class TestBodyguard(unittest.TestCase):

    def setUp(self) -> None:
        GlobalOptions.load_on_init.value(False)

    def test_init_global(self):
        obj = DummyClass(2, 3, 4)
        self.assertEqual('2 3 4', str(obj))

    @GlobalOptions.load_on_init(True)
    def test_load_global(self):
        obj = DummyClass(2, 3, 4)
        self.assertEqual('1 2 3', str(obj))

    def test_load_local(self):
        with GlobalOptions.load_on_init(True):
            obj1 = DummyClass(2, 3, 4)
            self.assertEqual('1 2 3', str(obj1))

        obj2 = DummyClass(2, 3, 4)
        self.assertEqual('2 3 4', str(obj2))

    @GlobalOptions.load_on_init(True)
    def test_init_local(self):
        with GlobalOptions.load_on_init(False):
            obj1 = DummyClass(2, 3, 4)
            self.assertEqual('2 3 4', str(obj1))

        obj2 = DummyClass(2, 3, 4)
        self.assertEqual('1 2 3', str(obj2))

    @GlobalOptions.load_on_init(True)
    def test_ids_load(self):
        obj1 = AnotherDummyClass(1, 2, 3)
        obj2 = DummyClass(2, 3, 4)
        obj3 = AnotherDummyClass(1, 2, 3)

        self.assertEqual('AnotherDummyClass_1', obj1.a)
        self.assertEqual(1, obj2.a)
        self.assertEqual('AnotherDummyClass_2', obj3.a)

    # TODO keep adding tests, e.g., loader/saver/_load/_save


if __name__ == '__main__':
    unittest.main()
import unittest
from base.bodyguard import Guarded, Opt  # TODO temporary


class DummyClass(metaclass=Guarded):
    def __init__(self, a, b, c):
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
        Opt.load = False

    def test_init_global(self):
        obj = DummyClass(2, 3, 4)
        self.assertEqual(str(obj), '2 3 4')

    def test_load_global(self):
        Opt.load = True  # TODO temporary

        obj = DummyClass(2, 3, 4)
        self.assertEqual(str(obj), '1 2 3')

    def test_load_local(self):
        obj1 = DummyClass(2, 3, 4, _load=True)
        self.assertEqual(str(obj1), '1 2 3')

        obj2 = DummyClass(2, 3, 4)
        self.assertEqual(str(obj2), '2 3 4')

    def test_init_local(self):
        Opt.load = True

        obj1 = DummyClass(2, 3, 4, _load=False)
        self.assertEqual(str(obj1), '2 3 4')

        obj2 = DummyClass(2, 3, 4)
        self.assertEqual(str(obj2), '1 2 3')

    def test_ids_load(self):
        Opt.load = True

        obj1 = AnotherDummyClass(1, 2, 3)
        obj2 = DummyClass(2, 3, 4)
        obj3 = AnotherDummyClass(1, 2, 3)

        self.assertEqual(obj1.a, 'AnotherDummyClass_1')
        self.assertEqual(obj2.a, 1)
        self.assertEqual(obj3.a, 'AnotherDummyClass_2')

    # TODO keep adding tests, e.g., loader/saver/_load/_save


if __name__ == '__main__':
    unittest.main()
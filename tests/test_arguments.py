import unittest
from io import StringIO
from base.arguments import Arguments


# TODO separate arguments from shared tree tests
class TestArguments(unittest.TestCase):

    def setUp(self) -> None:
        Arguments.reset()  # Reset the global variables always

        self.settings_str = '''
        arg1: true
        arg2: 'string'
        arg3: [1, 2, 3, 4]
        '''
        self.settings_dict = {'arg1': True, 'arg2': 'string', 'arg3': [1, 2, 3, 4]}

        self.settings_filename = 'example_settings.yaml'
        self.settings_filename_dict = {
            'seed': 7,
            'device': 'cuda',
            'output': {'interactive': False},
            'dataset': {
                'who': [],
                'params': [[{'probs': [0.25, 0.25, 0.25, 0.25]}]]
            },
            'something': {
                'that': ['looks', {'more': 'complicated'}],
                'but': ['it', 'may', 'not', 'be'],
                'the': {'whole': 'truth'}
            }
        }

    def test_load_stringio(self):
        args = Arguments()
        args.update(StringIO(self.settings_str), scope='local')
        dict(args)
        self.assertDictEqual(dict(args), self.settings_dict, 'Casting to dict failed.')

    def test_load_file(self):
        args = Arguments()
        with open(self.settings_filename, 'r') as file:
            args.update(file, scope='local')
        self.assertDictEqual(dict(args), self.settings_filename_dict, 'File update failed.')

    def test_load_filename(self):
        args = Arguments()
        args.update(filename=self.settings_filename, scope='local')
        self.assertDictEqual(dict(args), self.settings_filename_dict, 'Filename update failed.')

    def test_load_local_global(self):
        args1, args2 = Arguments(), Arguments()

        args1.update(self.settings_str, scope='local')
        args2.update(self.settings_str, scope='local')
        self.assertEqual(args1, args2, 'Local update failed.')

        args3 = Arguments()
        self.assertEqual(dict(args3), {})

        args3.update(self.settings_filename_dict, scope='global')
        args4 = Arguments()
        self.assertEqual(args3, args4)

        args5 = Arguments(path='something')
        args6 = Arguments(path='something')
        args7 = Arguments(path='something')

        args5.update({'that': ['array']})  # Global change
        self.assertEqual(args5.that, args6.that, 'Failed global editing.')

        # args5.that = 'element'  # This is not allowed
        args5.update({'that': ['element']}, scope='local')  # Change local attributes like this
        self.assertNotEqual(args5.that, args6.that)  # But you can read them like this

        args6.update({'that': ['element']}, scope='local') # Local changes
        self.assertNotEqual(args6.that, args7.that)
        self.assertEqual(args6.that, args5.that)

        Arguments.reset()
        args8 = Arguments()
        self.assertDictEqual(dict(args8), {})

    def test_update(self):
        my_dict = self.settings_filename_dict

        args = Arguments()
        args.update(my_dict)
        self.assertDictEqual(my_dict, dict(args), 'Update method failed.')

        update1 = {'seed': 10, 'device': 'cpu'}
        my_dict.update(update1)
        args.update(update1)
        self.assertDictEqual(my_dict, dict(args), 'Update 1 failed.')

        update2 = {'seed': 'string'}
        self.assertRaises(AssertionError, args.update, update2)

        update3 = {'seed': {'this': 'is', 'a': 'dict'}}
        self.assertRaises(AssertionError, args.update, update3)

        update4 = {'dataset': {'who': [1, 2, 3], 'a': 'dict'}}
        my_dict['dataset'].update({'who': [1, 2, 3], 'a': 'dict'})
        args.update(update4)
        self.assertDictEqual(my_dict, dict(args))

        update5 = {'something': {'that': ['looks', 'simple']}}
        my_dict['something'].update({'that': ['looks', 'simple']})
        args.update(update5)
        self.assertDictEqual(my_dict, dict(args))

    def test_global_nonargument(self):
        args1 = Arguments().update(self.settings_filename_dict)
        args2 = Arguments()
        self.assertEqual(args1, args2)

        # checks that args1.seed = 10 outputs an error
        self.assertRaises(ValueError, args1.__setattr__, 'seed', 10)

        # Global change of an integer
        args1.update({'seed': 10})
        self.assertEqual(args1, args2)

        # Local change of an integer
        args1.update({'seed': 5}, scope='local')
        self.assertNotEqual(args1, args2)

        # Check that I can do nested accesses
        self.assertEqual(args1.dataset.who, [])


if __name__ == '__main__':
    unittest.main()
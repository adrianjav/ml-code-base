import unittest
from io import StringIO
from base.arguments import Arguments


class TestArguments(unittest.TestCase):

    def setUp(self) -> None:
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
        args.update(StringIO(self.settings_str))
        self.assertDictEqual(dict(args), self.settings_dict, 'Casting to dict failed.')

    def test_load_file(self):
        args = Arguments()
        with open(self.settings_filename, 'r') as file:
            args.update(file)
        self.assertDictEqual(dict(args), self.settings_filename_dict, 'File update failed.')

    def test_load_filename(self):
        args = Arguments()
        args.update(filename=self.settings_filename)
        self.assertDictEqual(dict(args), self.settings_filename_dict, 'Filename update failed.')

    def test_load_local_global(self):
        args1, args2 = Arguments(), Arguments()

        args1.update(self.settings_str)
        args2.update(self.settings_str)
        self.assertEqual(args1, args2, 'Local update failed.')

        args3 = Arguments()
        self.assertEqual(dict(args3), {})

    def test_update(self):
        my_dict = self.settings_filename_dict

        args = Arguments()
        args.update(my_dict)
        self.assertDictEqual(my_dict, dict(args), 'Update method failed.')

        update1 = {'seed': 10, 'device': 'cpu'}
        my_dict.update(update1)
        args.update(update1)
        self.assertDictEqual(my_dict, dict(args), 'Update 1 failed.')

        # update2 = {'seed': 'string'}
        # self.assertRaises(AssertionError, args.update, update2)

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


if __name__ == '__main__':
    unittest.main()
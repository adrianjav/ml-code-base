import unittest
import sys
from pathlib import Path

import mlsuite
from mlsuite import directories as dirs


class TestArguments(unittest.TestCase):

    def setUp(self) -> None:
        mlsuite.create_dirs.value(False)
        dirs.reset()

        self.dirs_dict = '''
        folder1: []
        folder2: {
            folder2_1: [folder2_1_1, folder2_1_2],
            folder2_2: []
        }
        '''

    def test_root_creation(self):
        self.assertEqual('.', str(dirs))
        self.assertEqual('.', dirs.root)

    def test_load_settings(self):
        dirs.update(self.dirs_dict)

        self.assertEqual('./folder1', dirs.folder1.root)
        self.assertFalse(Path(str(dirs.folder1)).exists())

    def test_change_settings(self):
        dirs.update(self.dirs_dict)

        dirs.update_root('other_place')
        self.assertEqual('other_place/folder2/folder2_1', str(dirs.folder2.folder2_1))

    def test_creating_dir(self):
        with mlsuite.create_dirs(True):
            dirs.update(self.dirs_dict)
            with mlsuite.create_dirs(False):
                path = dirs.folder1.root

            self.assertFalse(Path(path).exists())

            self.assertTrue(Path(dirs.folder1.root).exists())

            Path('folder1').rmdir()

    def test_dots(self):
        dirs.update({'.hidden': []})
        self.assertEqual('./.hidden', str(dirs._H_hidden))

if __name__ == '__main__':
    unittest.main()
    sys.exit(0)
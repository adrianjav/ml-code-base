import sys

from collections.abc import Iterable
from pathlib import Path

from mlsuite.data_structures import NestedNamespace
from mlsuite.utils import Options

# From this class we are also going to have a single global variable directories which
# we will take root directory like
# from * import directories as dirs
# dirs.root
# and subfolders like dirs.subfolder.root
# and leaf subfolders like dirs.subfolder1.subfolder2
#
# This class is going to be instantiated from the very beginning but it shouldn't create
# any directory until someone is accessing to it
#
# We update it as dirs.update({'folder1': ['subfolder1', 'subfolder2']}) (add { root': '.'} in the function)
# then, lazily create the folder as we access to them TODO configure it?


# metaclass tiene que coger los atributos,

class GlobalOptions(metaclass=Options):
    _opt_create_dirs = True


class MkdirOnDemand(object):
    def __init__(self, val, owner):
        self.val = val
        self.owner = owner

    def side_effect(self):
        if self.owner.create_dirs.value():
            Path(self.val).mkdir(parents=True, exist_ok=True)
        return self.val


class Directories(NestedNamespace, GlobalOptions):  # I can inherit from it since I don't plan to use dict/save
    def __init__(self, root='.'):
        super(Directories, self).__init__()
        self._root = root
        self.update({})

    def _process_dirs(self, res, root: str) -> dict:
        assert isinstance(res, dict) or isinstance(res, Iterable), 'Wrong format.'

        res = res if isinstance(res, dict) else {k: None for k in res}
        for k, v in res.items():
            if isinstance(v, dict) or isinstance(v, Iterable):
                res[k] = self._process_dirs(v, root=f'{root}/{k}')
            else:
                res[k] = MkdirOnDemand(f'{root}/{k}', self)

        res.update({'root': MkdirOnDemand(root, self)})
        return res

    def _get_dict(self, source, filename) -> dict:
        res = super(Directories, self)._get_dict(source, filename)
        res = self._process_dirs(res, root=self._root)
        return res

    @GlobalOptions.create_dirs(False)
    def update(self, *args, **kwargs):
        return super(Directories, self).update(*args, **kwargs)

    def __getattribute__(self, item):
        res = super(Directories, self).__getattribute__(item)
        if isinstance(res, MkdirOnDemand):
            val = res.side_effect()
            if val == self._root:
                path = ['root']
            else:
                path = val[len(self._root)+1:].split('/')
                if item == 'root':
                    path += ['root']

            dict_path = val
            for i in range(1, len(path)+1):
                dict_path = {path[-i]: dict_path}

            super(Directories, self).update_from_dict(dict_path)
            return val
        return res



################
# Example code #
################


if __name__ == '__main__':
    import os.path;
    d = Directories(root='../outputs')
    d.update({'folder1': None, 'folder2': ['other']})
    # print(d)

    print(f'create_dirs={d.create_dirs.value()}')
    with d.create_dirs(False):
        print(f'create_dirs={d.create_dirs.value()}')
        print(d.root)
        print('d.root', os.path.exists(d.root))

    print(f'create_dirs={d.create_dirs.value()}')
    print(d.folder1)
    print('folder1', os.path.exists(d.folder1))

    @GlobalOptions.create_dirs(False)
    def show_last_folder():
        print(f'create_dirs={d.create_dirs.value()}')
        print(d.folder2.other)

    show_last_folder()

    GlobalOptions.create_dirs.value(False)
    print(f'create_dirs={d.create_dirs.value()}')
    print('folder2', os.path.exists(d.folder2.root))
    sys.exit(0)
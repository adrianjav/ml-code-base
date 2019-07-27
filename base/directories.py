from collections.abc import Iterable
from pathlib import Path

from base.data_structures import SharedTree
from base.utils import SideEffect

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

class Opt(object):
    create_dirs = False


class MkdirOnDemand(metaclass=SideEffect):
    def __init__(self, val):
        self.val = val

    def side_effect(self):
        if Opt.create_dirs:
            Path(self.val).mkdir(parents=True, exist_ok=True)
        return self.val


class Directories(SharedTree):
    class SafeDirException(Exception):
        pass

    def __init__(self, root='.', *args, **kwargs):
        super(Directories, self).__init__(*args, **kwargs)
        object.__setattr__(self, '_root', root)

    def _process_dirs(self, res, root: str) -> dict:
        assert isinstance(res, dict) or isinstance(res, Iterable), 'Wrong format.'

        res = res if isinstance(res, dict) else {k: None for k in res}
        for k, v in res.items():
            if isinstance(v, dict) or isinstance(v, Iterable):
                res[k] = self._process_dirs(v, root=f'{root}/{k}')
            else:
                res[k] = MkdirOnDemand(f'{root}/{k}')

        res.update({'root': MkdirOnDemand(root)})
        return res

    def _get_dict(self, source, filename) -> dict:
        res = super(Directories, self)._get_dict(source, filename)
        res = self._process_dirs(res, root=self._root)
        return res


################
# Example code #
################

if __name__ == '__main__':
    d = Directories(root='../outputs')
    d.update({'folder1': None, 'folder2': ['other']})
    print(d)
    print(d.root)
    print(d.folder1)
    print(d.folder2.other)
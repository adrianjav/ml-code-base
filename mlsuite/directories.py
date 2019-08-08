import sys
from typing import Optional, Any

from collections.abc import Iterable
from pathlib import Path

from mlsuite.data_structures import NestedNamespace
from mlsuite.options import Options


def args_to_str(sentence):
    pos = sentence.find('$args')
    if pos == -1:
        return sentence

    from . import arguments as args
    from .data_structures import NestedNamespace

    new_sentence = args
    for s in sentence[pos:].split('.')[1:]:
        new_sentence = getattr(new_sentence, s)
    assert not isinstance(new_sentence, NestedNamespace)
    return sentence[:pos] + new_sentence


class GlobalOptions(metaclass=Options):
    _opt_create_dirs = True


class LazyDirectory(object):
    def __init__(self, val):
        assert isinstance(val, str)
        self.val = val

    def mkdir(self, root, owner):
        if owner.create_dirs.value():
            path = f'{root}/{self.val}' if root is not None else self.val
            Path(path).mkdir(parents=True, exist_ok=True)
            return self.val
        else:
            return self

    def __repr__(self):
        return f'l\'{self.val}\''

    def __str__(self):
        return self.val


class Directories(GlobalOptions):  # I can inherit from it since I don't plan to use dict/save
    def __init__(self, namespace=None, root='.'):
        super(Directories, self).__init__()
        self.namespace = namespace or NestedNamespace()
        self.namespace.update_from_dict({'root': LazyDirectory(root)})  # Initialization
        self._root = root

    def reset(self, namespace=None, root='.'):
        self._root = root
        self.namespace = namespace or NestedNamespace()

        self.update({})

    @GlobalOptions.create_dirs(False)
    def update_root(self, path):
        def change_root_recursively(self, prev, new):
            old_root = self.root
            is_lazy = isinstance(old_root, LazyDirectory)

            with GlobalOptions.create_dirs(False):
                if is_lazy: old_root = str(old_root)

            new_root = new + old_root[len(prev):]
            self._root = new_root
            self.update({})
            # if is_lazy:
            #     self.update_from_dict({'root': LazyDirectory(new_root)})
            # else:
            #     self.update_from_dict({'root': new_root})

            for v in [getattr(self, k) for k in dict(self.namespace).keys()]:
                if isinstance(v, Directories):
                    change_root_recursively(v, prev, new)

        change_root_recursively(self, self.root, path)

        return self._root

    def _process_dirs(self, res, root: str) -> dict:
        assert isinstance(res, dict) or isinstance(res, Iterable), 'Wrong format.'

        res = res if isinstance(res, dict) else {k: [] for k in res}
        new_res = {}
        for k, v in res.items():
            k = args_to_str(k)
            if isinstance(v, str):
                v = args_to_str(v)

            if not isinstance(v, str) and (isinstance(v, dict) or isinstance(v, Iterable)):
                new_res[k] = self._process_dirs(v, root=f'{root}/{k}')
            else:
                new_res[k] = LazyDirectory(k)

        new_res.update({'root': LazyDirectory(root)})
        return new_res

    @GlobalOptions.create_dirs(False)
    def update(self, source: Optional[Any] = None, filename: Optional[str] = None):
        assert (source is not None or filename is not None) and not (
                    source is None and filename is None), 'Set one of "source" and "filename"'

        raw_dict = self.namespace.get_dict(source, filename)
        root = args_to_str(raw_dict['root']) if 'root' in raw_dict.keys() else self._root
        raw_dict = self._process_dirs(raw_dict, root)
        self.namespace.update(raw_dict)
        self._root = str(self.root)

    def __getattr__(self, item):
        if item == 'namespace':
            raise AttributeError(item)

        res = getattr(self.namespace, item)

        if isinstance(res, NestedNamespace):
            res = Directories(res, str(res.root))
        elif isinstance(res, LazyDirectory):
            val = res.mkdir(self.root, self) if item != 'root' else res.mkdir(None, self)
            self.namespace.update_from_dict({item: val})
            res = str(val)

        return res

    def __iter__(self):
        return self.namespace.__iter__()

    def __str__(self):
        return str(self.root)

    def __repr__(self):
        return f'd\'{str(self.root)}\''


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
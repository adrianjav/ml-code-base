from typing import Any, Optional
from types import SimpleNamespace

import yaml


class NestedNamespace(SimpleNamespace):
    def __init__(self, **kwargs):
        super().__init__()
        self.update(**kwargs)

    def update(self, **kwargs) -> None:
        """
        Updates the arguments of the object. Nested dicts get casted into NestedNamespaces objects.
        :param kwargs: dictionary with the arguments
        :return: itself
        """

        for k, v in kwargs.items():
            if k in self.__dict__.keys():
                if isinstance(v, dict):
                    assert isinstance(getattr(self, k), NestedNamespace), f'key "{k}"s is of type {type(getattr(self, k))}'
                    getattr(self, k).update(**v)
                else:
                    assert type(v) is type(getattr(self, k)), f'wrong type when trying to update "{k}"'
                    setattr(self, k, v)
            else:
                if isinstance(v, dict):
                    setattr(self, k, NestedNamespace(**v))
                else:
                    setattr(self, k, v)

    def __iter__(self):
        for k, v in self.__dict__.items():
            yield [k, dict(v)] if isinstance(v, NestedNamespace) else [k, v]


class Arguments(object):
    __shared_namespace = NestedNamespace()

    def __init__(self, path: Optional[str] = None, parent=None):
        self.namespace = Arguments.__shared_namespace if parent is None else parent.namespace
        if path is not None:
            for key in path.split('.'):
                nested_ns = getattr(self, key, None)
                if not isinstance(nested_ns, NestedNamespace):
                    tree_desc = 'root.' + path[:path.find(key) + len(key)]
                    raise ValueError(f'{tree_desc} do not exist in the arguments tree')

                self.namespace = nested_ns

    def __getattr__(self, item):
        return self.namespace.__getattribute__(item)

    def __iter__(self):
        return self.namespace.__iter__()

    def __eq__(self, other):
        return self.namespace == other.namespace

    def __str__(self):
        return self.namespace.__str__()

    @staticmethod
    def reset():
        Arguments.__shared_namespace = NestedNamespace()

    def load(self, source: Any, scope: str = 'global') -> None:
        """
        Load a file-like object (or dict) and reads all the arguments in there with an unsafe yaml loader.

        :param source: dict/file-like object from which to read the settings
        :param scope: specify how to update the arguments: `global` | `local`
        """

        if isinstance(source, dict):
            args_dict = source
        else:
            args_dict = yaml.load(source, Loader=yaml.UnsafeLoader) or {}

        if scope == 'global':
            self.namespace.update(**args_dict)
        elif scope == 'local':
            self.namespace = NestedNamespace(**args_dict)
        else:
            raise ValueError('mode should be `global` or `local`.')


# Example code
if __name__ == '__main__':
    args = Arguments()
    with open('../tests/example_settings.yaml', 'r') as file:
        args.load(file, scope='local')
    print(args.dataset)

    args = Arguments('dataset', args)
    print(args)

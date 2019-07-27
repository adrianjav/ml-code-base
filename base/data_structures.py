from __future__ import annotations
from typing import Any, Optional
from types import SimpleNamespace

import yaml


# TODO THIS IS A THING metaclass=my_function()->metaclass):
class NestedNamespace(SimpleNamespace):
    def __init__(self, **kwargs):
        super(NestedNamespace, self).__init__()
        self.update(**kwargs)

    def update(self, **kwargs) -> None:
        """
        Updates the arguments of the object. Nested dicts get casted into NestedNamespaces objects.
        :param kwargs: dictionary with the arguments
        """
        parser = lambda s: s.replace(' ', '_')  # TODO it might need to be modified to accomplish attributes syntax

        for k, v in kwargs.items():
            k = parser(k)

            if k in self.__dict__.keys():
                if isinstance(v, dict):
                    assert isinstance(getattr(self, k), NestedNamespace), f'wrong type: key="{k}", ' \
                        f'type={NestedNamespace}, expected={type(getattr(self, k))}'
                    getattr(self, k).update(**v)
                else:
                    assert type(v) is type(getattr(self, k)), f'wrong type: key="{k}", type={type(v)}, ' \
                        f'expected={type(getattr(self, k))}'
                    setattr(self, k, v)
            else:
                if isinstance(v, dict):
                    setattr(self, k, NestedNamespace(**v))
                else:
                    setattr(self, k, v)

    def __iter__(self):
        for k, v in self.__dict__.items():
            yield [k, dict(v)] if isinstance(v, NestedNamespace) else [k, v]


class SharedTree(object):
    def __init_subclass__(cls, **kwargs):  # Creates a different shared namespace per subclass
        cls._shared_namespace = NestedNamespace()
        super(SharedTree, cls).__init_subclass__(**kwargs)

    def __init__(self, path: Optional[str] = None, parent=None):
        object.__setattr__(self, 'namespace', parent or self._shared_namespace)

        if path is not None:
            for key in path.split('.'):
                nested_ns = getattr(self, key, None)
                if not isinstance(nested_ns, NestedNamespace):
                    tree_desc = 'root.' + path[:path.find(key) + len(key)]
                    raise ValueError(f'{tree_desc} does not exist in the tree')

                object.__setattr__(self, 'namespace', nested_ns)

    def __getattr__(self, item):
        return getattr(self.namespace, item)

    def __setattr__(self, key, value):
        raise ValueError('Use the "update" method to change attributes.')

    def __iter__(self):
        return self.namespace.__iter__()

    def __eq__(self, other):
        return self.namespace == other.namespace

    def __str__(self):
        return self.namespace.__str__()

    @classmethod
    def reset(cls):
        cls._shared_namespace = NestedNamespace()

    def update(self, source: Optional[Any] = None, filename: Optional[str] = None, scope: str = 'global') -> SharedTree:
        """
        Load a file-like/string/dict object and reads all the arguments in there with an unsafe yaml loader.

        :param source: dict/file-like object from which to read the settings
        :param filename Filename of the settings file. `filename` and `source` are incompatibles.
        :param scope: specify how to update the arguments: `global` | `local`
        :return itself
        """
        assert (source or filename) and not (source and filename), 'Set one of "source" and "filename"'

        if source:
            if isinstance(source, dict):
                args_dict = source
            else:
                args_dict = yaml.safe_load(source) or {}

        if filename:
            with open(filename, 'r') as file:
                args_dict = yaml.safe_load(file) or {}

        if scope == 'global':
            self.namespace.update(**args_dict)
        elif scope == 'local':
            object.__setattr__(self, 'namespace', NestedNamespace(**dict(self.namespace)))
            self.namespace.update(**args_dict)
        else:
            raise ValueError('mode should be "global" or "local".')

        return self
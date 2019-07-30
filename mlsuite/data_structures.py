from __future__ import annotations
from typing import Any, Optional
from types import SimpleNamespace

import yaml


# TODO THIS IS A THING metaclass=my_function()->metaclass):
class NestedNamespace(SimpleNamespace):
    def __init__(self):
        super(NestedNamespace, self).__init__()

    def get_dict(self, source, filename) -> dict:
        if isinstance(source, dict):
            res = source
        elif source:
            res = yaml.safe_load(source) or {}
        else:
            with open(filename, 'r') as file:
                res = yaml.safe_load(file) or {}

        assert isinstance(res, dict)
        return res

    def update_from_dict(self, my_dict):
        parser = lambda s: s.replace(' ', '_').replace('.', '_H_')  # TODO it might need to be modified

        for k, v in my_dict.items():
            k = parser(k)

            if k in self.__dict__.keys():
                if isinstance(v, dict):
                    assert isinstance(getattr(self, k), NestedNamespace), f'wrong type: key="{k}", ' \
                        f'type={NestedNamespace}, expected={type(getattr(self, k))}'
                    getattr(self, k).update(v)
                else:
                    # assert type(v) is type(getattr(self, k)), f'wrong type: key="{k}", type={type(v)}, ' \
                    #     f'expected={type(getattr(self, k))}'
                    setattr(self, k, v)
            else:
                if isinstance(v, dict):
                    new_obj = type(self)().update_from_dict(v)
                    setattr(self, k, new_obj)
                else:
                    setattr(self, k, v)

        return self


    def update(self, source: Optional[Any] = None, filename: Optional[str] = None):
        """
        Load a file-like/string/dict object and reads all the arguments in there with an unsafe yaml loader.

        :param source: dict/file-like object from which to read the settings
        :param filename Filename of the settings file. `filename` and `source` are incompatibles.
        :param scope: specify how to update the arguments: `global` | `local`
        :return itself
        """
        assert (source is not None or filename is not None) and not (source is None and filename is None), 'Set one of "source" and "filename"'

        args_dict = self.get_dict(source, filename)
        self.update_from_dict(args_dict)

        return self

    def __iter__(self):
        for k, v in self.__dict__.items():
            yield [k, dict(v)] if isinstance(v, NestedNamespace) else [k, v]


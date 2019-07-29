from __future__ import annotations
from typing import Any, Optional

import yaml

import mlsuite
from mlsuite.data_structures import NestedNamespace
from mlsuite.failsafe import FailSafe


class Arguments(metaclass=FailSafe):
    def __init__(self, namespace=None):
        super(Arguments, self).__init__()
        self.namespace = namespace or NestedNamespace()

    @classmethod
    def load(cls, filename):
        with open(filename, 'r') as file:
            raw_args = yaml.safe_load(file)

        self = Arguments()
        if raw_args:
            self.update_from_dict(raw_args)

        return self

    def save(self, filename):
        with open(filename, 'w') as file:
            yaml.safe_dump(dict(self), file)

    def update_from_dict(self, my_dict):
        self.namespace.update_from_dict(my_dict)

    def update(self, source: Optional[Any] = None, filename: Optional[str] = None) -> Arguments:
        self.namespace.update(source, filename)
        return self

    def __getattr__(self, item):
        res = getattr(self.namespace, item)
        if isinstance(res, NestedNamespace):
            return Arguments(res)
        return res

    def __iter__(self):
        return self.namespace.__iter__()

    def __eq__(self, other):
        return self.namespace == other.namespace



# Example code
if __name__ == '__main__':
    args = Arguments()
    print(args)

    with open('../tests/example_settings.yaml', 'r') as file:
        args.update(file)

    args = args.dataset
    print(args)

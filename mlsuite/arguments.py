import yaml

from mlsuite.data_structures import NestedNamespace
from mlsuite.failsafe import FailSafe

# TODO GUARDAR FICHERO CON EL INDICE DE LOS ELEMENTOS GUARDADOS (I can check the ls of the directory)


class Arguments(NestedNamespace, metaclass=FailSafe):
    @classmethod
    def load(cls, filename):
        with open(filename, 'r') as file:
            raw_args = yaml.safe_load(file)

        self = cls.__new__(cls)
        self.update_from_dict(raw_args)

        return self

    def save(self, filename):
        with open(filename, 'w') as file:
            yaml.safe_dump(dict(self), file)  TODO there is a problem when using dict, should be easy to fix tho

    def __iter__(self):
        return super(Arguments, self).__iter__()


# Example code
if __name__ == '__main__':
    args = Arguments()
    print(args)

    with open('../tests/example_settings.yaml', 'r') as file:
        args.update(file)

    args = args.dataset
    print(args)

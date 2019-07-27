from base.data_structures import NestedNamespace

# TODO from base.bodyguard import Guarded


# TODO GUARDAR FICHERO CON EL INDICE DE LOS ELEMENTOS GUARDADOS (I can check the ls of the directory)
class Arguments(NestedNamespace):
    pass
    # @classmethod
    # def load(cls, filename):  # TODO WIP
    #     print(f'loading {cls.__name__} object from {filename}...')
    #     self = cls.__new__(cls)
    #     object.__setattr__(self, 'namespace', Arguments._shared_namespace)
    #     return self
    #
    # def save(self, filename):  # TODO WIP
    #     print(f1'saving {type(self).__name__} object to {filename}...', id(self))


# Example code
if __name__ == '__main__':
    args = Arguments()
    print(args)

    with open('../tests/example_settings.yaml', 'r') as file:
        args.update(file)

    args = args.dataset
    print(args)

from .data_structures import SharedTree

# TODO from base.bodyguard import Guarded


# TODO GUARDAR FICHERO CON EL INDICE DE LOS ELEMENTOS GUARDADOS
class Arguments(SharedTree):
    pass
    # @classmethod
    # def load(cls, filename):  # TODO WIP
    #     print(f'loading {cls.__name__} object from {filename}...')
    #     self = cls.__new__(cls)
    #     object.__setattr__(self, 'namespace', Arguments._shared_namespace)
    #     return self
    #
    # def save(self, filename):  # TODO WIP
    #     print(f'saving {type(self).__name__} object to {filename}...', id(self))


# Example code
if __name__ == '__main__':
    args = Arguments()
    print(id(args._shared_namespace))
    print(Arguments._shared_namespace)
    Arguments.reset()
    with open('../tests/example_settings.yaml', 'r') as file:
        args.update(file, scope='local')
    print(args.dataset)

    args = Arguments('dataset', args)
    print(args)

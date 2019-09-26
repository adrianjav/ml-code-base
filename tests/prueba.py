import sys
import mlsuite
from mlsuite import arguments as args, directories as dirs


mlsuite.load_on_init.value(False)
# print(mlsuite.load_on_init.value())
#
# with mlsuite.load_on_init(False):
#     print(mlsuite.load_on_init.value())
#
# print(mlsuite.load_on_init.value())

mlsuite.update_arguments({'a': 2})
print(dict(args))

dirs.__reset_id__()
print(dirs.update({'folder1': None, 'folder2': ['folder2.1', 'folder2.2']}))
print(dict(dirs))
# print(dirs.folder1)  # creates the folder


class ImportantStuff(metaclass=mlsuite.FailSafe):
    def save(cls, filename):
        print('saving my important stuff')

    @classmethod
    def load(cls, filename):
        print('loading my stuff')
        instance = cls.__new__(cls)
        return instance

stuff = ImportantStuff()

# args.save('algo')
print(stuff.save_on_del.value())

with mlsuite.load_on_init(True), mlsuite.save_on_del(False), mlsuite.inherit_on_creation(True):
    loaded_stuff = ImportantStuff()

print(stuff.save_on_del.value())
print(loaded_stuff.save_on_del.value())

sys.exit(0)
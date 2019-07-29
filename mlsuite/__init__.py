from typing import Optional, Any

from .directories import Directories, GlobalOptions as dirsOptions

directories = Directories()


# Directories options
class create_dirs(dirsOptions.create_dirs): pass


from .failsafe import FailSafe, GlobalOptions as fsOptions


# FailSafe options
class load_on_init(fsOptions.load_on_init): pass
class save_on_del(fsOptions.save_on_del): pass
class remove_on_completion(fsOptions.remove_on_completion): pass
class inherit_on_creation(fsOptions.inherit_on_creation): pass
class failsafe_folder(fsOptions.failsafe_folder): pass


from .arguments import Arguments

with fsOptions.inherit_on_creation(True):
    with fsOptions.load_on_init(True), fsOptions.save_on_del(True), fsOptions.remove_on_completion(True):
        arguments = Arguments()


def update_arguments(source: Optional[Any] = None, filename: Optional[str] = None):
    arguments.update(source, filename)


def update_directories(source: Optional[Any] = None, filename: Optional[str] = None):
    directories.update(source, filename)


__all__ = ['arguments', 'directories', 'FailSafe', 'update_arguments', 'update_directories', 'inherit_on_creation']


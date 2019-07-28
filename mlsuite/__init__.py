from typing import Optional, Any

from .arguments import Arguments
from .failsafe import FailSafe, GlobalOptions as fsOptions
from .directories import Directories, GlobalOptions as dirsOptions


arguments = Arguments()
directories = Directories()


def update_arguments(source: Optional[Any] = None, filename: Optional[str] = None):
    arguments.update(source, filename)


def update_directories(source: Optional[Any] = None, filename: Optional[str] = None):
    directories.update(source, filename)


# FailSafe options
class load_on_init(fsOptions.load_on_init): pass
class save_on_del(fsOptions.save_on_del): pass
class remove_on_completion(fsOptions.remove_on_completion): pass

# Directories options
class create_dirs(dirsOptions.create_dirs): pass


__all__ = ['arguments', 'directories', 'FailSafe', 'update_arguments', 'update_directories']


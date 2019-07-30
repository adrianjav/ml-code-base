from typing import Optional, Any

from .data_structures import NestedNamespace
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


def load_config(source: Optional[Any] = None, filename: Optional[str] = None):
    assert (source is None or filename is None) and (source is not None or filename is not None)

    config = NestedNamespace().update(source, filename)

    if hasattr(config, 'arguments'):
        pass

    if hasattr(config, 'directories'):
        c_dirs = config.directories
        if hasattr(c_dirs,'root'): directories.update_root(c_dirs.root)
        if hasattr(c_dirs, 'init'): directories.update(dict(c_dirs.init))
        if hasattr(c_dirs, 'create_dirs'): dirsOptions._opt_create_dirs = c_dirs.create_dirs

    if hasattr(config, 'failsafe'):
        c_fs = config.failsafe
        if hasattr(c_fs, 'inherit_on_creation'): fsOptions._opt_inherit_on_creation = c_fs.inherit_on_creation
        if hasattr(c_fs, 'load_on_init'): fsOptions._opt_load_on_init = c_fs.load_on_init
        if hasattr(c_fs, 'save_on_del'): fsOptions._opt_save_on_del= c_fs.save_on_del
        if hasattr(c_fs, 'remove_on_completion'): fsOptions._opt_remove_on_completion = c_fs.remove_on_completion
        if hasattr(c_fs, 'folder'):
            with dirsOptions.create_dirs(False):
                folder = directories
                for s in c_fs.folder.split('/'):
                    folder = getattr(directories, s)

            fsOptions._opt_failsafe_folder = folder


__all__ = ['arguments', 'directories', 'FailSafe', 'update_arguments', 'update_directories', 'inherit_on_creation']


import os
from datetime import datetime
from typing import Optional, Any

from .data_structures import NestedNamespace
from .directories import args_to_str, Directories, GlobalOptions as dirsOptions

directories = Directories()


# Directories options
class create_dirs(dirsOptions.create_dirs): pass


from .failsafe import FailSafe, failsafe_result, keyboard_stopable, execute_once, GlobalOptions as fsOptions


# FailSafe options
class load_on_init(fsOptions.load_on_init): pass
class save_on_del(fsOptions.save_on_del): pass
class remove_on_completion(fsOptions.remove_on_completion): pass
class inherit_on_creation(fsOptions.inherit_on_creation): pass
class failsafe_folder(fsOptions.failsafe_folder): pass


from .arguments import Arguments

# with fsOptions.inherit_on_creation(True):
#     with fsOptions.load_on_init(True), fsOptions.save_on_del(True), fsOptions.remove_on_completion(True):
arguments = Arguments()
# arguments.timestamp = datetime.today().strftime('%Y-%m-%d-%H:%M:%S') # TODO bash: date +"%Y-%m-%d-%H:%M:%S"


def update_arguments(source: Optional[Any] = None, filename: Optional[str] = None):
    arguments.update(source, filename)


def update_directories(source: Optional[Any] = None, filename: Optional[str] = None):
    directories.update(source, filename)


def load_config(source: Optional[Any] = None, filename: Optional[str] = None):
    assert (source is None or filename is None) and (source is not None or filename is not None)

    parse = lambda d: {k.replace(' ', '_'): parse(v) for k, v in d.items()} if isinstance(d, dict) else d
    config = NestedNamespace().get_dict(source, filename)
    config = parse(config)

    if 'arguments' in config.keys():
        arguments.update(config['arguments'])

    if 'directories' in config.keys():
        c_dirs = config['directories']
        if 'root' in c_dirs.keys(): directories.update_root(c_dirs['root'])
        if 'init' in c_dirs.keys(): directories.update(c_dirs['init'])
        if 'create_dirs' in c_dirs.keys(): dirsOptions._opt_create_dirs = c_dirs['create_dirs']

    if 'failsafe' in config.keys():
        c_fs = config['failsafe']
        if 'inherit_on_creation' in c_fs.keys(): fsOptions._opt_inherit_on_creation = c_fs['inherit_on_creation']
        if 'load_on_init' in c_fs.keys(): fsOptions._opt_load_on_init = c_fs['load_on_init']
        if 'save_on_del' in c_fs.keys(): fsOptions._opt_save_on_del= c_fs['save_on_del']
        if 'remove_on_completion' in c_fs.keys(): fsOptions._opt_remove_on_completion = c_fs['remove_on_completion']
        if 'folder' in c_fs.keys():
            with dirsOptions.create_dirs(False):
                folder = directories
                for s in c_fs['folder'].split('/'):
                    s = args_to_str(s)
                    if s != 'root':  # root is a string and the previoius folder already gets it
                        folder = getattr(folder, s)

            fsOptions._opt_failsafe_folder = folder


# Default configuration loaded from the config.yaml file in this directory
load_config(filename=f'{os.path.dirname(os.path.abspath(__file__))}/config.yaml')


__all__ = ['arguments', 'directories', 'FailSafe', 'update_arguments', 'update_directories', 'inherit_on_creation',
           'failsafe_result', 'keyboard_stopable', 'execute_once']


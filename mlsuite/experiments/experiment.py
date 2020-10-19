import os
import sys
import subprocess
from functools import wraps
from datetime import datetime
from contextlib import redirect_stdout, redirect_stderr

import yaml
import click

from mlsuite.experiments.arguments import ArgumentsHeader, Arguments
from mlsuite.experiments.yaml_handlers import read_yaml, YAMLConfig


class TeeFile:
    """Writes to multiple files at once"""
    def __init__(self, *files):
        self.files = files

    def write(self, data):
        for file in self.files:
            file.write(data)

    def flush(self):
        for file in self.files:
            file.flush()


def is_interactive_shell() -> bool:
    return sys.__stdin__.isatty()


def experiment_wrapper(*args, **kwargs):
    """Automatises the usual boilerplate from experiments.

    In particular:
        1. Gathers all arguments and pass it to the function.
        2. Creates the experiment directories and changes the working directory.
        3. Saves a copy of the arguments to a yaml file.
        4. Adds the git hash (if it exists) and timestamp to the settings.
        5. Redirects output and error to a file.
        6. If verbose=True and it is running in an interactive terminal it also outputs to the terminal.
    """
    def _experiment_decorator(**kwargs):
        arguments = ArgumentsHeader(options={
            'output_dir': 'results', #'.',
            'default_dirs': [],
            'output_file': 'stdout.txt',
            'error_file': 'stderr.txt',
            'verbose': True,
            'git_hash': 'no-git',
            'exist_ok': False,
            'config_file': 'config.yml',
        })
        arguments.options.update(**kwargs)

        # Add git version to the config file
        try:
            git_hash = subprocess.check_output(["git", "describe", "--always"],
                                               stderr=subprocess.DEVNULL).strip().decode('ascii')
            arguments.options.update(git_hash=git_hash)
        except subprocess.CalledProcessError:
            pass

        # Add timestamp to the config file
        arguments.options.update(timestamp=datetime.today().strftime('%Y-%m-%d-%H:%M:%S'))

        def __experiment_decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    arguments.update(*args, **kwargs)
                    arguments.update(pwd=os.getcwd())

                    assert arguments.options.output_dir != '.', 'Do not use . as output directory please.'

                    # Create the project folder and change the working directory
                    output_dir = str(arguments.options.output_dir)
                    os.makedirs(output_dir, exist_ok=arguments.options.exist_ok)
                    os.chdir(output_dir)

                    for dir in arguments.options.default_dirs:
                        os.makedirs(str(dir), exist_ok=arguments.options.exist_ok)

                    # check if the configuration file exists already
                    if arguments.options.exist_ok:
                        try:
                            new_args = read_yaml(arguments.options.config_file)
                            assert 'options' in new_args.keys(), 'Loaded configuration does not have options.'
                            assert 'git_hash' in new_args['options'].keys() and 'timestamp' in new_args['options'].keys()
                            assert new_args['options']['git_hash'] == arguments.options.git_hash, 'Different git versions.'

                            options = new_args['options']
                            new_args.pop('options')

                            arguments.options.timestamp = options['timestamp']
                            arguments.update(new_args)
                        except FileExistsError:
                            pass

                    if arguments.options.verbose and is_interactive_shell():
                        print(arguments.to_dict(), file=sys.stderr)

                    with open(arguments.options.output_file, 'a') as out, open(arguments.options.error_file, 'a') as err:
                        if arguments.options.verbose and is_interactive_shell():
                            out_file = TeeFile(out, sys.stdout)
                            err_file = TeeFile(err, sys.stderr)
                        else:
                            out_file, err_file = out, err

                        with redirect_stdout(out_file), redirect_stderr(err_file):
                            func(arguments)

                except Exception as e:
                    arguments.update({'exception thrown': f'"{type(e).__name__}: {str(e)}"'})
                    raise e

                finally:
                    with open(arguments.options.config_file, 'w') as file:
                        arguments.pop('pwd')
                        yaml.safe_dump(arguments.to_dict(), file)

            return wrapper
        return __experiment_decorator

    assert len(args) == 0 or (len(args) == 1) and callable(args[0]), 'If you want to set some argument, use keywords.'

    if len(args) == 1 and callable(args[0]):
        assert len(kwargs) == 0
        return _experiment_decorator()(args[0])
    else:
        return _experiment_decorator(**kwargs)


def CLIConfig(func):
    """ Shortcut to read the experiment options from the command line."""
    @click.option('--output-dir', '-dir', type=click.Path(exists=False, dir_okay=True), help='Output directory.')
    @click.option('--output-file', '-out', type=str, help='Output filename.')
    @click.option('--error-file', '-err', type=str, help='Error filename.')
    @click.option('--config-file', '-conf', type=str, help='Configuration filename.')
    @click.option('--exist-ok', type=bool, is_flag=True, help='Whether it is ok if the directory already exists.')
    @click.option('--verbose', is_flag=True)
    @wraps(func)
    def wrapper(*args, output_dir=None, output_file=None, error_file=None, config_file=None, exist_ok=None, **kwargs):
        options = {}
        if output_file is not None: options['output_file'] = output_file
        if error_file is not None: options['error_file'] = error_file
        if config_file is not None: options['config_file'] = config_file
        if exist_ok is not None: options['exist_ok'] = exist_ok
        if output_dir is not None: options['output_dir'] = output_dir

        return func(Arguments(options=options), *args, **kwargs)

    return wrapper


def command(func):
    return click.command()(func)


def experiment(*args, **kwargs):

    def wrapper(**kwargs):
        def _wrapper(func):
            @command
            @CLIConfig
            @YAMLConfig
            @experiment_wrapper(**kwargs)
            @wraps(func)
            def __wrapper(*args, **kwargs):
                func(*args, **kwargs)

            return __wrapper

        return _wrapper

    if len(args) == 1 and callable(args[0]):
        assert len(kwargs) == 0
        return wrapper()(args[0])
    else:
        return wrapper(**kwargs)


if __name__ == '__main__':
    # @click.option('-smth', help='Something', required=False)
    # @command
    # @CLIConfig
    # @YAMLConfig
    # @experiment_wrapper(verbose=True)
    # def foo(config):
    #     print(config.to_dict())
    #     print('test2')
    #     print('test', file=sys.stderr)
    #     # raise Exception('esto es un fallo')

    @click.option('-smth', help='Something', required=False)
    @experiment(verbose=True, output_dir='result', default_dirs=['plots', 'checkpoints'])
    def foo(config):
        print(config.to_dict())
        print('test2')
        print('test', file=sys.stderr)
        # raise Exception('esto es un fallo')

    foo()
    print('haha')
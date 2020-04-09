import os
import sys
import subprocess
from functools import wraps
from datetime import datetime
from contextlib import redirect_stdout, redirect_stderr

import yaml
import click

from mlsuite.experiments.arguments import Arguments


command = lambda func: click.command()(func)


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
    return not sys.__stdin__.isatty()


def experiment(*args, **kwargs):
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
        arguments = Arguments(options={
            'output_dir': '.',
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
                # if 'config' in kwargs.keys():
                #     config = kwargs.pop('config')
                #     if config is not None:
                #         arguments.update(config)

                arguments.update(*args, **kwargs)

                if arguments.options.verbose and is_interactive_shell():
                    print(arguments.to_dict(), file=sys.stderr)

                if arguments.options.output_dir != '.':
                    # Create the project folder and change the working directory
                    output_dir = arguments.replace_placeholders(arguments.options.output_dir)
                    os.makedirs(output_dir, exist_ok=arguments.options.exist_ok)
                    os.chdir(output_dir)

                with open(arguments.options.output_file, 'a') as out, open(arguments.options.error_file, 'a') as err:
                    if arguments.options.verbose and is_interactive_shell():
                        out_file = TeeFile(out, sys.stdout)
                        err_file = TeeFile(err, sys.stderr)
                    else:
                        out_file, err_file = out, err

                    with redirect_stdout(out_file), redirect_stderr(err_file):
                        func(arguments)

                with open(arguments.options.config_file, 'w') as file:
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
    @click.option('--output_file', '-out', type=str, help='Output filename.')
    @click.option('--error_file', '-err', type=str, help='Error filename.')
    @click.option('--config_file', '-conf', type=str, help='Configuration filename.')
    @click.option('--exist_ok', type=bool, help='Whether it is ok if the directory already exists.')
    @wraps(func)
    def wrapper(*args, output_file=None, error_file=None, config_file=None, exist_ok=None, **kwargs):
        options = {}
        if output_file is not None: options['output_file'] = output_file
        if error_file is not None: options['error_file'] = error_file
        if config_file is not None: options['config_file'] = config_file
        if exist_ok is not None: options['exist_ok'] = exist_ok

        return func(Arguments(options=options), *args, **kwargs)

    return wrapper


if __name__ == '__main__':
    from mlsuite.experiments.yaml_handlers import YAMLConfig

    @command
    @CLIConfig
    @YAMLConfig
    @click.option('-smth', help='Something', required=False)
    @experiment(verbose=True)
    def foo(config):
        print(config)
        print('test2')

    foo()
    print('haha')
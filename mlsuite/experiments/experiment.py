import os
import sys
import functools
import subprocess
from datetime import datetime
from contextlib import redirect_stdout, redirect_stderr

import yaml

from mlsuite.experiments.arguments import Arguments


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
            'config_filename': 'config.yml',
        })
        arguments.options.update(**kwargs)

        # Add git version to the config file
        try:
            arguments.options.update(git_hash=subprocess.check_output(["git", "describe", "--always"],
                                                              stderr=subprocess.DEVNULL).strip())
        except subprocess.CalledProcessError:
            pass

        # Add timestamp to the config file
        arguments.options.update(timestamp=datetime.today().strftime('%Y-%m-%d-%H:%M:%S'))

        def __experiment_decorator(func):
            @functools.wraps(func)
            def wrapper(*args, config=None, **kwargs):
                if config is not None:
                    arguments.update(config)

                arguments.update(*args, **kwargs)

                if arguments.options.verbose and is_interactive_shell():
                    print(arguments.to_dict(), file=sys.stderr)

                if arguments.options.output_dir != '.':
                    # Create the project folder and change the working directory
                    output_dir = arguments.replace_placeholders(arguments.options.output_dir)
                    os.makedirs(output_dir, exist_ok=arguments.options.exist_ok)
                    os.chdir(output_dir)

                with open(arguments.options.config_filename, 'w') as file:
                    yaml.safe_dump(arguments.to_dict(), file)

                with open(arguments.options.output_file, 'a') as out, open(arguments.options.error_file, 'a') as err:
                    if arguments.options.verbose and is_interactive_shell():
                        out_file = TeeFile(out, sys.stdout)
                        err_file = TeeFile(err, sys.stderr)
                    else:
                        out_file, err_file = out, err

                    with redirect_stdout(out_file), redirect_stderr(err_file):
                        func(arguments)

            return wrapper
        return __experiment_decorator

    assert len(args) == 0 or (len(args) == 1) and callable(args[0]), 'If you want to set some argument, use keywords.'

    if len(args) == 1 and callable(args[0]):
        assert len(kwargs) == 0
        return _experiment_decorator()(args[0])
    else:
        return _experiment_decorator(**kwargs)


if __name__ == '__main__':
# if True:
    # @experiment
    # def foo():
    #     print('test1')
    # foo()

    import click
    from mlsuite.experiments.yaml_handlers import YAMLConfig, read_yaml_click

    # @YAMLConfig


    # @click.command()
    # @click.option('--config_file', '-c', multiple=True, help='YAML configuration file', callback=read_yaml_click)
    @YAMLConfig
    # @click.option('--algo', '-a', help='Algo', required=True)
    @experiment(verbose=True)
    def foo(config):
        print(config)
        print('test2')
    foo()

    print('haha')

    # @experiment('other')
    # def foo():
    #     print('test3')
    # foo()
from pathlib import Path
from functools import wraps

import yaml
import click

from mlsuite.experiments.arguments import Arguments


def read_yaml(path):
    """Safely reads a YAML file and returns its content as a dictionary."""
    path = Path(path)
    assert path.exists() and path.is_file(), f'{path} doesn\'t exist or is not a file.'

    with path.open('r') as file:
        content = yaml.safe_load(file)
        return content


def read_yaml_click(ctx, param, value):
    if value is not None:
        config = Arguments()
        for path in value:
            config.update(read_yaml(path))
        return config


def YAMLConfig(func):
    """ Reads YAML filenames as arguments of the command line, parses them, and pass the dictionary.

        You can pass as many files as you want with `-c filename1 -c filename2`. If two files define the same option
        the latter is the one that takes priority.
    """
    @click.command()
    @click.option('--config_file', '-c', multiple=True, help='YAML configuration file', callback=read_yaml_click)
    @wraps(func)
    def wrapper(*args, config_file, **kwargs):
        return func(*args, **kwargs, config=config_file)

    return wrapper

from pathlib import Path

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


def YAMLConfig(func):
    """ Reads YAML filenames as arguments of the command line, parses them, and pass the dictionary.

        You can pass as many files as you want with `-c filename1 -c filename2`. If two files define the same option
        the latter is the one that takes priority.
    """
    @click.command()
    @click.option('--config_file', '-c', multiple=True, help='YAML configuration file')
    def wrapper(*args, config_file, **kwargs):
        config = Arguments()
        for filename in config_file:
            config.update(read_yaml(filename))

        return func(*args, **kwargs, config=config)
    return wrapper()
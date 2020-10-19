import sys

import torch
import click

from mlsuite import experiment
from mlsuite.pytorch import fix_seed
from mlsuite.utils import keyboard_stoppable, timed


def validate_args(args) -> None:  # Make sure that our arguments are as they should
    if 'cuda' in args.device and not torch.cuda.is_available():  # We can access to them using dot notation
        print('CUDA requested but not available.', file=sys.stderr)  # printing to the error output
        args.update({'device': 'cpu'})  # updating the parameters

    if args.model_type == 'cluster':
        args.dataset.extra.update({'num clusters': args.model.num_clusters})


def create_model(args):
    return None


@timed  # We want to know how much our training takes
@keyboard_stoppable  # We can stop the function using ctrl+C in a safe way
def train(model, args):
    print("Starting training")
    for i in range(10000000): # some waiting time
        pass

    print("Training done")


# Try running python nice_example.py --help
# and python nice_example.py -c prueba.yml -device cuda --exist-ok

@click.option('-device', type=str, required=True)
@click.option('-other-parameter', type=int, default=10)  # Add parameters to the CLI as you please
@experiment(output_dir='my_results', default_dirs=['plots', 'checkpoints'])  # Custom options
def main(args):  # If it fails because the directory exists, put --exist-ok in the command line arguments
    validate_args(args)
    fix_seed(1)

    model = create_model(args)
    train(model, args)


if __name__ == '__main__':
    main()  # Try also the command line (and the --help option!)

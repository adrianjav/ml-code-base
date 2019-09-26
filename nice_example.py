import sys

import argparse
import torch

import mlsuite
from mlsuite import arguments as args, directories as dirs
from mlsuite.pytorch import fix_seed

import utils.plotting as plt
from utils import ProbabilisticModel, Normalizer
from utils.datasets import normalize_by_std, normalize_by_max, scale_data, get_dataloader
from models import create_model


# TODO temporary
# dirs.create_dirs.value(False)
# mlsuite.save_on_del.value(False)


def validate_args() -> None:
    if 'cuda' in args.device and not torch.cuda.is_available():
        print('CUDA requested but not available.', file=sys.stderr)
        args.update({'device': 'cpu'})

    if args.model_type == 'cluster':
        args.dataset.extra.update({'num clusters': args.model.num_clusters})

    # return context.validate_args(args)


def generate_preprocess_functions(prob_model):
    preprocess_fn = [prob_model.preprocess_data]

    if len(args.preprocess.ours) > 0:
        normalizer = Normalizer(prob_model, args.preprocess.angle, args.preprocess.epochs, args.preprocess.ours)

        # preprocess_fn += [normalizer.optimize]
        preprocess_fn += [lambda x: normalizer.optimize(x,  step='angle')]
        preprocess_fn += [lambda x: normalizer.optimize(x, step='epsilon')]

    preprocess_fn += [normalize_by_max(prob_model, args.preprocess.max)]
    preprocess_fn += [normalize_by_std(prob_model, args.preprocess.std)]
    preprocess_fn += [scale_data(prob_model, args.preprocess.arbitrary)]

    # preprocess_fn += [lambda x: x.abs()]

    return preprocess_fn


def print_suff_stats(prob_model, x):
    for i, dist_i in enumerate(prob_model):
        suff_stats = dist_i.sufficient_statistics(x[:, i])
        suff_stats = [v.mean().item() for v in suff_stats]
        print(f'mean sufficient statistics of [{i}={dist_i}]: ({x[:,i].mean()}) {suff_stats}')


def print_data_info(prob_model, loader):
    print()
    print('#' * 20)

    print('Original data')
    print_suff_stats(prob_model, loader.dataset.data)
    plt.plot_angles_with_pdf(loader.dataset.data, prob_model, f'{dirs.plots}/angles_originals', title='Angles Originals')
    plt.plot_magnitude_with_pdf(loader.dataset.data, prob_model, f'{dirs.plots}/magnitude_originals', title='Magnitude Originals')

    print()
    print(f'weights = {prob_model.weights}')
    print()

    print('Scaled data')
    print_suff_stats(prob_model, prob_model.scale_data(loader.dataset.data))
    plt.plot_angles_with_pdf(prob_model.scale_data(loader.dataset.data), prob_model, f'{dirs.plots}/angles_scaled', title='Angles Scaled')
    plt.plot_magnitude_with_pdf(prob_model.scale_data(loader.dataset.data), prob_model, f'{dirs.plots}/magnitude_scaled', title='Magnitude Scaled')

    print('#' * 20)
    print()

    # context.print_info(model, loader, args)

from mlsuite import FailSafe

class A(metaclass=FailSafe):
    def __init__(self):
        self.epoch = 0

def main():
    # Configuration
    parser = argparse.ArgumentParser('')
    parser.add_argument('-config', type=str, default='default_settings.yaml', help='configuration file')
    parser.add_argument('-pr-config', type=str, default='experiment_settings.yaml', help='priority configuration file')
    parser = parser.parse_args()

    args.update(filename=parser.config)
    args.update(filename=parser.pr_config)

    # Validation and initial setup
    validate_args()
    fix_seed(args.seed)

    prob_model = ProbabilisticModel(args.probabilistic_model)
    preprocess_fn = generate_preprocess_functions(prob_model)
    loader = mlsuite.failsafe_result()(get_dataloader)(preprocess_fn=preprocess_fn)

    print_data_info(prob_model, loader)

    model = create_model(prob_model)
    #
    # @mlsuite.failsafe_result()
    # def foo():
    #     print('ive been called')
    #     return 2
    #     #return p
    #
    # foo()

    # @mlsuite.execute_once
    # def foo2():
    #     print('hola')
    #     raise Exception
    #
    # foo2()

    @mlsuite.keyboard_stopable
    def loop(a):
        print('starting at', a.epoch)
        for i in range(a.epoch, 1000000000):
            a.epoch = i

    a = A()
    a.save(a.__path__)
    loop(a)


    # # TODO load things
    # prob_model.__del__()


if __name__ == '__main__':
    main()
    sys.exit(0)
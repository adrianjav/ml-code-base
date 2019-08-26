import atexit

import torch
import torch.backends.cudnn
import torch.cuda

if int(torch.__version__.split('.')[0]) >= 1 and int(torch.__version__.split('.')[1]) >= 2:
    from torch.utils.tensorboard import SummaryWriter
else:
    from tensorboardX import SummaryWriter


def fix_seed(seed) -> None:
    """
    Fixes the seed of Pytorch's RNG and put the CuDNN backend in deterministic mode.
    :param seed: seed to be used.
    """
    if seed is not None:
        torch.backends.cudnn.deterministic = True
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)


def to_one_hot(x, size):
    """
    Converts a tensor `x` into a one-hot representation of size `size` where x_one_hot[i] is a one hot with ones at the
    positions x[i].
    :param x: tensor with the indexes of the one-elements.
    :param size: size of the resulting tensor.
    :return: the one-hot tensor.
    """
    x_one_hot = x.new_zeros(x.size(0), size)
    x_one_hot.scatter_(1, x.unsqueeze(-1).long(), 1).float()

    return x_one_hot


class LazySummaryWriter(object):
    """
    Lazy implementation of a SummaryWriter of Tensorboard.
    """

    def __init__(self, log_dir):
        setattr(self, 'wrapped', None)
        self._log_dir = log_dir

    @property
    def log_dir(self):
        return self._log_dir

    @log_dir.setter
    def log_dir(self, value):
        assert object.__getattribute__(self, 'wrapped') is None, "The SummaryWritter has already been initialized."
        self._log_dir = value

    def __getattr__(self, item):
        if item != 'wrapped':
            return getattr(self.wrapped, item)
        raise AttributeError(item)

    def __getattribute__(self, item):
        res = super(LazySummaryWriter, self).__getattribute__(item)
        if item == 'wrapped' and res is None:
            res = SummaryWriter(self.log_dir.root)
            atexit.register(res.close)
            setattr(self, 'wrapped', res)

        return res

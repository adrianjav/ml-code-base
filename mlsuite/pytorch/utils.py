import torch.backends.cudnn
import torch.cuda


def fix_seed(seed) -> None:
    """
    Fixes the seed of Pytorch's RNG and sets the backend (CuDNN) in deterministic mode.
    :param seed:
    """
    if seed is not None:
        torch.backends.cudnn.deterministic = True
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)


def to_one_hot(x, size):
    """
    Converts a tensor `x` into a one-hot representation of size `size` where x_one_hot[i] is a one hot with ones at the
    positions x[i].
    :param x: indexes tensor.
    :param size: size of the resulting tensor.
    :return: the one-hot tensor.
    """
    x_one_hot = x.new_zeros(x.size(0), size)
    x_one_hot.scatter_(1, x.unsqueeze(-1).long(), 1).float()

    return x_one_hot
"""
Pytorch common utilities that can be handy to have in a common place.
"""

from .utils import fix_seed, to_one_hot, LazySummaryWriter
from mlsuite import directories

summary_writer = LazySummaryWriter(directories.root)

__all__ = ['fix_seed', 'to_one_hot', 'summary_writer']
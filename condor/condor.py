import sys
import mlsuite
from mlsuite import directories as dirs, arguments as args


def init():
    mlsuite.load_config(filename='config.yaml')


if __name__ == "__main__":
    init()
    print(dict(dirs))
    print(dict(args))
    sys.exit(0)

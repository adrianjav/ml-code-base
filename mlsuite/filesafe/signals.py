import sys
import signal
import atexit
from functools import wraps


def exit_gracefully(signum, frame):
    class SigtermException(Exception):
        pass

    raise SigtermException('SIGTERM signal received')


# Code to ensure that there is an exit code that we can check when exiting (an act wrt it)
def exit_hook(func):
    @wraps(func)
    def _exit_hook(code=0):
        sys.exit_code = code
        func(code)
    return _exit_hook


def except_hook(func):  # TODO it breaks when debugging with PyCharm
    @wraps(func)
    def except_hook_(*args, **kwargs):
        sys.exit_code = None
        func(*args, **kwargs)
    return except_hook_


def exit_assert():
    assert hasattr(sys, 'exit_code'), 'Make sure to call "sys.exit" in your program.'  # TODO exit function?


atexit.register(exit_assert)
sys.exit = exit_hook(sys.exit)
sys.excepthook = except_hook(sys.excepthook)

signal.signal(signal.SIGTERM, exit_gracefully)

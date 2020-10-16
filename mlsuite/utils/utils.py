import sys
import time
from functools import wraps


def timed(func):
    """
    Decorator that prints out the running time (in seconds) of the decorated function.
    """
    @wraps(func)
    def timed_(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()

        print(f'{func.__name__} completed in {end - start :.3f} seconds.')
        print()

        return result
    return timed_


def keyboard_stoppable(func):
    """
    Decorator that captures a keyboard interruption signal (SIGINT) and prints out an informative message.
    """
    @wraps(func)
    def keyboard_stoppable_(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            print(f'{func.__name__} interrupted by keyboard.', file=sys.stderr)
            pass
    return keyboard_stoppable_


if __name__ == '__main__':
    @timed
    def fast():
        print("hello")

    fast()

    def slow():
        for i in range(10000000):
            pass

    timed(slow)()

    @keyboard_stoppable
    def function_that_can_be_interrupted(some_param):
        raise KeyboardInterrupt()

    function_that_can_be_interrupted(2)

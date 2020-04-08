import sys
import time
import functools


def timed(func):
    @functools.wraps(func)
    def timed_(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()

        print(f'{func.__name__} completed in {end - start :.3f} seconds.')
        print()

        return result
    return timed_


def keyboard_stopable(func):
    @functools.wraps(func)
    def keyboard_stopable_(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            print(f'{func.__name__} interrupted by keyboard.', file=sys.stderr)
            pass
    return keyboard_stopable_


if __name__ == '__main__':
    @timed
    def fast():
        print("hello")

    fast()

    def slow():
        for i in range(10000000):
            pass

    timed(slow)()

    @timed
    @keyboard_stopable
    def extremely_slow():
        for i in range(int(1e20)):
            pass

    extremely_slow()
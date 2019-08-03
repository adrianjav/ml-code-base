import time
import functools


def timed(func):
    @functools.wraps(func)
    def timed_(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()

        print(f'{func.__name__} completed in {end - start :.3f} seconds.')
        return result
    return timed_


if __name__ == '__main__':
    @timed
    def fast():
        print("hello")

    fast()

    def slow():
        for i in range(10000000):
            pass

    timed(slow)()
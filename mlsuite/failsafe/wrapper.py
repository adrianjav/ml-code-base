from functools import wraps

from .failsafe import default_load, FailSafe


# TODO for now this has the basic options (non-configurable at all)
class FailSafeWrapper(metaclass=FailSafe):
    def __init__(self, func, *args, **kwargs):
        try:
            self.wrapped = func(*args, **kwargs)
            self.func_name = func.__name__
        except Exception:
            self.wrapped = None
            raise

    def __len__(self): return len(self.wrapped)
    def __iter__(self): return self.wrapped.__iter__()
    def __getitem__(self, item): return self.wrapped.__getitem__(item)

    @staticmethod
    def load(path):
        result = default_load(path)
        if result is None or result.wrapped is None:
            return None
        return result

    def __filename__(self, oid):
        return f'{self.func_name}_{oid}.pickle'

    def __getattr__(self, item):
        if item != 'wrapped':  # This happens if save is called when CPython is already shutting down
            return getattr(self.wrapped, item)
        raise AttributeError(item)

    def __call__(self, *args, **kwargs):
        return self.wrapped(*args, **kwargs)

    def __str__(self):
        return str(self.wrapped)


def failsafe_result(func):
    @wraps(func)
    def failsafe_result_wrapper(*args, **kwargs):
        wrapper = FailSafeWrapper(func, *args, **kwargs)
        return wrapper

    return failsafe_result_wrapper


def execute_once(func):
    @failsafe_result
    @wraps(func)
    def execute_once_(*args, **kwargs):
        result = func(*args, **kwargs)
        return result if result is not None else 1
    return execute_once_


def failsafe_object(obj):
    def failsafe_object_(obj):
        return obj

    failsafe_object_.__name__ = type(obj).__name__  # Save it with the name of the object safed
    return failsafe_result(failsafe_object_)(obj)
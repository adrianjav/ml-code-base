import functools


class lazy_property(object):
    def __init__(self, function):
        self.function = function
        functools.update_wrapper(self, function)

    def __get__(self, obj, type_):
        if obj is None:
            return self
        val = self.function(obj)
        obj.__dict__[self.function.__name__] = val
        return val


class SideEffect(type):
    def __call__(cls, *args, **kwargs):
        instance = super(SideEffect, cls).__call__(*args, **kwargs)
        return instance.side_effect()
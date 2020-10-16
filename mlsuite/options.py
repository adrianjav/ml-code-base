from functools import partial, wraps


def with_stmt(outer_func):
    """
    Takes a function an returns a context manager that can be used as decorator and in a with statement.

    :param outer_func Function that works as a setter/getter when some/no arguments are passed to it.
    """

    class CM(object):
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs
            self.old_value = []

        def __enter__(self):
            self.old_value.append(outer_func())
            outer_func(*self.args, **self.kwargs)

        def __exit__(self, exc_type, exc_val, exc_tb):
            prev_value = self.old_value.pop()
            outer_func(prev_value) if prev_value is not None else outer_func(reset=True)
            return False

        def __call__(self, inner_func):
            @wraps(inner_func)
            def decorate_inner_func(*args, **kwargs):
                with self:
                    return inner_func(*args, **kwargs)
            return decorate_inner_func

        @staticmethod
        def value(*args, **kwargs):  # TODO should I allow to change it like this?
            return outer_func(*args, **kwargs)

    return CM


class Options(type):
    def __init__(cls, name, bases, namespace):
        super(Options, cls).__init__(name, bases, namespace)

        def getter(self, name, value=None):
            if value is not None:
                setattr(self, name, value)
            return getattr(self, name)

        for attr in [x for x in namespace if x.startswith('_opt_')]:
            setattr(cls, attr[len('_opt_'):], with_stmt(partial(getter, cls, attr)))


class GlobalOptions(metaclass=Options):
    # _opt_inherit_on_creation = False
    # _opt_load_on_init = True
    # _opt_save_on_del = True
    _opt_replace_placeholders = True


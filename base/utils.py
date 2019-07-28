from functools import partialmethod, partial, wraps


class SideEffect(type):
    def __call__(cls, *args, **kwargs):
        instance = super(SideEffect, cls).__call__(*args, **kwargs)
        return instance.side_effect()

# a = A()
# print(a.create_dirs.value())
# print(a.create_dirs.value(False))
# print(a.create_dirs.value())
# with a.create_dirs(False):
#     print(a.create_dirs.value())
#     with a.create_dirs(reset=True):
#         print(a.create_dirs.value())
# print(a.create_dirs(reset=True))


def with_stmt(outer_func):
    class CM(object):
        def __init__(self, *args, **kwargs):
            self.old_value = outer_func()
            self.args = args
            self.kwargs = kwargs

        def __enter__(self):
            outer_func(*self.args, **self.kwargs)

        def __exit__(self, exc_type, exc_val, exc_tb):
            outer_func(self.old_value) if self.old_value is not None else outer_func(reset=True)
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

    def __call__(cls, *args, **kwargs):
        instance = super(Options, cls).__call__(*args, **kwargs)

        def getter(self, name, value=None, reset=False):
            assert not reset or (reset and not value)

            if reset:
                setattr(self, name, None)

            if value is not None:
                setattr(self, name, value)

            return getattr(self, name)

        def real_value(self, name, value=None):
            if value is not None:
                setattr(self, name, value)
            else:
                value = getattr(self, name)

            supervalue = getattr(super(type(self), self), name[len('_opt_'):]).value()
            return value if value is not None else supervalue

        for attr in [x for x in dir(cls) if x.startswith('_opt_')]:
            setattr(instance, attr, None)
            setattr(instance, attr[len('_opt_'):], with_stmt(partial(getter, instance, attr)))
            getattr(instance, attr[len('_opt_'):]).value = staticmethod(partial(real_value, instance, attr))

        return instance

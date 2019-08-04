from functools import partial, wraps


def with_stmt(outer_func):
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


def getstate(self):
    state = self.__dict__
    for attr in [v for v in dir(self) if v.startswith('_opt_')]:
        if attr[len('_opt_'):] in state.keys():
            state.pop(attr[len('_opt_'):])
    return state


def safe_getstate(getstate):
    def safe_getstate_(self):
        import inspect  # TODO temporary

        new_state = {'state': getstate(self)}
        new_state.update({k: v for k, v in inspect.getmembers(self) if k.startswith('_opt_')})

        return new_state
    return safe_getstate_


def safe_setstate(setstate):
    def safe_setstate_(self, state):
        for k, v in state.items():
            if k.startswith('_opt_'):
                setattr(self, k, v)

        setstate(self, state['state'])
    return safe_setstate_


class Options(type):
    def __init__(cls, name, bases, namespace):
        super(Options, cls).__init__(name, bases, namespace)

        def getter(self, name, value=None):
            if value is not None:
                setattr(self, name, value)
            return getattr(self, name)

        for attr in [x for x in namespace if x.startswith('_opt_')]:
            setattr(cls, attr[len('_opt_'):], with_stmt(partial(getter, cls, attr)))

        setattr(cls, '__getstate__', safe_getstate(getattr(cls, '__getstate__', getstate)))  # can't pickle CM
        setattr(cls, '__setstate__', safe_setstate(getattr(cls, '__setstate__', lambda s, d: s.__dict__.update(d))))

    def decorate(cls, instance):

        def getter(self, name, value=None, reset=False):
            assert not reset or (reset and not value)

            if reset:
                setattr(self, name, None)

            if value is not None:
                setattr(self, name, value)

            return getattr(self, name)

        def real_value(self, name, value=None, reset=None):
            assert not reset or (reset and not value)

            if reset:
                setattr(self, name, None)

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

    def __call__(cls, *args, **kwargs):
        instance = super(Options, cls).__call__(*args, **kwargs)
        cls.decorate(instance)
        return instance

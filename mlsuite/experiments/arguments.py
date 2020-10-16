import re

from dotmap import DotMap

from options import GlobalOptions


def _parse(x):
    return x.replace(' ', '_')


class LazyString(str):
    """Wrapper class to replace placeholders in the argument's strings"""
    _root = None

    def __str__(self):
        if GlobalOptions.replace_placeholders.value():
            return type(self)._root.replace_placeholders(self, recurse=True)

        return self

    def __repr__(self):
        # with GlobalOptions.replace_placeholders(False):
        return str(self)


class Arguments(DotMap):
    """ Class to handle arguments with dot notation."""
    def __init__(self, *args, **kwargs):
        super(Arguments, self).__init__(_dynamic=False)
        self.update(*args, **kwargs)

    def __setattr__(self, key, value):
        super(Arguments, self).__setattr__(_parse(key), value if not isinstance(value, str) else LazyString(value))

    def __getattr__(self, item: str) -> object:
        item = _parse(item)
        try:
            return super(Arguments, self).__getattr__(item)
        except KeyError as exc:
            raise AttributeError(*exc.args) from exc

    def update(self, *args, **kwargs):
        for item in args:
            self.update(**item)

        new_kwargs = {}
        for k, v in kwargs.items():
            parsed_k = _parse(k)

            if isinstance(v, (Arguments, dict)) and isinstance(getattr(self, parsed_k, None), Arguments):
                getattr(self, parsed_k).update(v)
            else:
                if isinstance(v, dict):
                    v = Arguments(v)
                elif isinstance(v, str):
                    v = LazyString(v)

                new_kwargs[parsed_k] = v

        super(Arguments, self).update(**new_kwargs)

    def to_dict(self) -> dict:
        return self.toDict()

    def replace_placeholders(self, pattern: str, recurse=True) -> str:
        """ Returns project string where placeholders of the form `${nested.key}` replaced by their value.

        :param pattern: string with the placeholders
        :param recurse: whether or not to keep replacing the string until exhausted
        :return: project string like pattern with the proper value of the placeholders.
        """

        result, pos = '', 0
        for match in re.finditer(r'\$\{.*?\}', pattern):
            request = match.group()[2:-1].split(sep='.')
            value = self
            for item in request:
                value = getattr(value, item)
            assert not isinstance(value, Arguments), f'pattern {match.group()} failed.'

            result += pattern[pos:match.start()] + (self.replace_placeholders(value) if recurse and isinstance(value, str) else str(value))
            pos = match.end()

        result += pattern[pos:]
        return result


class ArgumentsHeader(Arguments):
    """Dummy class for the root of the arguments"""
    def __init__(self, *args, **kwargs):
        super(ArgumentsHeader, self).__init__(*args, **kwargs)
        LazyString._root = self


if __name__ == '__main__':
    args = ArgumentsHeader()
    args.update({'I have spaces': 1, 'b': {'c': 2, 'd': 'e'}})
    print(args)
    print(args.I_have_spaces)

    args.device = 'cuda'
    print(args)

    args.b.c = Arguments({'hello': 'world'})

    print(args.to_dict())

    print(hasattr(args, 'e'))

    args.update({'g': {'one': 1, 'two': 'hello ${b.c.hello}'}, 'project': 4})

    print(type(LazyString('prueba')).__mro__)

    print('='*10)
    with GlobalOptions.replace_placeholders(False):
        print(args)
    print(dict(args))
    print(args.to_dict())
    print(args.g.two)
    # args.g.two += ' of warcraft'
    # print(args.g.two)
    # args.g.two += ' (${I_have_spaces})'
    print(args.g.two)
    with GlobalOptions.replace_placeholders(False):
        print(args.to_dict())
    print('=' * 10)

    import yaml
    from yaml.representer import SafeRepresenter
    yaml.add_representer(LazyString, SafeRepresenter.represent_str, yaml.SafeDumper)

    with open('args_test.yml', 'w') as f:
        yaml.safe_dump(args.to_dict(), f)

    exit(0)
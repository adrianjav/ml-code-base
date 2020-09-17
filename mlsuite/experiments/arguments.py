import re

from dotmap import DotMap


class Arguments(DotMap):
    """ Class to handle arguments with dot notation."""
    _parse = lambda x: x.replace(' ', '_')

    def __init__(self, *args, **kwargs):
        super(Arguments, self).__init__(_dynamic=False)
        self.update(*args, **kwargs)

    def __setattr__(self, key, value):
        super(Arguments, self).__setattr__(key.replace(' ', '_'), value)

    def __getattr__(self, item: str) -> object:
        item = self.__class__._parse(item)
        try:
            return super(Arguments, self).__getattr__(item)
        except KeyError as exc:
            raise AttributeError(*exc.args) from exc

    def update(self, *args, **kwargs):
        for item in args:
            self.update(**item)

        new_kwargs = {}
        for k, v in kwargs.items():
            parsed_k = self.__class__._parse(k)

            if isinstance(v, (Arguments, dict)) and isinstance(getattr(self, parsed_k, None), Arguments):
                getattr(self, parsed_k).update(v)
            else:
                new_kwargs[parsed_k] = Arguments(v) if isinstance(v, dict) else v

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

            result += pattern[pos:match.start()] + (self.replace_placeholders(value) if recurse and type(value) == str else str(value))
            pos = match.end()

        result += pattern[pos:]
        return result


if __name__ == '__main__':
    args = Arguments()
    args.update({'I have spaces': 1, 'b': {'c': 2, 'd': 'e'}})
    print(args)
    print(args.I_have_spaces)

    args.device = 'cuda'
    print(args)

    args.b.c = Arguments({'hello': 'world'})

    print(args.to_dict())

    print(hasattr(args, 'e'))

    args.update({'g': {'one': 1, 'two': 'hello ${b.c.hello}'}, 'project': 4})
    print(args)

    print(args.replace_placeholders(args.g.two))

    import yaml
    with open('args_test.yml', 'w') as f:
        yaml.safe_dump(args.to_dict(), f)

    exit(0)
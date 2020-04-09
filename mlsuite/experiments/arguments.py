from __future__ import annotations

import re

from dotmap import DotMap


class Arguments(DotMap):
    """ Class to handle arguments with dot notation."""
    def __init__(self, *args, **kwargs):
        super(Arguments, self).__init__(_dynamic=False)
        self.update(*args, **kwargs)

    def __setattr__(self, key, value):
        super(Arguments, self).__setattr__(key.replace(' ', '_'), value)

    def __getattr__(self, item: str) -> object:
        item = item.replace(' ', '_')
        try:
            return super(Arguments, self).__getattr__(item)
        except KeyError as exc:
            raise AttributeError(*exc.args) from exc

    def update(self, *args, **kwargs):
        new_kwargs = kwargs
        for item in args:
            assert isinstance(item, dict), item
            new_kwargs.update(item)

        new_kwargs = {key.replace(' ', '_'): self.__class__(item) if isinstance(item, dict) else item for key, item in kwargs.items()}
        to_pop = []
        for k, v in new_kwargs.items():
            if isinstance(v, Arguments) and isinstance(getattr(self, k, None), Arguments):
                getattr(self, k).update(v)
                to_pop.append(k)

        for k in to_pop:
            new_kwargs.pop(k)

        super(Arguments, self).update(**new_kwargs)

    def to_dict(self) -> dict:
        return self.toDict()

    def replace_placeholders(self, pattern: str) -> str:
        """ Returns project string where placeholders of the form `${nested.key}` replaced by their value.

        :param pattern: string with the placeholders
        :return: project string like pattern with the proper value of the placeholders.
        """

        result, pos = '', 0
        for match in re.finditer(r'\$\{.*?\}', pattern):
            request = match.group()[2:-1].split(sep='.')
            value = self
            for item in request:
                value = getattr(value, item)
            assert isinstance(value, str), f'pattern {match.group()} failed.'

            result += pattern[:match.start()] + value
            pos = match.end() + 1

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
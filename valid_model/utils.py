import inspect


def is_descriptor(obj):
    return all((
        hasattr(obj, 'name'),
        hasattr(obj, '__delete__'),
        hasattr(obj, '__get__'),
        hasattr(obj, '__set__')
    ))


class ObjectPrinter(object):
    @classmethod
    def attr_definition(cls, descriptor, tabs=1):
        from .descriptors import Generic

        valid_attributes = {
            'default', 'validator', 'mutator', 'nullable',
            'key', 'value', 'class_obj'
        }
        full_code = []
        for name, value in inspect.getmembers(descriptor):
            if name not in valid_attributes:
                continue
            if name in ('mutator', 'validator'):
                print_val = cls.func_str(name, value)
            elif name in ('key', 'value'):
                if isinstance(value, Generic):
                    params = ObjectPrinter.attr_definition(
                        value, tabs=tabs + 1
                    )
                    leading_tabs = '    ' * tabs
                    params = '\n' + '\n'.join([
                        leading_tabs + l for l in params.splitlines()
                    ])
                else:
                    params = ''

                print_val = '{}({})'.format(value.__class__.__name__, params)
            elif name == 'default' and callable(value) and not isinstance(value, type):
                print_val = cls.func_str(name, value)
            else:
                print_val = cls.static_str(value)
            full_code.append('        {} = {},'.format(name, print_val))
        return '\n'.join(full_code)

    @staticmethod
    def static_str(value):
        if isinstance(value, type):
            return value.__name__
        else:
            return repr(value)

    @classmethod
    def func_str(cls, name, value):
        try:
            print_val = inspect.getsource(value)
        except TypeError:
            return value.__name__
        idx = print_val.find(name)
        print_val = print_val[idx:].split(',')[0]
        print_val = ''.join(print_val.split('=')[1:]).strip()
        print_val = print_val[:-1] if print_val.endswith(',') else print_val
        print_val = print_val[:-1] if print_val.endswith(')') else print_val
        print_val = print_val.strip()
        return print_val

    @classmethod
    def format_class(cls, klass):
        from .base import Object
        from .descriptors import Generic

        assert issubclass(klass, Object)

        full_code = ['class {}(Object):'.format(klass.__name__)]
        attr_descriptors = inspect.getmembers(
            klass, lambda x: isinstance(x, Generic)
        )
        for attr_name, descriptor in attr_descriptors:
            full_code.append('    {} = {}(\n{}\n    )'.format(
                attr_name, descriptor.__class__.__name__,
                cls.attr_definition(descriptor)
            ))
        full_code.append('')

        return '\n'.join(full_code)

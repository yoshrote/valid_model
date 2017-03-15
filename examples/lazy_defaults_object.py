"""
A quick upgrade to Objct so that default values are never actually assigned
unless explicitly set.

This opens a way to change default values of persisted copies of an Object
(such as from a DB) without having some kind of data migration.

LazyInteger = make_lazy(Integer)

class Truck(LazyObject):
    wheels = LazyInteger(default=16)

truck = Truck()
assert truck._fields['wheels'] is DEFAULT
assert truck.wheels == 16
assert 'wheels' not in truck.__json__()
"""
from .base import Object
from .descriptors import Dict, EmbeddedObject, List, Set
DEFAULT = object()


class LazyObject(Object):
    NEVER_LAZY = (Dict, List, Set, EmbeddedObject)

    def __init__(self, **kwargs):
        self._fields = {}
        cls = self.__class__
        for field in self.field_names:  # pylint: disable=E1135,E1133
            if isinstance(field, self.NEVER_LAZY):
                self._fields[field] = getattr(cls, field).get_default()
            else:
                self._fields[field] = DEFAULT
        for key, value in kwargs.items():
            if key in self.field_names:  # pylint: disable=E1135,E1133
                setattr(self, key, value)

    def __json__(self):
        """
        Convert the Object instance and any nested Objects into a dict.
        If a key has the default value, remove it entirely from the result
        """
        json_doc = {}
        for key, value in self._fields.iteritems():
            if hasattr(value, '__json__'):
                json_doc[key] = value.__json__()
            elif isinstance(value, list):
                json_doc[key] = [
                    v.__json__() if hasattr(v, '__json__') else v
                    for v in value
                ]
            elif isinstance(value, dict):
                json_doc[key] = dict(
                    (k, v.__json__()) if hasattr(v, '__json__') else (k, v)
                    for k, v in value.iteritems()
                )
            else:
                json_doc[key] = value

            if json_doc[key] is DEFAULT:
                del json_doc[key]

        return json_doc

    def validate(self):
        """
        Allows for multi-field validation
        """
        for key in self._fields:
            if self._fields[key] is not DEFAULT:
                setattr(self, key, self._fields[key])
        for key, value in self._fields.iteritems():
            if hasattr(value, 'validate'):
                value.validate()
            elif isinstance(value, list):
                for v in value:
                    if hasattr(v, 'validate'):
                        v.validate()


def make_lazy(desc_klass):
    class NewDescriptor(desc_klass):
        def __init__(self, default=None, validator=None, mutator=None, nullable=True):
            super(NewDescriptor, self).__init__(
                default=DEFAULT,
                validator=validator,
                mutator=mutator,
                nullable=nullable
            )
            self.actual_default = default

        def get_actual_default(self):
            if not callable(self.actual_default):
                return self.actual_default
            else:
                return self.actual_default()

        def __get__(self, instance, klass=None):
            value = super(NewDescriptor, self).__get__(instance, klass=klass)
            return value if value is not DEFAULT else self.get_actual_default()

    return NewDescriptor

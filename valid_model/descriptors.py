from datetime import datetime, timedelta

import six

from .base import Generic, Object
from .exc import ValidationError
from .utils import is_descriptor


class SimpleType(Generic):
    """This descriptor will not attempt to coerce the value on __set__."""

    _type_klass = None
    _type_label = None

    def __set__(self, instance, value):
        if value is not None and not isinstance(value, self._type_klass):
            raise ValidationError(
                "{!r} is not {}".format(value, self._type_label),
                self.name
            )
        return Generic.__set__(self, instance, value)


class EmbeddedObject(Generic):
    def __init__(self, class_obj):
        self.class_obj = class_obj

        def validator(obj):
            return isinstance(obj, class_obj)

        Generic.__init__(
            self, default=class_obj, validator=validator
        )

    def __set__(self, instance, value):
        try:
            if isinstance(value, dict):
                value = self.class_obj(**value)
            return Generic.__set__(self, instance, value)
        except ValidationError as ex:
            raise ValidationError(
                ex.msg,
                '{}.{}'.format(self.name, ex.field) if ex.field else self.name
            )


class String(Generic):
    """
    This descriptor attempts to set a unicode string value.

    If the value is type(str) it will be decoded using utf-8.
    """

    def __set__(self, instance, value):
        if value is None or isinstance(value, six.text_type):
            pass
        elif isinstance(value, six.binary_type):
            value = value.decode('utf-8')
        else:
            raise ValidationError(
                "{!r} is not a string".format(value),
                self.name
            )
        return Generic.__set__(self, instance, value)


class _Number(Generic):
    """This descriptor attempts to converts any a value to a number."""

    _number_type = None
    _number_label = None

    def __set__(self, instance, value):
        if value is not None:
            number_like = isinstance(value, (six.integer_types, float))
            is_bool = isinstance(value, bool)

            if not number_like or is_bool:
                raise ValidationError(
                    "{!r} is not {}".format(value, self._number_label),
                    self.name
                )
            else:
                value = int(value)
        return Generic.__set__(self, instance, value)


class Integer(_Number):
    """This descriptor attempts to coerce a number to an integer."""

    _number_type = int
    _number_label = "an int"


class Float(_Number):
    """This descriptor attempts to coerce a number to a float."""

    _number_type = float
    _number_label = "a float"


class Bool(Generic):
    """This descriptor attempts to converts any a value to a boolean."""

    def __set__(self, instance, value):
        if value is not None:
            if value in (0, 1) or isinstance(value, bool):
                value = bool(value)
            else:
                raise ValidationError(
                    "{!r} is not a bool".format(value),
                    self.name
                )
        return Generic.__set__(self, instance, value)


class DateTime(SimpleType):
    """This descriptor attempts to set a datetime value."""

    _type_klass = datetime
    _type_label = "a datetime"


class TimeDelta(SimpleType):
    """This descriptor attempts to set a timedalta value."""

    _type_klass = timedelta
    _type_label = "a timedelta"


NO_DEFAULT = object()


class _Collection(Generic):
    _collection_type = object
    _collection_label = None

    def __init__(self, default=NO_DEFAULT, value=None, validator=None, mutator=None):
        if default is NO_DEFAULT:
            default = self._collection_type
        Generic.__init__(
            self, default=default, validator=validator, mutator=mutator, nullable=False
        )
        if value is not None and not isinstance(value, Generic):
            raise TypeError('value must be None or an instance of Generic')
        self.value = value

    @staticmethod
    def iterate(collection):
        return iter(collection)

    def recursive_validation(self, element):
        """Validate element of collection against `self.value`."""
        dummy = Object()
        if self.value is not None:
            try:
                element = self.value.__set__(dummy, element)
            except ValidationError as ex:
                raise ValidationError(
                    ex.msg,
                    '{}.{}'.format(self.name, ex.field) if ex.field else self.name
                )
        return element

    def add_to_collection(self, collection, element):
        raise NotImplementedError("_add_to_collection")

    def __set__(self, instance, value):
        if value is None:
            value = self._collection_type()
        elif not isinstance(value, self._collection_type):
            raise ValidationError(
                "{!r} is not {}".format(value, self._collection_label),
                self.name
            )

        new_value = self._collection_type()
        iterable = self.iterate(value)
        for element in iterable:
            element = self.recursive_validation(element)
            self.add_to_collection(new_value, element)
        value = new_value
        return Generic.__set__(self, instance, value)


class List(_Collection):
    _collection_type = list
    _collection_label = "a list"

    def add_to_collection(self, collection, element):
        collection.append(element)
        return collection


class Set(_Collection):
    _collection_type = set
    _collection_label = "a set"

    def add_to_collection(self, collection, element):
        collection.add(element)
        return collection


class Dict(_Collection):
    _collection_type = dict
    _collection_label = "a dict"

    def __init__(self, default=dict, key=None, value=None, validator=None, mutator=None):
        _Collection.__init__(
            self, default=default, value=value, validator=validator, mutator=mutator
        )
        if key is not None and not isinstance(key, Generic):
            raise TypeError('key must be None or an instance of Generic')
        self.key = key

    @staticmethod
    def iterate(collection):
        return six.iteritems(collection)

    def recursive_validation(self, element):
        """Validate element of collection against `self.value`."""
        dummy = Object()
        key, value = element
        if self.key is not None:
            try:
                key = self.key.__set__(dummy, key)
            except ValidationError as ex:
                raise ValidationError(
                    ex.msg,
                    "{} key {}".format(self.name, key)
                )
        if self.value is not None:
            try:
                value = self.value.__set__(dummy, value)
            except ValidationError as ex:
                raise ValidationError(
                    ex.msg,
                    "{}['{}']".format(self.name, key)
                )
        return key, value

    def add_to_collection(self, collection, element):
        key, value = element
        collection[key] = value
        return collection


def descriptors():
    """Generate list of descriptor class names."""
    return [
        name for name, value in six.iteritems(globals())
        if is_descriptor(value) and issubclass(value, Generic)
    ]


def descriptor_classes():
    """Generate list of descriptor classes."""
    return [
        value for value in six.itervalues(globals())
        if is_descriptor(value) and issubclass(value, Generic)
    ]

__all__ = ['descriptor_classes'] + descriptors()

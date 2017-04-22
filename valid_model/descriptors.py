import warnings
from datetime import datetime, timedelta

import six

from .base import Generic, Object
from .exc import ValidationError
from .utils import is_descriptor


class EmbeddedObject(Generic):
    def __init__(self, class_obj):
        self.class_obj = class_obj
        validator = lambda x: isinstance(x, class_obj)
        Generic.__init__(
            self, default=class_obj, validator=validator
        )

    def __set__(self, instance, value):
        try:
            if isinstance(value, dict):
                value = self.class_obj(**value)
            return Generic.__set__(self, instance, value)
        except ValidationError as ex:
            raise ValidationError(ex.msg, '{}.{}'.format(self.name, ex.field) if ex.field else self.name)


class String(Generic):
    """
    This descriptor will convert any set value to a python unicode string before
    being mutated and validated.  If the value is type(str) it will be decoded
    using utf-8
    """
    def __init__(self, default=None, validator=None, mutator=None, nullable=True):
        Generic.__init__(
            self, default=default, validator=validator, mutator=mutator, nullable=nullable
        )

    def __set__(self, instance, value):
        if value is None or isinstance(value, six.text_type):
            pass
        elif isinstance(value, six.binary_type):
            value = value.decode('utf-8')
        else:
            raise ValidationError("{!r} is not a string".format(value), self.name)
        return Generic.__set__(self, instance, value)


class Integer(Generic):
    """
    This descriptor will convert any set value to an int before being mutated and
    validated.
    """
    def __init__(self, default=None, validator=None, mutator=None, nullable=True):
        Generic.__init__(
            self, default=default, validator=validator, mutator=mutator, nullable=nullable
        )

    def __set__(self, instance, value):
        if value is not None:
            if not isinstance(value, (six.integer_types, float)) or isinstance(value, bool):
                raise ValidationError("{!r} is not an int".format(value), self.name)
            else:
                value = int(value)
        return Generic.__set__(self, instance, value)


class Float(Generic):
    """
    This descriptor will convert any set value to a float before being mutated
    and validated.
    """
    def __init__(self, default=None, validator=None, mutator=None, nullable=True):
        Generic.__init__(
            self, default=default, validator=validator, mutator=mutator, nullable=nullable
        )

    def __set__(self, instance, value):
        if value is not None:
            if not isinstance(value, (six.integer_types, float)) or isinstance(value, bool):
                raise ValidationError("{!r} is not a float".format(value), self.name)
            else:
                value = float(value)
        return Generic.__set__(self, instance, value)


class Bool(Generic):
    """
    This descriptor will convert any set value to a bool before being mutated
    and validated.
    """
    def __init__(self, default=None, validator=None, mutator=None, nullable=True):
        Generic.__init__(
            self, default=default, validator=validator, mutator=mutator, nullable=nullable
        )

    def __set__(self, instance, value):
        if value is not None:
            if value in (0, 1) or isinstance(value, bool):
                value = bool(value)
            else:
                raise ValidationError("{!r} is not a bool".format(value), self.name)
        return Generic.__set__(self, instance, value)


class DateTime(Generic):
    """
    This descriptor will assert any set value is a datetime or None before being
    mutated and validated.
    """
    def __init__(self, default=None, validator=None, mutator=None, nullable=True):
        Generic.__init__(
            self, default=default, validator=validator, mutator=mutator, nullable=nullable
        )

    def __set__(self, instance, value):
        if value is not None and not isinstance(value, datetime):
            raise ValidationError("{!r} is not a datetime".format(value), self.name)
        return Generic.__set__(self, instance, value)


class TimeDelta(Generic):
    """
    This descriptor will assert any set value is a timedelta or None before
    being mutated and validated.
    """
    def __init__(self, default=None, validator=None, mutator=None, nullable=True):
        Generic.__init__(
            self, default=default, validator=validator, mutator=mutator, nullable=nullable
        )

    def __set__(self, instance, value):
        if value is not None and not isinstance(value, timedelta):
            raise ValidationError("{!r} is not a timedelta".format(value), self.name)
        return Generic.__set__(self, instance, value)


class List(Generic):
    def __init__(self, default=list, value=None, validator=None, mutator=None):
        Generic.__init__(
            self, default=default, validator=validator, mutator=mutator, nullable=False
        )
        if value is not None and not isinstance(value, Generic):
            raise TypeError('value must be None or an instance of Generic')
        self.value = value

    def __set__(self, instance, value):
        if value is None:
            value = []
        elif not isinstance(value, list):
            raise ValidationError("{!r} is not a list".format(value), self.name)

        if self.value is not None:
            new_value = list()
            dummy = Object()
            for v in value:
                try:
                    v = self.value.__set__(dummy, v)
                except ValidationError as ex:
                    raise ValidationError(ex.msg, '{}.{}'.format(self.name, ex.field) if ex.field else self.name)
                new_value.append(v)
            value = new_value
        return Generic.__set__(self, instance, value)


class Set(Generic):
    def __init__(self, default=set, value=None, validator=None, mutator=None):
        Generic.__init__(
            self, default=default, validator=validator, mutator=mutator, nullable=False
        )
        if value is not None and not isinstance(value, Generic):
            raise TypeError('value must be None or an instance of Generic')
        self.value = value

    def __set__(self, instance, value):
        if value is None:
            value = set()
        elif not isinstance(value, set):
            raise ValidationError("{!r} is not a set".format(value), self.name)
        if self.value is not None:
            new_value = set()
            dummy = Object()
            for v in value:
                try:
                    v = self.value.__set__(dummy, v)
                except ValidationError as ex:
                    raise ValidationError(ex.msg, '{}.{}'.format(self.name, ex.field) if ex.field else self.name)
                new_value.add(v)
            value = new_value
        return Generic.__set__(self, instance, value)


class Dict(Generic):
    def __init__(self, default=dict, key=None, value=None, validator=None, mutator=None):
        Generic.__init__(
            self, default=default, validator=validator, mutator=mutator, nullable=False
        )
        if key is not None and not isinstance(key, Generic):
            raise TypeError('key must be None or an instance of Generic')
        self.key = key
        if value is not None and not isinstance(value, Generic):
            raise TypeError('value must be None or an instance of Generic')
        self.value = value

    def __set__(self, instance, value):
        if value is None:
            value = {}
        elif not isinstance(value, dict):
            raise ValidationError("{!r} is not a dict".format(value), self.name)
        new_value = {}
        dummy = Object()
        for k, v in six.iteritems(value):
            if self.key is not None:
                try:
                    k = self.key.__set__(dummy, k)
                except ValidationError as ex:
                    raise ValidationError(ex.msg, "{} key {}".format(self.name, k))
            if self.value is not None:
                try:
                    v = self.value.__set__(dummy, v)
                except ValidationError as ex:
                    raise ValidationError(ex.msg, "{}['{}']".format(self.name, k))
            new_value[k] = v
        return Generic.__set__(self, instance, new_value)


def descriptors():
    return [
        name for name, value in six.iteritems(globals())
        if is_descriptor(value) and issubclass(value, Generic)
    ]


def descriptor_classes():
    return [
        value for value in six.itervalues(globals())
        if is_descriptor(value) and issubclass(value, Generic)
    ]

__all__ = ['descriptor_classes'] + descriptors()

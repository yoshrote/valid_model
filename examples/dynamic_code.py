"""
Generate classes from a specification and generate the class declaration code
"""
import re
import inspect
from datetime import datetime, timedelta

import rfc3987
from strict_rfc3339 import validate_rfc3339
from validate_email import validate_email

from valid_model.base import Object, ObjectMeta
from valid_model.descriptors import (
    String, Integer, Bool, Dict, List, TimeDelta, DateTime, Set, EmbededObject, Float, Generic
)

class ObjectPrinter(object):
    @classmethod
    def attr_definition(cls, descriptor):
        valid_attributes = {'default', 'validator', 'mutator', 'nullable', 'key', 'value', 'class_obj'}
        full_code = []
        for name, value in inspect.getmembers(descriptor):
            if name not in valid_attributes:
                continue
            # print repr((name, value))
            if name in ('mutator', 'validator'):
                print_val = cls.func_str(name, value)
            elif name in ('key', 'value'):
                print_val = '{}()'.format(value.__class__.__name__)
            elif name == 'default':
                print_val = cls.func_str(name, value) if callable(value) and not isinstance(value, type) else cls.static_str(value)
            else:
                print_val = cls.static_str(value)
            full_code.append('\t\t{} = {},'.format(name, print_val))
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
            return print_val.__name__
        idx = print_val.find(name)
        print_val = print_val[idx:].split(',')[0]
        print_val = ''.join(print_val.split('=')[1:]).strip()
        print_val = print_val[:-1] if print_val.endswith(',') else print_val
        print_val = print_val[:-1] if print_val.endswith(')') else print_val
        print_val = print_val.strip()
        return print_val

    @classmethod
    def print_class(cls, klass):
        assert issubclass(klass, Object)
        print 'class {}(Object):'.format(klass.__name__)
        for attr_name, descriptor in inspect.getmembers(klass, lambda x: isinstance(x, Generic)):
            print '\t{} = {}(\n{}\n\t)'.format(attr_name, descriptor.__class__.__name__, cls.attr_definition(descriptor))
        print ''

def print_class(klass):
    return ObjectPrinter.print_class(klass)


class JSONBase(object):
    def __init__(self, name=None, description=None, **kwargs):
        self.name = name
        self.description = description
        super(JSONBase, self).__init__()

    def __call__(self, value):
        return self.validate()

    def validate(self):
        raise NotImplementedError('validate')

    def __repr__(self):
        return u'{}({})'.format(
            self.__class__.__name,
            u', '.join(
                u'{}={}'.format(k.ltrim('_'), repr(v))
                for k, v in vars(self)
                if not callable(v) and k.startswith('_')
            )
        )

class JSONNumber(JSONBase):
    def __init__(self, multipleOf=None, maximum=None, exclusiveMaximum=None, enum=None, **kwargs)
        self._multipleOf = multipleOf
        self._maximum = maximum
        self._exclusiveMaximum = exclusiveMaximum
        self._enum = enum
        super(JSONNumber, self).__init__(**kwargs)

    def enum(self, value):
        if self._enum is not None:
            return value in self._enum
        else:
            return True

    def validate(self, value):
        return all(
            self.multipleOf(value),
            self.maximum(value),
            self.minimum(value),
            self.enum(value),
        )

    def multipleOf(self, value):
        if self._multipleOf is not None:
            return value % self._multipleOf == 0
        else:
            return True

    def maximum(self, value):
        if self._maximum is not None:
            if self._exclusive_maximum:
                return value < self._maximum
            else:
                return value <= self._maximum
        else:
            return True

    def minimum(self, value):
        if self._minimum is not None:
            if self._exclusive_minimum:
                return value > self._minimum
            else:
                return value >= self._minimum
        else:
            return True

class JSONString(JSONBase):
    FORMATS = {
        'date-time': lambda x: validate_rfc3339(x),
        'email': lambda x: validate_email(x),
        'hostname': lambda x: rfc3987.match(x, 'host') is not None
        'ipv4': lambda x: rfc3987.match(x, 'IPv4address') is not None
        'ipv6': lambda x: rfc3987.match(x, 'IPv6address') is not None
        'uri': lambda x: rfc3987.match(x, 'URI') is not None
        'uriref': lambda x: rfc3987.match(x, 'URI_reference') is not None
    }

    def __init__(self, default=None, maxLength=None, minLength=None, pattern=None, format_=None, enum=None, **kwargs):
        self._maxLength = maxLength
        self._minLength = minLength
        self._pattern = re.compile(pattern)
        self._format = format_
        self._enum = enum
        super(JSONString, self).__init__(**kwargs)

    def validate(self, value):
        return all(
            self.maxLength(value),
            self.minLength(value).
            self.pattern(value),
            self.format(value),
            self.enum(value),
        )

    def enum(self, value):
        if self._enum is not None:
            return value in self._enum
        else:
            return True

    def maxLength(self, value):
        if self._maxLength is not None:
            return len(value) <= self._maxLength
        else:
            return True

    def minLength(self, value):
        if self._minLength is not None:
            return len(value) >= self._minLength
        else:
            return True

    def pattern(self, value):
        if self._pattern is not None:
            return self._pattern.search(value) is not None
        else:
            return True

    def format(self, value):
        if self._format is not None:
            return self.FORMATS[self._format](value)
        else:
            return True

class JSONArray(JSONBase):
    def __init__(self, default=None, maxItems=None, minItems=None, uniqueItems=None, allOf=None, anyOf=None, oneOf=None, **kwargs):
        self._maxItems = maxItems
        self._minItems = minItems
        self._uniqueItems = uniqueItems
        self._allOf = allOf
        self._anyOf = anyOf
        self._oneOf = oneOf
        super(JSONArray, self).__init__(**kwargs)

    def _undefined_properties(self, value):
        keys = set(value.keys())
        keys = keys - set(self._properties or [])
        if self._patternProperties:
            for pattern in self._patternProperties:
                if self._pattern_matches(pattern, value):
                    keys.remove(key)
        return keys

    def validate(self, value):
        return all(
            self.maxItems(value),
            self.minItems(value),
            self.uniqueItems(value),
            self.allOf(value),
            self.anyOf(value),
            self.oneOf(value),
            self.items(value),
        )

    def items(self, value)
        """
        items and additionalItems
        MUST be a valid JSON Schema.
        The value of "items" MUST be either a schema or array of schemas.
        Successful validation of an array instance with regards to these two keywords is determined as follows:
        if "items" is not present, or its value is an object, validation of the instance always succeeds, regardless of the value of "additionalItems";
        if the value of "additionalItems" is boolean value true or an object, validation of the instance always succeeds;
        if the value of "additionalItems" is boolean value false and the value of "items" is an array, the instance is valid if its size is less than, or equal to, the size of "items".
        If either keyword is absent, it may be considered present with an empty schema.
        """
        if self._items is None:
            return True

        if isinstance(self._items, list):
            if len(value) < len(self._items):
                return False
            for item, value_piece in zip(self._items):
                if not item.validate(value_piece):
                    return False
        elif self._items:
            for value_piece in value:
                if not self._items.validate(value_piece):
                    return False

        if self._additionalItems is False and isinstance(self._items, list) and len(self._items) != len(value):
            return False
        elif not isinstance(self._items, list) and self._additionalItems is False:
            raise ValueError('schema should not have an object for items')

        return True

    def maxItems(self, value):
        if self._maxItems is not None:
            return len(value) <= self._maxItems
        else:
            return True

    def minItems(self, value):
        if self._minItems is not None:
            return len(value) >= self._minItems
        else:
            return True

    def uniqueItems(self, value):
        if self._uniqueItems is not None:
            return len(value) == len(set(value))
        else:
            return True

    def allOf(self, value):
        if self._allOf is not None:
            try:
                for v in value:
                    self._allOf.__set__(Object(), v)
            except ValidationError:
                return False
            else:
                return True
        else:
            return True

    def anyOf(self, value):
        if self._anyOf is not None:
            for v in value:
                try:
                    self._anyOf.__set__(Object(), v)
                except ValidationError:
                    pass
                else:
                    return True
            return False
        else:
            return True

    def oneOf(self, value):
        if self._oneOf is not None:
            counter = 0
            for v in value:
                try:
                    self._oneOf.__set__(Object(), v)
                except ValidationError:
                    pass
                else:
                    counter += 1
            return counter == 1
        else:
            return True

class JSONObject(JSONBase):
    def __init__(self, required=None, properties=None, patternProperties=None, additionalProperties=None, **kwargs):
        self._properties = properties
        self._patternProperties
        self._additionalProperties = additionalProperties
        self._required = required
        super(JSONObject, self).__init__(**kwargs)

    def __call__(self, value):
        if self._additionalProperties is not None:
            if self._additionalProperties is True:
                return True

            undefined_properties = self._undefined_properties(value)
            if self._additionalProperties is False:
                return not undefined_properties
            elif not all(self._additionalProperties.validate(getattr(value, property_)) for property_ in undefined_properties):
                return False

        return self.validate(value)

    def _undefined_properties(self, value):
        keys = set(value.keys())
        keys = keys - set(self._properties or [])
        if self._patternProperties:
            for pattern in self._patternProperties:
                if self._pattern_matches(pattern, value):
                    keys.remove(key)
        return keys

    def _pattern_matches(self, pattern, value):
        matches = []
        for key in value.keys():
            if re.search(pattern, key) is not None:
                matches.append(key)
        return matches

    def validate(self, value):
        return all(
            self.required(value),
            self.maxProperties(value),
            self.minProperties(value),
            self.properties(value),
            self.patternProperties(value),
        )

    def properties(self, value):
        if self._properties is not None:
            for key, rule in self._properties.items()
                rule.validate(getattr(value, key))

    def patternProperties(self, value):
        if self._patternProperties is not None:
            for pattern, rule in self._patternProperties.items():
                for key in self._pattern_matches(pattern, value):
                    if not rule.validate(value):
                        return False

        return True

    def maxProperties(self, value):
        if self._maxProperties is not None:
            return len(value) <= self._maxProperties
        else:
            return True

    def minProperties(self, value):
        if self._minProperties is not None:
            return len(value) >= self._minProperties
        else:
            return True

    def required(self, value):
        if self._required is not None:
            return all(hasattr(value, req_key) for req_key in self._required)
        else:
            return True

'''
5.19. dependencies
    This keyword specifies rules that are evaluated if the instance is an object and contains a certain property.
    This keyword's value MUST be an object. Each property specifies a dependency. Each dependency value MUST be an object or an array.
    If the dependency value is an object, it MUST be a valid JSON Schema. If the dependency key is a property in the instance, the dependency value must validate against the entire instance.
    If the dependency value is an array, it MUST have at least one element, each element MUST be a string, and elements in the array MUST be unique. If the dependency key is a property in the instance, each of the items in the dependency value must be a property that exists in the instance.

5.25. not
    This keyword's value MUST be an object. This object MUST be a valid JSON Schema.
    An instance is valid against this keyword if it fails to validate successfully against the schema defined by this keyword.

5.26. definitions
    This keyword's value MUST be an object. Each member value of this object MUST be a valid JSON Schema.
    This keyword plays no role in validation per se. Its role is to provide a standardized location for schema authors to inline JSON Schemas into a more general schema.

dependencies
not
definitions
title
description
'''

class ObjectMaker(object):
    KLASS_MAP = {
        'string': String,
        'integer': Integer,
        'boolean': Bool,
        'datetime': DateTime,
        'timedelta': TimeDelta,
        'map': Dict,
        'list': List,
        'array': List,
        'set': Set,
    }
    DEFAULT_MAP = {
        'string': unicode,
        'integer': int,
        'boolean': lambda x: eval(x.lower()), # TODO: This is bad
        'datetime': lambda x: datetime.strptime(x, '%Y-%m-%dT%H:%M:%S'),
        'timedelta': lambda x: timedelta(seconds=float(x)),
        'map': lambda x: x,
        'list': lambda x: x,
        'set': lambda x: x,
    }
    JSON_SCHEME_MAP = {
        'boolean': Bool,
        'array': List,
        'object': Dict,
        'number': Float,
        'string': String,
    }
    JSON_VALIDATORS = {
        'array': JSONArray,
        'string': JSONString,
        'number': JSONNumber,
        'object': JSONObject,
    }
    def __init__(self, schema_fetcher, registry=None):
        self.registry = registry or {}
        self.schema_fetcher = schema_fetcher

    def get_class(self, name):
        try:
            klass = self.registry[name]
        except KeyError:
            schema = self.schema_fetcher.get(name)
            if not schema:
                raise RuntimeError('could not fetch schema for {!r}'.format(name))
            klass = self.registry[name] = self.create_class_from_json_schema(name, schema)
        return klass

    @classmethod
    def create_class_from_json_schema(cls, name, schema):
        assert schema['type'] == 'object', "Only supporting object creation"
        required_fields = set(schema.get('required', []))
        attrs = {}
        for prop_name, prop_spec in schema['properties'].iteritems():
            attrs[prop_name] = cls.descriptor_from_schema(prop_spec, required=prop_name in required_fields)
        return cls.create_class(name, attrs)

    @classmethod
    def descriptor_from_schema(cls, spec, required=False):
        klass = cls.JSON_SCHEME_MAP[spec['type']]
        klass_kwargs = {'default':spec.get('default'), 'nullable':not required}
        if spec['type'] in cls.JSON_VALIDATORS:
            klass_kwargs['validator'] = cls.JSON_VALIDATORS[spec['type']](**spec)
        return klass(**klass_kwargs)

    @staticmethod
    def create_class(name, attrs):
        return ObjectMeta.__new__(ObjectMeta, name, (Object,), dict(attrs))

    @classmethod
    def descriptor_from_spec(cls, spec):
        klass = cls.KLASS_MAP[spec['type']]
        default = cls.DEFAULT_MAP[spec['type']](spec['default']) if spec.get('default') else None
        if spec.get('required'):
            nullable = bool(spec.get('required'))
            return klass(default=default, nullable=nullable)
        else:
            return klass(default=default)

    @classmethod
    def create_class_from_spec(cls, name, spec):
        attrs = {}
        for k, v in spec.iteritems():
            attrs[k] = cls.descriptor_from_spec(v)
        return cls.create_class(name, attrs)

def create_class(name, attrs):
    return ObjectMaker.create_class(name, attrs)

def create_class_from_spec(name, spec):
    return ObjectMaker.create_class_from_spec(name, spec)

def main():
    foo_attrs = {
        'a': String(validator=lambda x: len(x) < 5, mutator=lambda x: x.lower()),
        'b': Integer(default=5),
        'c': Bool(nullable=True),
        'd': List(value=String()),
        'e': Dict(key=String(), value=Integer())
    }
    Foo = create_class('Foo', foo_attrs)
    print_class(Foo)

    bar_attrs = {
        'a': {'type': 'string', 'required': True},
        'b': {'type': 'integer', 'default': 5},
        'c': {'type': 'boolean'},
        'd': {'type': 'datetime', 'default': '1970-01-01T00:00:00'},
        'e': {'type': 'list', 'value': {'type': 'integer', 'required': True}}
    }
    Bar = create_class_from_spec('Bar', bar_attrs)
    print_class(Bar)

if __name__ == '__main__':
    main()

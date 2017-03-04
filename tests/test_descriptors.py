import unittest


class TestEmbeddedObject(unittest.TestCase):
    @staticmethod
    def _make_one():
        from valid_model.descriptors import EmbeddedObject
        from valid_model import Object

        class Foo(Object):
            test = EmbeddedObject(Object)
        return Foo()

    def test___delete__(self):
        instance = self._make_one()
        del instance.test
        self.assertEquals(instance.test, None)


class TestObjectList(unittest.TestCase):
    @staticmethod
    def _make_one(mutator=None):
        from valid_model.descriptors import List, EmbeddedObject
        from valid_model import Object

        class Foo(Object):
            test = List(value=EmbeddedObject(Object), mutator=mutator)
        return Foo()

    def test___set___validator(self):
        from valid_model import ValidationError
        instance = self._make_one()
        self.assertRaises(ValidationError, setattr, instance, 'test', 10)
        self.assertRaises(ValidationError, setattr, instance, 'test', [10])

    def test___delete__(self):
        instance = self._make_one()
        del instance.test
        self.assertEquals(instance.test, None)


class TestObjectDict(unittest.TestCase):
    @staticmethod
    def _make_one(mutator=None):
        from valid_model.descriptors import EmbeddedObject, Dict
        from valid_model import Object

        class Foo(Object):
            test = Dict(value=EmbeddedObject(Object), mutator=mutator)
        return Foo()

    @staticmethod
    def _make_two(mutator=None):
        from valid_model.descriptors import Dict, Integer
        from valid_model import Object

        class Foo(Object):
            test = Dict(key=Integer(validator=lambda x: x > 5), mutator=mutator)
        return Foo()

    def test___set___validator(self):
        from valid_model import ValidationError
        instance = self._make_one()
        nested_instance = self._make_one()
        self.assertRaises(ValidationError, setattr, instance, 'test', 10)
        self.assertRaises(ValidationError, setattr, instance, 'test', {'foo': 10})
        instance.test = {'foo': nested_instance}

        instance2 = self._make_two()
        self.assertRaises(ValidationError, setattr, instance2, 'test', 10)
        self.assertRaises(ValidationError, setattr, instance2, 'test', {'abc': 10})
        self.assertRaises(ValidationError, setattr, instance2, 'test', {2: 10})
        instance2.test[8] = 5

    def test___delete__(self):
        instance = self._make_one()
        del instance.test
        self.assertEquals(instance.test, None)


class TestOldObjectList(unittest.TestCase):
    @staticmethod
    def _make_one(mutator=None):
        from valid_model.descriptors import ObjectList
        from valid_model import Object

        class Foo(Object):
            test = ObjectList(Object)
        return Foo()

    def test___set___validator(self):
        from valid_model import ValidationError
        instance = self._make_one()
        self.assertRaises(ValidationError, setattr, instance, 'test', 10)
        self.assertRaises(ValidationError, setattr, instance, 'test', [10])

    def test___delete__(self):
        instance = self._make_one()
        del instance.test
        self.assertEquals(instance.test, None)


class TestOldObjectDict(unittest.TestCase):
    @staticmethod
    def _make_one(mutator=None):
        from valid_model.descriptors import ObjectDict
        from valid_model import Object

        class Foo(Object):
            test = ObjectDict(Object)
        return Foo()

    def test___set___validator(self):
        from valid_model import ValidationError
        instance = self._make_one()
        nested_instance = self._make_one()
        self.assertRaises(ValidationError, setattr, instance, 'test', 10)
        self.assertRaises(ValidationError, setattr, instance, 'test', {'foo': 10})
        instance.test = {'foo': nested_instance}

    def test___delete__(self):
        instance = self._make_one()
        del instance.test
        self.assertEquals(instance.test, None)


class TestString(unittest.TestCase):
    @staticmethod
    def _make_one(default=None, validator=None, mutator=None):
        from valid_model.descriptors import String
        from valid_model import Object

        class Foo(Object):
            test = String(default=default, validator=validator, mutator=mutator)
        return Foo()

    def test___set___validator(self):
        from valid_model import ValidationError
        instance = self._make_one()
        instance.test = u'hello'
        instance.test = 'hello'
        self.assertTrue(isinstance(instance.test, unicode))
        self.assertRaises(ValidationError, setattr, instance, 'test', 10)


class TestInteger(unittest.TestCase):
    @staticmethod
    def _make_one(default=None, validator=None, mutator=None):
        from valid_model.descriptors import Integer
        from valid_model import Object

        class Foo(Object):
            test = Integer(
                default=default, validator=validator, mutator=mutator
            )
        return Foo()

    def test___set___validator(self):
        from valid_model import ValidationError
        instance = self._make_one()
        instance.test = 5
        self.assertEquals(instance.test, 5)
        instance.test = 3.5
        self.assertEquals(instance.test, 3)
        instance.test = None
        self.assertEquals(instance.test, None)
        self.assertRaises(ValidationError, setattr, instance, 'test', True)
        self.assertRaises(ValidationError, setattr, instance, 'test', 'hello')
        self.assertRaises(ValidationError, setattr, instance, 'test', '15')


class TestFloat(unittest.TestCase):
    @staticmethod
    def _make_one(default=None, validator=None, mutator=None):
        from valid_model.descriptors import Float
        from valid_model import Object

        class Foo(Object):
            test = Float(default=default, validator=validator, mutator=mutator)
        return Foo()

    def test___set___validator(self):
        from valid_model import ValidationError
        instance = self._make_one()
        instance.test = 5.0
        self.assertEquals(instance.test, 5.0)
        instance.test = 10
        self.assertEquals(instance.test, 10.0)
        instance.test = None
        self.assertEquals(instance.test, None)
        self.assertRaises(ValidationError, setattr, instance, 'test', True)
        self.assertRaises(ValidationError, setattr, instance, 'test', 'hello')
        self.assertRaises(ValidationError, setattr, instance, 'test', '15')


class TestBool(unittest.TestCase):
    @staticmethod
    def _make_one(default=None, validator=None, mutator=None):
        from valid_model.descriptors import Bool
        from valid_model import Object

        class Foo(Object):
            test = Bool(default=default, validator=validator, mutator=mutator)
        return Foo()

    def test___set___validator(self):
        from valid_model import ValidationError
        instance = self._make_one()
        self.assertEquals(instance.test, None)
        instance.test = True
        self.assertEquals(instance.test, True)
        instance.test = False
        self.assertEquals(instance.test, False)
        instance.test = None
        self.assertEquals(instance.test, None)
        instance.test = 0
        self.assertIs(instance.test, False)
        instance.test = 1
        self.assertIs(instance.test, True)
        instance = self._make_one()
        self.assertRaises(ValidationError, setattr, instance, 'test', object())


class TestDateTime(unittest.TestCase):
    @staticmethod
    def _make_one(default=None, validator=None, mutator=None):
        from valid_model.descriptors import DateTime
        from valid_model import Object

        class Foo(Object):
            test = DateTime(
                default=default, validator=validator, mutator=mutator
            )
        return Foo()

    def test___set___validator(self):
        from valid_model import ValidationError
        from datetime import datetime
        instance = self._make_one()
        today = datetime.utcnow()
        instance.test = today
        self.assertEquals(instance.test, today)
        self.assertRaises(ValidationError, setattr, instance, 'test', 10)


class TestTimeDelta(unittest.TestCase):
    @staticmethod
    def _make_one(default=None, validator=None, mutator=None):
        from valid_model.descriptors import TimeDelta
        from valid_model import Object

        class Foo(Object):
            test = TimeDelta(
                default=default, validator=validator, mutator=mutator
            )
        return Foo()

    def test___set___validator(self):
        from valid_model import ValidationError
        from datetime import timedelta
        instance = self._make_one()
        one_minute = timedelta(minutes=1)
        instance.test = one_minute
        self.assertEquals(instance.test, one_minute)
        self.assertRaises(ValidationError, setattr, instance, 'test', 10)


class TestList(unittest.TestCase):
    @staticmethod
    def _make_one(validator=None, mutator=None, value=None):
        from valid_model.descriptors import List
        from valid_model import Object

        class Foo(Object):
            test = List(value=value, validator=validator, mutator=mutator)
        return Foo()

    def test___set___validator(self):
        from valid_model import ValidationError
        instance = self._make_one()
        instance.test = [True, 10]
        self.assertRaises(ValidationError, setattr, instance, 'test', 10)

    def test_invalid_descriptor(self):
        self.assertRaises(TypeError, self._make_one, value=5)

    def test_none(self):
        instance = self._make_one()
        instance.test = None
        self.assertEquals(instance.test, [])


class TestSet(unittest.TestCase):
    @staticmethod
    def _make_one(validator=None, mutator=None, value=None):
        from valid_model.descriptors import Set
        from valid_model import Object

        class Foo(Object):
            test = Set(value=value, validator=validator, mutator=mutator)
        return Foo()

    def test___set___validator(self):
        from valid_model import ValidationError
        instance = self._make_one()
        instance.test = set([True, 10])
        self.assertRaises(ValidationError, setattr, instance, 'test', 10)

    def test___delete__(self):
        instance = self._make_one()
        del instance.test
        self.assertEquals(instance.test, None)

    def test_invalid_descriptor(self):
        self.assertRaises(TypeError, self._make_one, value=5)

    def test_descriptor(self):
        from valid_model import ValidationError
        from valid_model.descriptors import Integer
        instance = self._make_one(value=Integer())
        self.assertRaises(ValidationError, setattr, instance, 'test', set(['f', 'o', 'o']))
        instance.test = {1, 2, 3}

    def test_none(self):
        instance = self._make_one()
        instance.test = None
        self.assertEquals(instance.test, set())


class TestDict(unittest.TestCase):
    @staticmethod
    def _make_one(default=dict, validator=None, mutator=None, value=None, key=None):
        from valid_model.descriptors import Dict
        from valid_model import Object

        class Foo(Object):
            test = Dict(
                default=default, validator=validator, mutator=mutator, key=key, value=value
            )
        return Foo()

    def test___set___validator(self):
        from valid_model import ValidationError
        instance = self._make_one()
        instance.test = {'a': 1, 'b': 2}
        self.assertRaises(ValidationError, setattr, instance, 'test', 10)

    def test_invalid_descriptor(self):
        self.assertRaises(TypeError, self._make_one, value=5)
        self.assertRaises(TypeError, self._make_one, key=5)

    def test_none(self):
        instance = self._make_one()
        instance.test = None
        self.assertEquals(instance.test, {})


if __name__ == '__main__':
    unittest.main()

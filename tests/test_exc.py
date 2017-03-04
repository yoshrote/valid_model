import unittest


class TestValidationError(unittest.TestCase):
    def _make_one(self, msg, field=None):
        from valid_model import ValidationError
        return ValidationError(msg, field=field)

    def test___str__(self):
        self.assertEquals(str(self._make_one('foo')), 'foo')
        self.assertEquals(str(self._make_one('foo', 'bar')), 'bar: foo')

    def test___unicode__(self):
        self.assertEquals(unicode(self._make_one('foo')), u'foo')
        self.assertEquals(unicode(self._make_one('foo', 'bar')), u'bar: foo')

    def test___repr__(self):
        self.assertEquals(repr(self._make_one('foo')), "ValidationError('foo', None)")
        self.assertEquals(repr(self._make_one('foo', 'bar')), "ValidationError('foo', 'bar')")


if __name__ == '__main__':
    unittest.main()

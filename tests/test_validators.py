import unittest


class TestValidators(unittest.TestCase):
    def test_truthy(self):
        from valid_model.validators import truthy
        self.assertTrue(truthy(True))
        self.assertFalse(truthy(False))

    def test_falsey(self):
        from valid_model.validators import falsey
        self.assertFalse(falsey(True))
        self.assertTrue(falsey(False))

    def test_identity(self):
        from valid_model.validators import identity
        self.assertTrue(identity(True)(True))
        self.assertTrue(identity(None)(None))
        self.assertFalse(identity(True)(False))

    def test_not_identity(self):
        from valid_model.validators import not_identity
        self.assertFalse(not_identity(True)(True))
        self.assertFalse(not_identity(None)(None))
        self.assertTrue(not_identity(True)(False))

    def test_is_instance(self):
        from valid_model.validators import is_instance
        self.assertTrue(is_instance(int)(25))
        self.assertFalse(is_instance(float)("hello"))

    def test_equals(self):
        from valid_model.validators import equals
        self.assertTrue(equals(12)(12))
        self.assertFalse(equals(12)(13))

    def test_not_equals(self):
        from valid_model.validators import not_equals
        self.assertTrue(not_equals(12)(13))
        self.assertFalse(not_equals(12)(12))

    def test_gt(self):
        from valid_model.validators import gt
        self.assertTrue(gt(12)(13))
        self.assertFalse(gt(12)(12))
        self.assertFalse(gt(12)(11))

    def test_gte(self):
        from valid_model.validators import gte
        self.assertTrue(gte(12)(13))
        self.assertTrue(gte(12)(12))
        self.assertFalse(gte(12)(11))

    def test_lt(self):
        from valid_model.validators import lt
        self.assertFalse(lt(12)(13))
        self.assertFalse(lt(12)(12))
        self.assertTrue(lt(12)(11))

    def test_lte(self):
        from valid_model.validators import lte
        self.assertFalse(lte(12)(13))
        self.assertTrue(lte(12)(12))
        self.assertTrue(lte(12)(11))

    def test_contains(self):
        from valid_model.validators import contains
        self.assertTrue(contains(12)([12, 13]))
        self.assertFalse(contains(11)([12, 13]))

    def test_not_contains(self):
        from valid_model.validators import not_contains
        self.assertFalse(not_contains(12)([12, 13]))
        self.assertTrue(not_contains(11)([12, 13]))

    def test_is_in(self):
        from valid_model.validators import is_in
        self.assertTrue(is_in([12, 13])(12))
        self.assertFalse(is_in([12, 13])(11))

    def test_is_not_in(self):
        from valid_model.validators import is_not_in
        self.assertFalse(is_not_in([12, 13])(12))
        self.assertTrue(is_not_in([12, 13])(11))

    def test_any_of(self):
        from valid_model.validators import any_of, lt, gte
        v = any_of([lt(5), gte(12)])
        self.assertTrue(v(2))
        self.assertTrue(v(15))
        self.assertFalse(v(10))

    def test_compound(self):
        from valid_model.validators import all_of, any_of, lt, gte, is_instance
        range_validator = any_of([lt(5), gte(12)])
        v = all_of([is_instance(int), range_validator])
        self.assertTrue(v(2))
        self.assertTrue(v(150))
        self.assertFalse(v(10))
        self.assertFalse(v("hello"))

if __name__ == '__main__':
    unittest.main()

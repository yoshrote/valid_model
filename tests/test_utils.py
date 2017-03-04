import unittest


class TestDescriptorFuncs(unittest.TestCase):
    def test_descriptor_finders(self):
        from valid_model.descriptors import descriptor_classes, descriptors
        descriptors_list = descriptors()
        descriptor_cls_list = descriptor_classes()
        for cls in descriptor_cls_list:
            self.assert_(cls.__name__ in descriptors_list)
            descriptors_list.remove(cls.__name__)
        self.assertEquals(len(descriptors_list), 0)


class TestObjectPrinter(unittest.TestCase):
    def make_class(self):
        import datetime

        from valid_model import Object, descriptors as desc

        class AwesomeModel(Object):
            simple = desc.Bool()
            def_scalar = desc.Integer(default=5)
            def_func = desc.Integer(default=lambda: 5 * 1)
            mutatable = desc.String(mutator=lambda x: x.lower())
            dict_attr = desc.Dict(
                key=desc.String(nullable=False),
                value=desc.DateTime(default=datetime.datetime.utcnow)
            )

        return AwesomeModel

    def test_format_class(self):
        from valid_model.utils import ObjectPrinter

        class_output = """class AwesomeModel(Object):
    def_func = Integer(
        default = lambda: 5 * 1,
        mutator = lambda x: x,
        nullable = True,
        validator = lambda x: True,
    )
    def_scalar = Integer(
        default = 5,
        mutator = lambda x: x,
        nullable = True,
        validator = lambda x: True,
    )
    dict_attr = Dict(
        default = dict,
        key = String(
            default = None,
            mutator = lambda x: x,
            nullable = False,
            validator = lambda x: True,),
        mutator = lambda x: x,
        nullable = False,
        validator = lambda x: True,
        value = DateTime(
            default = utcnow,
            mutator = lambda x: x,
            nullable = True,
            validator = lambda x: True,),
    )
    mutatable = String(
        default = None,
        mutator = lambda x: x.lower(),
        nullable = True,
        validator = lambda x: True,
    )
    simple = Bool(
        default = None,
        mutator = lambda x: x,
        nullable = True,
        validator = lambda x: True,
    )

"""
        for line, expected in zip(ObjectPrinter.format_class(self.make_class()).splitlines(), class_output.splitlines()):
            self.assertEquals(line, expected)
        self.assertEquals(
            ObjectPrinter.format_class(self.make_class()),
            class_output
        )


if __name__ == '__main__':
    unittest.main()

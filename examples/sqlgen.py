from __future__ import unicode_literals
from valid_model.base import ObjectMeta, Object, Generic


def flatten(l):
    return [item for sublist in l for item in sublist]


class SQLBase(object):
    @staticmethod
    def expression_fragment(data):
        if isinstance(data, Generic):
            return data.extra['name']
        elif isinstance(data, SQLBase):
            return data
        else:
            return "?"

    @staticmethod
    def yield_fragment(data):
        if not isinstance(data, (SQLBase, Generic)):
            yield data
        elif isinstance(data, SQLBase):
            for value in data.values():
                yield value
        raise StopIteration()


class Select(SQLBase):
    def __init__(self, *columns):
        self._columns = list(columns)
        self._from = None
        self._where = None

    def columes(self, *columns):
        self._columns.extend(columns)
        return self

    def where(self, where):
        self._where = where
        return self

    def from_(self, from_):
        self._from = from_
        return self

    def __unicode__(self):
        seen = set()
        columns = []
        for c in self._columns:
            c_str = unicode(c if not isinstance(c, Generic) else c.extra['name'])
            for part in c_str.split(", "):
                if part not in seen:
                    columns.append(part)
                    seen.add(part)
        columns = ', '.join(columns)
        statement = """SELECT {columns} FROM {from_}""".format(
            columns=columns,
            from_=self._from)
        if self._where is not None:
            statement = "{statement} WHERE {where}".format(
                statement=statement,
                where=self._where)
        return statement

    @property
    def query(self):
        return self.__unicode__(), self.values()

    def values(self):
        return self._where.values() if self._where else []

    def __str__(self):
        return self.__unicode__().encode('utf-8')


class Where(SQLBase):

    def __init__(self, *expressions):
        self._expressions = list(expressions)

    def and_(self, expression):
        self._expressions.append('AND')
        self._expressions.append(expression)
        return self

    def or_(self, expression):
        self._expressions.append('OR')
        self._expressions.append(expression)
        return self

    def __unicode__(self):
        return " ".join(["({})".format(" ".join([unicode(e) for e in self._expressions]))])

    def __str__(self):
        return self.__unicode__().encode('utf-8')

    def values(self):
        return flatten(e.values() for e in self._expressions if not isinstance(e, basestring))


class Expression(SQLBase):
    def __init__(self, lhs=None, operation=None, rhs=None):
        self.lhs = lhs
        self.operation = operation
        self.rhs = rhs

    def __unicode__(self):
        lhs = self.expression_fragment(self.lhs)
        rhs = self.expression_fragment(self.rhs)
        return " ".join(map(unicode, (lhs, self.operation, rhs)))

    def __str__(self):
        return self.__unicode__().encode('utf-8')

    def values(self):
        for value in self.yield_fragment(self.lhs):
            yield value
        for value in self.yield_fragment(self.rhs):
            yield value
        raise StopIteration()


class UnaryExpression(SQLBase):
    def __init__(self, operation=None, rhs=None):
        self.operation = operation
        self.rhs = rhs

    def __unicode__(self):
        rhs = self.expression_fragment(self.rhs)
        return " ".join(map(unicode, (self.operation, rhs)))

    def __str__(self):
        return self.__unicode__().encode('utf-8')

    def values(self):
        for value in self.yield_fragment(self.rhs):
            yield value
        raise StopIteration()


class Function(SQLBase):
    def __init__(self, function=None, rhs=None):
        self.function = function
        self.rhs = rhs

    def __unicode__(self):
        rhs = self.expression_fragment(self.rhs)
        return "{}({})".format(self.function, rhs)

    def __str__(self):
        return self.__unicode__().encode('utf-8')

    def values(self):
        for value in self.yield_fragment(self.rhs):
            yield value
        raise StopIteration()


class From(SQLBase):
    def __init__(self, *tables):
        self._tables = list(tables)

    def join(self, table, on):
        self._tables.append("JOIN")
        self._tables.append(table)
        self._tables.append("ON")
        self._tables.append(on)
        return self

    def __unicode__(self):
        return " ".join(map(unicode, self._tables))

    def __str__(self):
        return self.__unicode__().encode('utf-8')


class SQLObjectMeta(ObjectMeta):
    @classmethod
    def hook(mcs, name, attrs, attr, value):
        attr_name = "{}.{}".format(attrs.get('__table_name__', name), attr)
        value.extra['name'] = attr_name

    def __unicode__(self):
        return ", ".join(getattr(self, f).extra['name'] for f in self.field_names)

    def __str__(self):
        return self.__unicode__().encode('utf-8')


class SQLObject(Object):
    __metaclass__ = SQLObjectMeta


def main():
    from valid_model import descriptors as desc

    class Car(SQLObject):
        __table_name__ = 'test_cars'
        model = desc.String()
        wheels = desc.Integer()

    class Manufacturer(SQLObject):
        __table_name__ = 'test_manufacturer'
        make = desc.String()
        started = desc.DateTime()

    subq = Select(
        Manufacturer.make
    ).from_(
        From('test_manufacturer')
    ).where(
        Expression(Manufacturer.started, '>=', 2020)
    )

    print Car
    print Car(model="foo", wheels=4)
    print unicode(Car.model)
    foo = Select(
        Car, Manufacturer
    ).from_(
        From('test_cars').join('test_manufacturer', Expression(Car.model, 'STARTSWITH', Manufacturer.make))
    ).where(
        Where(
            Where(
                Expression(Car.wheels, '>', 3)
            ).and_(
                Expression(Car.model, 'LIKE', '%Tesla%')
            ).and_(
                Function('EXISTS', subq)
            )
        ).or_(
            Where(
                Expression(Car.model, 'LIKE', '%Toyota%')
            ).and_(
                Expression(Car.wheels, '>', 16)
            ).and_(
                UnaryExpression('NOT', Manufacturer.make)
            )
        )
    )
    query, params = foo.query
    print query
    print params

if __name__ == '__main__':
    main()

from __future__ import unicode_literals

from collections import OrderedDict
from valid_model.base import Generic, Object, ObjectMeta


def flatten(l):
    return [item for sublist in l for item in sublist]


class SQLBase(object):
    @staticmethod
    def expression_param(data):
        if isinstance(data, Generic):
            return data.extra['name']
        elif isinstance(data, SQLBase):
            return data
        else:
            return "?"

    @staticmethod
    def expression_values(data):
        if not isinstance(data, (SQLBase, Generic)):
            yield data
        elif isinstance(data, SQLBase):
            for value in data.bound_values():
                yield value
        raise StopIteration()


class Select(SQLBase):
    def __init__(self, *columns):
        self._columns = list(columns)
        self._from = None
        self._where = None
        self._group_by = None
        self._order_by = None

    @staticmethod
    def format_columns(column_list):
        seen = set()
        columns = []
        for c in column_list:
            c_str = unicode(
                c if not isinstance(c, Generic) else c.extra['name'])
            for part in c_str.split(", "):
                if part not in seen:
                    columns.append(part)
                    seen.add(part)
        columns = ', '.join(columns)
        return columns

    def columes(self, *columns):
        self._columns.extend(columns)
        return self

    def where(self, where):
        self._where = where
        return self

    def from_(self, from_):
        self._from = from_
        return self

    def group_by(self, *columns):
        self._group_by = columns
        return self

    def order_by(self, *order_expressions):
        order_by = []
        for expr in order_expressions:
            if isinstance(expr, (tuple, list)):
                column, direction = expr
                direction = direction.upper()
                if direction not in ("ASC", "DESC"):
                    raise ValueError("Invalid sort direction: {!r}".format(
                        direction))
            else:
                column = expr
                direction = "ASC"
            if isinstance(column, Generic):
                column = column.extra['name']
            elif not isinstance(column, basestring):
                raise ValueError("Invalid value for column: {!r}".format(
                    column))

            order_by.append((column, direction))
        self._order_by = order_by
        return self

    def __unicode__(self):
        columns = self.format_columns(self._columns)
        statement = """SELECT {columns} FROM {from_}""".format(
            columns=columns, from_=self._from)
        if self._where is not None:
            statement = "{statement} WHERE {where}".format(
                statement=statement, where=self._where)
        if self._group_by is not None:
            group_by = self.format_columns(self._group_by)
            statement = "{statement} GROUP BY {group_by}".format(
                statement=statement, group_by=group_by)
        if self._order_by is not None:
            order_by = ", ".join([
                "{} {}".format(col, direction)
                for col, direction in self._order_by
            ])
            statement = "{statement} ORDER BY {order_by}".format(
                statement=statement, order_by=order_by)
        return statement

    @property
    def query(self):
        return self.__unicode__(), self.bound_values()

    def bound_values(self):
        return self._where.bound_values() if self._where else []

    def __str__(self):
        return self.__unicode__().encode('utf-8')


class Delete(SQLBase):
    def __init__(self):
        self._from = None
        self._where = None

    def where(self, where):
        self._where = where
        return self

    def from_(self, from_):
        self._from = from_
        return self

    def __unicode__(self):
        statement = """DELETE FROM {from_}""".format(from_=self._from)
        if self._where is not None:
            statement = "{statement} WHERE {where}".format(
                statement=statement, where=self._where)
        return statement

    @property
    def query(self):
        return self.__unicode__(), self.bound_values()

    def bound_values(self):
        return self._where.bound_values() if self._where else []

    def __str__(self):
        return self.__unicode__().encode('utf-8')


class Update(SQLBase):
    def __init__(self, tablename):
        self._table = tablename
        self._set_ops = UpdateAssignment()
        self._where = None

    @staticmethod
    def format_key(key):
        c_str = unicode(
            key if not isinstance(key, Generic) else key.extra['name'])
        return c_str

    def set_(self, kwargs):
        self._set_ops.update(kwargs)
        return self

    def where(self, where):
        self._where = where
        return self

    def __unicode__(self):
        # TODO: move Update.set to it's own class to handle serialization and
        # bound values cleaner
        set_params = unicode(self._set_ops)
        statement = """UPDATE {table} SET {set_params}""".format(
            table=self._table, set_params=set_params)

        if self._where is not None:
            statement = "{statement} WHERE {where}".format(
                statement=statement, where=self._where)
        return statement

    @property
    def query(self):
        return self.__unicode__(), self.bound_values()

    def bound_values(self):
        bound_values = []
        bound_values.extend(self._set_ops.bound_values())
        bound_values.extend(self._where.bound_values() if self._where else [])
        return bound_values

    def __str__(self):
        return self.__unicode__().encode('utf-8')


class Insert(SQLBase):
    def __init__(self, tablename):
        self._into = tablename
        self._values = {}
        self._select = None
        self._columns = None

    def values(self, kwargs):
        self._values.update(kwargs)
        return self

    def from_select(self, columns, select_query):
        self._columns = columns
        self._select = select_query
        return self

    def __unicode__(self):
        statement = """INSERT INTO {into}""".format(into=self._into)

        if self._values:
            columns = []
            values = []
            for k, v in sorted(self._values.iteritems()):
                columns.append(unicode(k))
                values.append(self.expression_param(v))

            statement = "{statement} ({columns}) VALUES ({values})".format(
                statement=statement,
                columns=", ".join(columns),
                values=", ".join(values))
        elif self._select is not None:
            columns = ", ".join([unicode(c) for c in self._columns])
            statement = "{statement} ({columns}) {select}".format(
                statement=statement, columns=columns, select=self._select)

        return statement

    @property
    def query(self):
        return self.__unicode__(), self.bound_values()

    def bound_values(self):
        if self._values:
            return [v for _, v in sorted(self._values.iteritems())]
        elif self._select:
            return list(self._select.bound_values())

    def __str__(self):
        return self.__unicode__().encode('utf-8')


class UpdateAssignment(SQLBase):
    def __init__(self):
        self._assignments = OrderedDict()

    def update(self, data):
        self._assignments.update(data)

    def __unicode__(self):
        assignments = []
        for field, assignment in self._assignments.iteritems():
            field_name = unicode(
                field.extra['name']
                if isinstance(field, Generic) else field)
            field_assignment = (
                unicode(assignment)
                if isinstance(assignment, SQLBase) else "?")
            assignments.append((field_name, field_assignment))
        return ", ".join("{} = {}".format(k, v) for k, v in assignments)

    def bound_values(self):
        bound_values = []
        for value in self._assignments.itervalues():
            if isinstance(value, SQLBase):
                bound_values.extend(value.bound_values())
            else:
                bound_values.append(value)
        return bound_values

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
        return " ".join(
            ["({})".format(" ".join([unicode(e) for e in self._expressions]))])

    def __str__(self):
        return self.__unicode__().encode('utf-8')

    def bound_values(self):
        return flatten(e.bound_values() for e in self._expressions
                       if not isinstance(e, basestring))


class Expression(SQLBase):
    def __init__(self, lhs=None, operation=None, rhs=None):
        self.lhs = lhs
        self.operation = operation
        self.rhs = rhs

    def __unicode__(self):
        lhs = self.expression_param(self.lhs)
        rhs = self.expression_param(self.rhs)
        return " ".join(map(unicode, (lhs, self.operation, rhs)))

    def __str__(self):
        return self.__unicode__().encode('utf-8')

    def bound_values(self):
        for value in self.expression_values(self.lhs):
            yield value
        for value in self.expression_values(self.rhs):
            yield value
        raise StopIteration()


class UnaryExpression(SQLBase):
    def __init__(self, operation=None, rhs=None):
        self.operation = operation
        self.rhs = rhs

    def __unicode__(self):
        rhs = self.expression_param(self.rhs)
        return " ".join(map(unicode, (self.operation, rhs)))

    def __str__(self):
        return self.__unicode__().encode('utf-8')

    def bound_values(self):
        for value in self.expression_values(self.rhs):
            yield value
        raise StopIteration()


class Function(SQLBase):
    def __init__(self, function=None, rhs=None):
        self.function = function
        self.rhs = rhs

    def __unicode__(self):
        return "{}({})".format(self.function, self.rhs)

    def __str__(self):
        return self.__unicode__().encode('utf-8')

    def bound_values(self):
        for value in self.expression_values(self.rhs):
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


class All(SQLBase):
    def __unicode__(self):
        return '*'

    def __str__(self):
        return self.__unicode__().encode('utf-8')


class SQLObjectMeta(ObjectMeta):
    @classmethod
    def hook(mcs, name, attrs, attr, value):
        attr_name = "{}.{}".format(attrs.get('__table_name__', name), attr)
        value.extra['name'] = attr_name

    def __unicode__(self):
        return ", ".join(
            getattr(self, f).extra['name'] for f in self.field_names)

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

    subq = Select(Manufacturer.make).from_(From('test_manufacturer')).where(
        Expression(Manufacturer.started, '>=', 2020))

    print Car
    print Car(model="foo", wheels=4)
    print unicode(Car.model)
    foo = Select(Car, Manufacturer).from_(
        From('test_cars').join(
            'test_manufacturer',
            Expression(Car.model, 'STARTSWITH', Manufacturer.make))).where(
                Where(
                    Where(Expression(Car.wheels, '>', 3)).and_(
                        Expression(Car.model, 'LIKE', '%Tesla%'))
                    .and_(Function('EXISTS', subq))).or_(
                        Where(Expression(Car.model, 'LIKE', '%Toyota%')).and_(
                            Expression(Car.wheels, '>', 16)).and_(
                                UnaryExpression('NOT', Manufacturer.make))))
    query, params = foo.query
    print query
    print params
    print '*' * 80

    bar = Select(Car.wheels, Function('COUNT', All())).from_(
        From('test_cars')).order_by(Car.wheels).group_by(Car.wheels)
    query, params = bar.query
    print query
    print params
    print '*' * 80

    delq = Delete().from_(From('test_cars')).where(
        Where(Expression(Car.wheels, '<', 4)))
    query, params = delq.query
    print query
    print params
    print '*' * 80

    insert_basic = Insert(From('test_cars')).values({
        Car.wheels: 5,
        Car.model: "foo"
    })
    query, params = insert_basic.query
    print query
    print params
    print '*' * 80

    insert_select = Insert(From('test_cars')).from_select((Car.model, ), subq)
    query, params = insert_select.query
    print query
    print params
    print '*' * 80

    update = Update(From('test_cars')).set_({
        Car.wheels: 5,
        Car.model: "foo"
    }).where(Where(Expression(Car.wheels, '<', 4)))
    query, params = update.query
    print query
    print params
    print '*' * 80


if __name__ == '__main__':
    main()

from __future__ import unicode_literals
import itertools


def flatten(l): 
	return [item for sublist in l for item in sublist]


class Select(object):
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
		return self.__unicode__(), self._where.values() if self._where else []

	def __str__(self):
		return self.__unicode__().encode('utf-8')


class Where(object):

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


class Expression(object):
	def __init__(self, lhs=None, operation=None, rhs=None):
		self.lhs = lhs
		self.operation = operation
		self.rhs = rhs

	def __unicode__(self):
		lhs = "?" if not isinstance(self.lhs, Generic) else self.lhs.extra['name']
		rhs = "?" if not isinstance(self.rhs, Generic) else self.rhs.extra['name']
		return " ".join(map(unicode, (lhs or "", self.operation, rhs or "")))

	def __str__(self):
		return self.__unicode__().encode('utf-8')

	def values(self):
		if not isinstance(self.lhs, Generic):
			yield self.lhs
		if not isinstance(self.rhs, Generic):
			yield self.rhs
		raise StopIteration()


class From(object):
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


from functools import partial
from valid_model.base import ObjectMeta, Object, Generic
from valid_model import descriptors as desc
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
	class Car(SQLObject):
		__table_name__ = 'test_cars'
		model = desc.String()
		wheels = desc.Integer()

	class Manufacturer(SQLObject):
		__table_name__ = 'test_manufacturer'
		make = desc.String()

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
				Expression(Manufacturer.make, 'EXISTS')
			)
		).or_(
			Where(
				Expression(Car.model, 'LIKE', '%Toyota%')
			).and_(
				Expression(Car.wheels, '>', 16)
			).and_(
				Expression(operation='NOT', rhs=Manufacturer.make)
			)
		)
	)
	query, params = foo.query
	print query
	print params

if __name__ == '__main__':
	main()

from __future__ import unicode_literals

import six


@six.python_2_unicode_compatible
class ValidationError(TypeError, ValueError):
    def __init__(self, msg, field=None):
        super(ValidationError, self).__init__(msg)
        self.field = field
        self.msg = msg

    def __str__(self):
        if self.field:
            return '{}: {}'.format(self.field, self.msg)
        else:
            return str(self.msg)

    def __repr__(self):
        return 'ValidationError({!r}, {!r})'.format(self.msg, self.field)

# import os, sys
# os.environ['EMCLI_PYTHONPATH'] = ':'.join(sys.path)
# print('hello world')
# see https://www.jython.org/jython-old-sites/docs/library/sys.html

from .creds import (
    CredsHandler,
)

from .core import (
    foo,
)

__all__ = (
    'CredsHandler',
    'foo',
)

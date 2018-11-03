import sys
import os



for p in sys.path:
    if (p.endswith('addons21')):
        sys.path.append(os.path.join(p, __name__))
        break

from ._version import __version__

from . import fields
from . import editor
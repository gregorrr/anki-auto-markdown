import sys
import os
from anki import version

anki21 = version.startswith("2.1.")
sys_encoding = sys.getfilesystemencoding()

if anki21:
    addon_path = os.path.dirname(__file__)
else:
    addon_path = os.path.dirname(__file__).decode(sys_encoding)

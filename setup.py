import sys
from cx_Freeze import setup, Executable
import version

# GUI applications require a different base on Windows (the default is for a console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

executables = [Executable("pyktv.py", base=base)]

options = {
    'build_exe': {
        'include_files': ['config.ini','db.sqlite3','locale','themes'],
    },

}

setup(
    name = "pyktv",
    options = options,
    version = version.__version__,
    description = 'A simple KTV program',
    executables = executables
)

import sys
from cx_Freeze import setup, Executable

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
    name = "<any name>",
    options = options,
    version = "<any number>",
    description = '<any description>',
    executables = executables
)

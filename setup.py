import sys
from cx_Freeze import setup, Executable
import version
import os


include_files=['config.ini','db.sqlite3','locale','themes','html']

# GUI applications require a different base on Windows (the default is for a console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"
    import ctypes.util
    lib=ctypes.util.find_library('mpv-1.dll')
    if lib: include_files.append(lib)
    lib=ctypes.util.find_library('youtube-dl.exe')
    if lib: include_files.append(lib)

    PYTHON_INSTALL_DIR = os.path.dirname(os.path.dirname(os.__file__))
    os.environ['TCL_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tcl8.6')
    os.environ['TK_LIBRARY'] = os.path.join(PYTHON_INSTALL_DIR, 'tcl', 'tk8.6')


executables = [Executable("pyktv.py", base=base, icon='pyktv.ico')]

options = {
    'build_exe': {
        'include_files': include_files,
        'packages': ['multiprocessing', 'idna', 'certifi', 'chardet', 'urllib3', 'asyncio', 'jinja2']
    },

}

setup(
    name = "pyktv",
    options = options,
    version = version.__version__,
    description = 'A simple KTV program',
    executables = executables
)

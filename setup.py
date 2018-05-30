import sys
from cx_Freeze import setup, Executable
import version
import os
from PyQt5.QtCore import QCoreApplication


include_files=['README.md','ChangeLog.md','LICENSE','config.ini','db.sqlite3','locale','themes','html','editor']

qtplugins=['sqldrivers','styles']
paths = [os.path.join(str(libpath), plug) for libpath in QCoreApplication.libraryPaths() for plug in qtplugins]
include_files.extend(filter(os.path.exists, paths))


# GUI applications require a different base on Windows (the default is for a console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"
    import ctypes.util
    # msvcr100.dll - Microsoft Visual C++ 2010
    # vcruntime140.dll - Microsoft Visual C++ 2015
    for n in ('mpv-1.dll', 'youtube-dl.exe', 'ffmpeg.exe', 'msvcr100.dll', 'vcruntime140.dll', ):
        lib=ctypes.util.find_library(n)
        if lib: include_files.append(lib)


executables = [Executable("pyktv.py", base=base, icon='themes/pyktv.ico'),
               Executable("songeditor.py", base=base, icon='themes/pyktv.ico'),
               Executable("show_key.py", base=base, icon='themes/pyktv.ico')]

options = {
    'build_exe': {
        'include_files': include_files,
        'packages': ['multiprocessing', 'idna', 'certifi', 'chardet', 'urllib3', 'asyncio', 'jinja2'],
        'excludes': ['tkinter'],
        'zip_include_packages': ['*'],
        'zip_exclude_packages': ['opencc'],
    },
}

# Build_YoutubeDL = False
# if Build_YoutubeDL:
#     for p in sys.path:
#         f=os.path.join(p,'youtube_dl/__main__.py')
#         if os.path.isfile(f):
#             executables.append(Executable(f, targetName='youtube-dl'+ (".exe" if sys.platform == "win32" else "") ))

setup(
    name = "pyktv",
    options = options,
    version = version.__version__.split('-')[0],
    description = 'A simple KTV program',
    executables = executables
)

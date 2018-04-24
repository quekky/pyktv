#!/usr/bin/env python

"""Editor for the db

copyleft quekky
"""

import sys
from PyQt5.QtWidgets import QApplication

import settings
from editorui import *


if __name__ == '__main__':
    settings.__init__()
    app = QApplication(sys.argv)
    editor = EditorWindow()
    # a = SearchMedia()
    sys.exit(app.exec_())

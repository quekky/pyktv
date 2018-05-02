#!/usr/bin/env python

"""Editor for the db

copyleft quekky
"""

import os
import sys

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, qApp

import settings
from editorui import EditorWindow


if __name__ == '__main__':
    settings.__init__()
    app = QApplication(sys.argv)
    qApp.setOrganizationName('pyktv')
    qApp.setApplicationName('songeditor')
    qApp.setWindowIcon(QIcon(os.path.join(settings.programDir, 'themes/pyktv.ico')))
    editor = EditorWindow()
    sys.exit(app.exec_())

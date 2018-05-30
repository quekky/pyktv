"""
Simple program to show what is the key pressed.
Click on the window to copy to clipboard, and paste directly to config.ini keyboard section
"""

import sys
import time

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QShortcut


class ShowKeyWindow(QWidget):
    prevtime=0
    prevkeys=[]

    def __init__(self):
        super().__init__()
        self.bglabel = QLabel(self)
        self.bglabel.setFixedSize(400, 100)
        self.cb = QApplication.clipboard()
        self.show()

    def keyReleaseEvent(self, QKeyEvent):
        key = QKeyEvent.key()
        if key==Qt.Key_Shift:
            key = Qt.ShiftModifier
        elif key==Qt.Key_Control:
            key = Qt.ControlModifier
        elif key==Qt.Key_Meta:
            key = Qt.MetaModifier
        elif key==Qt.Key_Alt:
            key = Qt.AltModifier

        now = time.time()
        if now-self.prevtime>1:
            self.prevkeys=[]
        self.prevkeys.append(key + int(QKeyEvent.modifiers()))
        self.prevtime = now
        s=QKeySequence(*self.prevkeys[-4:]).toString()
        self.bglabel.setText(s if s.isprintable() else hex(key))

    def mousePressEvent(self, QMouseEvent):
        self.cb.setText(self.bglabel.text(), mode=self.cb.Clipboard)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = ShowKeyWindow()
    sys.exit(app.exec_())

"""
Simple program to show what is the key pressed.
Click on the window to copy to clipboard, and paste directly to config.ini keyboard section
"""

import sys
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QApplication, QWidget, QLabel


class ShowKeyWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.bglabel = QLabel(self)
        self.bglabel.setFixedSize(200, 100)
        self.cb = QApplication.clipboard()
        self.show()

    def keyReleaseEvent(self, QKeyEvent):
        key = QKeyEvent.key()
        s=QKeySequence(key).toString()
        self.bglabel.setText(s if s.replace(' ', '').isalnum() else hex(key))

    def mousePressEvent(self, QMouseEvent):
        self.cb.setText(self.bglabel.text(), mode=self.cb.Clipboard)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    win = ShowKeyWindow()
    sys.exit(app.exec_())

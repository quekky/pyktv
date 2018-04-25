from PyQt5.QtCore import Qt, QUrl, pyqtSignal, pyqtSlot, QTimer, QSortFilterProxyModel, QRegExp
from PyQt5.QtNetwork import QNetworkRequest, QNetworkAccessManager
from PyQt5.QtWidgets import QLabel, QSizePolicy, QLineEdit, QStyledItemDelegate, QComboBox, QCompleter
from PyQt5.QtGui import QRegExpValidator, QTextDocument, QPixmap, QFont, QPainter, QFontMetrics
import re

import settings


class QScaledLabel(QLabel):
    _pixmap = None
    def drawPixmap(self):
        if self._pixmap:
            ratio=5/4
            h=self.height()
            w=h*ratio
            if w>self.width():
                w=self.width()
                h=w/ratio
            super().setPixmap(self._pixmap.scaled(w, h))

    def setPixmap(self, QPixmap):
        self._pixmap = QPixmap
        self.drawPixmap()

    def resizeEvent(self, *args, **kwargs):
        self.drawPixmap()


class QMarquee(QLabel):
    """Marque QLabel"""

    x = 0
    paused = False
    document = None
    speed = 100
    timer = None
    textvalue = ''
    plaintextvalue = ''
    fontcolor = 'black'
    fontpixelsize = 12

    def __init__(self, parent=None):
        super().__init__(parent)
        self.document = QTextDocument()

        self.x = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.translate)
        self.timer.start((1 / self.speed) * 1000)

    def setText(self, value):
        self.textvalue='<body>'+value+'</body>'
        self.plaintextvalue=value
        self._setDocument()

    def text(self):
        return self.plaintextvalue

    def setFontColor(self, p_str):
        self.fontcolor = p_str
        self._setDocument()

    def setPixelSize(self, p_int):
        self.fontpixelsize = int(p_int)
        self._setDocument()

    def _setDocument(self):
        self.document.setUseDesignMetrics(True)
        self.document.setDefaultStyleSheet('* {color: ' + self.fontcolor + '; font-size: ' +  str(self.fontpixelsize) + 'px;}')
        font = QFont()
        font.setPixelSize(self.fontpixelsize)
        fm = QFontMetrics(font)
        # I multiplied by 1.06 because otherwise the text goes on 2 lines
        self.document.setTextWidth(fm.width(self.plaintextvalue) * 1.06 + 10)
        self.document.setHtml(self.textvalue)


    @pyqtSlot()
    def translate(self):
        if not self.paused and self.isVisible():
            # text shorter then label
            if self.width() > self.document.textWidth():
                if self.x > -self.document.textWidth():
                    self.x -= 1
                else:
                    self.x = self.width() - self.document.textWidth()
            # text longer then label
            else:
                if self.x > self.width()-self.document.textWidth()*2:
                    self.x -= 1
                else:
                    self.x = self.width() - self.document.textWidth()
        self.update()

    def paintEvent(self, event):
        if self.plaintextvalue!='':
            p = QPainter(self)
            p.translate(self.x, 0)
            self.document.drawContents(p)
            if self.x < 0:
                p.translate(max(self.width(), self.document.textWidth()), 0)
                self.document.drawContents(p)
        return super().paintEvent(event)


class QLabelButton(QLabel):
    """
    Clickable Label

    This can pass an object to the function on click
    """

    clicked = pyqtSignal(object)
    rightclicked = pyqtSignal(object)
    index = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, QMouseEvent):
        if QMouseEvent.button()==Qt.LeftButton:
            self.click()
        elif QMouseEvent.button()==Qt.RightButton:
            self.rightclick()

    def click(self):
        try:
            self.clicked.emit(self.index)
        except:
            settings.logger.printException()

    def rightclick(self):
        try:
            self.rightclicked.emit(self.index)
        except:
            settings.logger.printException()


class QLabelListButton(QLabelButton):
    """Label with a numbering in front"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.fontcolor = settings.config['font.color']
        self.fontstylesheet = 'color: ' + self.fontcolor + ';'
        self.globalfont = QFont()

        self.text = QLabel(self)
        self.text.setStyleSheet(self.fontstylesheet+'border-radius: 8px; background-color: qlineargradient(spread:pad, x1:0, x2:1, stop:0 rgba(0, 0, 0, 200), stop:1 rgba(120, 120, 120, 50));padding:2px 0px;')
        self.image = QLabel(self)
        self.image.setScaledContents(True)
        self.image.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.label = QLabel(self)
        self.label.move(0, 0)
        self.label.setAlignment(Qt.AlignCenter)

    def setText(self, p_str):
        self.text.setText(p_str)

    def setLabelText(self, p_str):
        self.label.setText(p_str)

    def setPixmap(self, QPixmap):
        if QPixmap is None:
            self.image.clear()
        else:
            self.image.setPixmap(QPixmap)

    def setImageResponse(self, reply):
        qp = QPixmap()
        qp.loadFromData(reply.readAll())
        self.setPixmap(qp)

    def setImage(self, image, altimage):
        if re.match("(ftp|http|https)://", image):
            self.setPixmap(QPixmap(altimage))
            self.nam = QNetworkAccessManager()
            self.nam.finished.connect(self.setImageResponse)
            self.nam.get(QNetworkRequest(QUrl(image)))
        else:
            try:
                if image=='':
                    self.setPixmap(QPixmap(altimage))
                else:
                    pixmap = QPixmap(image)
                    if pixmap.isNull():
                        self.setPixmap(QPixmap(altimage))
                    else:
                        self.setPixmap(QPixmap(image))
            except:
                self.setPixmap(QPixmap(altimage))

    def clearPixmap(self):
        self.image.clear()

    def setTextSize(self):
        labelwidth=int(self.height()*0.9)
        self.label.resize(labelwidth, labelwidth)
        self.label.setStyleSheet('color: white; border-radius: '+str(labelwidth/2-0.5)+'px; font: bold '+str(int(self.height()*0.7))+'px;padding:0px 4px 4px 0px;'
                                 'background-color: qradialgradient(spread:pad, cx:0.272, cy:0.354515, radius:0.848, fx:0.186, fy:0.256117, stop:0 rgba(220, 220, 220, 255), stop:0.2 rgba(200, 20, 20, 255), stop:1 rgba(20, 0, 0, 220));')

        self.text.move(self.height(), 0)
        self.text.resize(self.width() - self.height(), self.height())
        self.globalfont.setPixelSize(self.height() * 0.7)
        self.text.setFont(self.globalfont)

        self.image.move(self.width()-self.height(), 0)
        self.image.resize(self.height(), self.height())

    def resizeEvent(self, *args, **kwargs):
        super().resizeEvent(*args, **kwargs)
        self.setTextSize()


class QLabeImageButton(QLabelListButton):
    """Image and text"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.text.setStyleSheet(self.fontstylesheet+'border-bottom-left-radius: 18px; border-bottom-right-radius: 18px; background-color: qlineargradient(spread:pad, y1:0, y2:1, stop:0 rgba(0, 0, 0, 230), stop:1 rgba(120, 120, 120, 120));padding: 0px;')
        self.text.setAlignment(Qt.AlignCenter)
        self.image.setStyleSheet('background-color: qlineargradient(spread:pad, x1:1, y1:0.8, x2:0, y2:0.1, stop:0.00564972 rgba(186, 225, 255, 255), stop:0.4 rgba(255, 255, 255, 230), stop:0.6 rgba(255, 255, 255, 180), stop:1 rgba(134, 203, 255, 120));')

    def setTextSize(self):
        labelwidth=int(self.height()*0.2)
        self.label.move((self.width()-labelwidth)/2, 0)
        self.label.resize(labelwidth, labelwidth)
        self.label.setStyleSheet('color: white; border-radius: '+str(labelwidth/2-0.5)+'px; font: bold '+str(int(labelwidth*0.9))+'px;padding:0px 3px 3px 0px;'
                                 'background-color: qradialgradient(spread:pad, cx:0.272, cy:0.354515, radius:0.848, fx:0.186, fy:0.256117, stop:0 rgba(220, 220, 220, 255), stop:0.2 rgba(200, 20, 20, 255), stop:1 rgba(20, 0, 0, 220));')

        imagey=self.height()*0.13
        imageheight=int(self.height()*0.7)
        self.image.move(0, imagey)
        self.image.resize(self.width(), imageheight)

        self.text.move(0, imagey+imageheight)
        self.text.resize(self.width(), self.height()-imagey-imageheight)
        self.globalfont.setPixelSize(self.text.height()*0.8)
        self.text.setFont(self.globalfont)


class QUpperValidator(QRegExpValidator):
    def validate(self, p_str, p_int):
        ret=super().validate(p_str, p_int)
        return ret[0], ret[1].upper(), ret[2]


class QTagCompleterLineEdit(QLineEdit):
    _completer = None

    def __init__(self, parent):
        super().__init__(parent)
        self.textEdited.connect(self.text_edited)
        self.cursorPositionChanged.connect(self.cursor_changed)

    def text_edited(self, text):
        if self._completer:
            cursor_pos = self.cursorPosition()
            before_text = self.text()[:cursor_pos]
            after_text = self.text()[cursor_pos:]
            prefix = before_text.split(',')[-1].strip()

            # filter away those already typed
            text_tags = set(before_text.split(',')[:-1]+after_text.split(','))
            text_tags = [t.strip().replace('|','\\|') for t in text_tags]
            if text_tags:
                model=self._completer.model()
                if not isinstance(model, QSortFilterProxyModel):
                    proxy1 = QSortFilterProxyModel()
                    proxy1.setSourceModel(model)
                    self._completer.setModel(proxy1)
                    model=proxy1
                model.setFilterRegExp('(?!('+'|'.join(text_tags)+')$)(^.*$)')

            self._completer.setCompletionPrefix(prefix)
            self._completer.complete()

    def cursor_changed(self, old, new):
        if self._completer.popup() and self._completer.popup().isVisible():
            self.text_edited(self.text())

    def complete_text(self, text):
        cursor_pos = self.cursorPosition()
        before_text = self.text()[:cursor_pos]
        after_text = self.text()[cursor_pos:]
        prefix_len = len(before_text.split(',')[-1].strip())
        self.setText('%s%s, %s' % (before_text[:cursor_pos - prefix_len], text, after_text))
        self.setCursorPosition(cursor_pos - prefix_len + len(text) + 2)

    def setCompleter(self, completer):
        self._completer = completer
        self._completer.setWidget(self)
        self._completer.activated.connect(self.complete_text)

    def completer(self):
        return self._completer


class QCustomDelegate(QStyledItemDelegate):
    def __init__(self, parent=None, validator=None, model=None):
        super().__init__(parent)
        self._validator=validator
        self._model=model


class QLineEditDelegate(QCustomDelegate):
    def createEditor(self, parent, option, index):
        lineedit=QLineEdit(parent)
        lineedit.setValidator(self._validator)
        if self._model:
            completer=QCompleter()
            completer.setModel(self._model)
            lineedit.setCompleter(completer)
        return lineedit

    def setEditorData(self, editor, index):
        editor.setText(index.data(Qt.EditRole))

    def setModelData(self, editor, model, index):
        model.setData(index, editor.text())


class QComboBoxDelegate(QCustomDelegate):
    def createEditor(self, parent, option, index):
        combobox=QComboBox(parent)
        combobox.setValidator(self._validator)
        combobox.setModel(self._model)
        try:
            edit = not self._model.disallowedit
        except:
            edit = True
        combobox.setEditable(edit)
        return combobox

    def setEditorData(self, editor, index):
        data=index.data(Qt.EditRole)
        editor.setCurrentIndex(editor.findText(data))
        editor.setCurrentText(data)

    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText())


class QTagCompleterLineEditDelegate(QLineEditDelegate):
    def createEditor(self, parent, option, index):
        lineedit=QTagCompleterLineEdit(parent)
        lineedit.setValidator(self._validator)
        if self._model:
            completer=QCompleter()
            completer.setModel(self._model)
            lineedit.setCompleter(completer)
        return lineedit

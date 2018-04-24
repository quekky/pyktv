from PyQt5.QtCore import Qt, QUrl, pyqtSignal, pyqtSlot, QTimer
from PyQt5.QtNetwork import QNetworkRequest, QNetworkAccessManager
from PyQt5.QtWidgets import QLabel, QSizePolicy, qApp
from PyQt5.QtGui import QRegExpValidator, QTextDocument, QPixmap, QFont, QPainter, QFontMetrics

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
            try:
                self.clicked.emit(self.index)
            except:
                settings.logger.printException()
        elif QMouseEvent.button()==Qt.RightButton:
            try:
                self.rightclicked.emit(self.index)
            except:
                settings.logger.printException()


class QLabelListButton(QLabelButton):
    """Label with a numbering in front"""

    def __init__(self, parent=None, havesub=False):
        super().__init__(parent)
        self.fontcolor = settings.config['font.color']
        self.fontstylesheet = 'color: ' + self.fontcolor + ';'
        self.globalfont = QFont()
        self.havesub = havesub

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
        if re.match("(ftp|http|https):\/\/", image):
            self.setPixmap(QPixmap(altimage))
            self.nam = QNetworkAccessManager()
            self.nam.finished.connect(self.setImageResponse)
            self.nam.get(QNetworkRequest(QUrl(image)))
        else:
            try:
                if image=='':
                    self.setPixmap(QPixmap(altimage))
                else:
                    self.setPixmap(QPixmap(image))
            except:
                self.setPixmap(QPixmap(altimage))

    def clearPixmap(self):
        self.image.clear()

    def setTextSize(self):
        labelwidth=int(self.height()*0.9);
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

    def __init__(self, parent=None, havesub=False):
        super().__init__(parent)
        self.text.setStyleSheet(self.fontstylesheet+'border-bottom-left-radius: 18px; border-bottom-right-radius: 18px; background-color: qlineargradient(spread:pad, y1:0, y2:1, stop:0 rgba(0, 0, 0, 230), stop:1 rgba(120, 120, 120, 120));padding: 0px;')
        self.text.setAlignment(Qt.AlignCenter)
        self.image.setStyleSheet('background-color: qlineargradient(spread:pad, x1:1, y1:0.8, x2:0, y2:0.1, stop:0.00564972 rgba(186, 225, 255, 255), stop:0.4 rgba(255, 255, 255, 230), stop:0.6 rgba(255, 255, 255, 180), stop:1 rgba(134, 203, 255, 120));')

    def setTextSize(self):
        labelwidth=int(self.height()*0.2);
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


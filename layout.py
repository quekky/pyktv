import sys
from PyQt5.QtCore import QTimer, pyqtSignal, pyqtSlot, Qt
from PyQt5.QtGui import QPixmap, QFont, QTextDocument, QFontMetrics, QPainter
from PyQt5.QtWidgets import QWidget, QLabel, QSizePolicy, QHBoxLayout, qApp, QVBoxLayout, QMenu, QStackedLayout, QGridLayout
import time

import playlist
import settings
from screen import startHomeScreen


def setZeroMargins(layout):
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    return layout


class CommonWindow(QWidget):
    """Common window for both windows"""

    def contextMenuEvent(self, QContextMenuEvent):
        """Right click"""
        menu = QMenu(self)
        # page1 = menu.addAction("Page1")
        # page2 = menu.addAction("Page2")
        # page3 = menu.addAction("Page3")
        # pages = [page1, page2, page3]
        # menu.addSeparator()
        quitAction = menu.addAction("Quit")
        action = menu.exec_(self.mapToGlobal(QContextMenuEvent.pos()))
        # if action in pages:
        #     settings.selectorWindow.gotoPage(pages.index(action))
        if action == quitAction:
            qApp.quit()

    def keyReleaseEvent(self, QKeyEvent):
        """Key press"""
        key = QKeyEvent.key()
        if settings.selectorWindow.insearch:
            if Qt.Key_0 <= key <= Qt.Key_9:
                index = key - Qt.Key_0 - 1
                if index == -1: index = 9
                # print("Search number pressed", index)
                settings.selectorWindow.searchcontentoption[index].click()
            if Qt.Key_A <= key <= Qt.Key_Z:
                index = key
                # print("Search number pressed", index)
                settings.selectorWindow.searchKeyPressedAlpha(chr(index))
            elif Qt.Key_F1 <= key <= Qt.Key_F4:
                index = key - Qt.Key_F1
                # print("Search F_key pressed", index)
                settings.selectorWindow.searchfunctionoption[index].click()
            elif key == Qt.Key_Backspace:
                # print("Search backspace pressed")
                settings.selectorWindow.searchbackspaceoption.click()
            elif key == Qt.Key_Enter or key==Qt.Key_Return:
                # print(key, Qt.Key_Enter, Qt.Key_Return, settings.selectorWindow.searchenteroption)
                settings.selectorWindow.searchenteroption.click()
        else:
            if Qt.Key_0 <= key <= Qt.Key_9:
                index=key-Qt.Key_0-1
                if index==-1: index=9
                # print("Number pressed", index)
                settings.selectorWindow.contentoption[settings.selectorWindow.stackedlayout.currentIndex()][index].click()
            elif Qt.Key_F1 <= key <= Qt.Key_F4:
                index=key-Qt.Key_F1
                # print("F_key pressed", index)
                settings.selectorWindow.functionoption[index].click()
            elif key == Qt.Key_PageUp or key == Qt.Key_F5:
                settings.selectorWindow.footeroption[0].click()
            elif key == Qt.Key_PageDown or key == Qt.Key_F6:
                settings.selectorWindow.footeroption[1].click()
            elif key == Qt.Key_Backspace:
                settings.selectorWindow.backoption.click()
        if key == Qt.Key_Space:
            playlist.switchChannel()
        elif key == Qt.Key_F10:
            playlist.playNextSong()
        elif key == Qt.Key_F12:
            settings.selectorWindow.stopSearch()
            settings.selectorWindow.homeoption.click()

    def closeEvent(self, QCloseEvent):
        qApp.quit()


class VideoWindow(CommonWindow):
    """Video window"""

    timer=QTimer()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video")
        geo=list(map(int, settings.config['video.window'].split(',')))
        self.move(geo[0], geo[1])
        self.resize(geo[2], geo[3])
        if settings.config.getboolean('video.frameless'): self.setWindowFlag(Qt.FramelessWindowHint)

        self.timer.timeout.connect(self.stopStatusTempText)

        ### Using qlabel to set the image, so not sure if MacOS will still work for vlc
        # In this widget, the video will be drawn
        # if sys.platform == "darwin":  # for MacOS
        #     from PyQt5.QtWidgets import QMacCocoaViewContainer
        #     self.videoframe = QMacCocoaViewContainer(0)
        # else:
        #     self.videoframe = QFrame()
        #
        # self.videolayout = setZeroMargins(QHBoxLayout(self))
        # self.videolayout.addWidget(self.videoframe)

        self.bglabel = QLabel()
        self.backgroundimage = QPixmap(settings.themeDir + "video.jpg")
        self.bglabel.setScaledContents(True)
        self.bglabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.bglabel.setPixmap(self.backgroundimage)

        self.bglayout = setZeroMargins(QHBoxLayout(self))
        self.bglayout.addWidget(self.bglabel)

        self.videoframe = self.bglabel

        self.mediaplayer = settings.vlcMediaPlayer
        # the media player has to be 'connected' to the QFrame
        # (otherwise a video would be displayed in it's own window)
        # this is platform specific!
        # you have to give the id of the QFrame (or similar object) to
        # vlc, different platforms have different functions for this
        if sys.platform.startswith('linux'):  # for Linux using the X Server
            self.mediaplayer.set_xwindow(self.videoframe.winId())
        elif sys.platform == "win32":  # for Windows
            self.mediaplayer.set_hwnd(self.videoframe.winId())
            pass
        elif sys.platform == "darwin":  # for MacOS
            self.mediaplayer.set_nsobject(int(self.videoframe.winId()))

        self.globalfont = QFont()
        self.statuslabel = QLabel(self)
        self.statuslabel.setStyleSheet('color:' + settings.config['font.color'] + '; background:black')
        self.statuslabel.hide()

        self.show()
        if settings.config.getboolean('video.fullscreen'): self.setWindowState(Qt.WindowFullScreen)

    def resizeEvent(self, QResizeEvent):
        super().resizeEvent(QResizeEvent)
        height=self.height()
        width=self.width()
        self.globalfont.setPixelSize(height*0.03)
        self.statuslabel.move(width*0.01, height*0.01)
        self.statuslabel.setFont(self.globalfont)
        self.statuslabel.adjustSize()

    def setStatusTempText(self, p_str, msec):
        if self.timer.isActive():
            self.timer.stop()
        self.timer.setSingleShot(True)
        self.timer.start(msec)

        self.statuslabel.setText(p_str)
        self.statuslabel.adjustSize()
        if p_str != '': self.statuslabel.show()

    @pyqtSlot()
    def stopStatusTempText(self):
        self.statuslabel.setText('')
        self.statuslabel.hide()


class SelectorWindow(CommonWindow):
    """Selector window"""

    statustext=''
    timer=QTimer()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Selector")
        geo=list(map(int, settings.config['selector.window'].split(',')))
        self.move(geo[0], geo[1])
        self.resize(geo[2], geo[3])
        if settings.config.getboolean('selector.frameless'): self.setWindowFlag(Qt.FramelessWindowHint)

        self.globalfont=QFont()
        self.fontcolor=settings.config['font.color']
        self.fontstylesheet = 'color: ' + self.fontcolor

        self.timer.timeout.connect(self.setOldStatusText)

        self.loadImages()
        self.createLayout()

        self.show()
        self.gotoPage(0)
        if settings.config.getboolean('selector.fullscreen'): self.setWindowState(Qt.WindowFullScreen)


    def loadImages(self):
        imagefiles = ['menu_main.jpg', 'menu_normal.jpg', 'menu_singer.jpg']
        self.backgroundimages = []
        for f in imagefiles:
            self.backgroundimages.append(QPixmap(settings.themeDir + f))
        self.nosingerimage = QPixmap(settings.themeDir + 'default_singer.jpg')


    def createLayout(self):
        fontstylesheet=self.fontstylesheet
        # background image
        self.bglabel = QLabel()
        self.bglabel.setScaledContents(True)
        self.bglabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.bglayout = setZeroMargins(QHBoxLayout(self))
        self.bglayout.addWidget(self.bglabel)

        # create the vertical frames
        self.vlayout = setZeroMargins(QVBoxLayout(self.bglabel))
        self.headerframe = QWidget()
        self.functionframe = QWidget()
        self.contentframe = QWidget()
        self.footerframe = QWidget()
        self.statusframe = QMarquee()
        self.statusframe.setFontColor(self.fontcolor)

        self.vlayout.addWidget(self.headerframe, 65)
        self.vlayout.addWidget(self.functionframe, 60)
        self.vlayout.addWidget(self.contentframe, 695)
        self.vlayout.addStretch(10)
        self.vlayout.addWidget(self.footerframe, 60)
        self.vlayout.addStretch(60)
        self.vlayout.addWidget(self.statusframe, 50)


        # create the header
        self.headerlayout = setZeroMargins(QHBoxLayout(self.headerframe))
        self.backoption = QLabelButton()
        self.backoption.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.backoption.setText("🡄")
        self.backoption.setStyleSheet("color:lightgrey")
        self.backoption.setAlignment(Qt.AlignCenter)
        self.backoption.setCursor(Qt.PointingHandCursor)
        self.backoption.index = "Back"
        self.headerlayout.addWidget(self.backoption, 10)
        self.headerlayout.addStretch(35)

        self.homeoption = QLabelButton()
        self.homeoption.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        # self.homeoption.setText("🏠")
        self.homeoption.setText(" ")
        self.homeoption.setStyleSheet("color:lightyellow")
        self.homeoption.setAlignment(Qt.AlignCenter)
        self.homeoption.setCursor(Qt.PointingHandCursor)
        self.homeoption.index = "Home"
        self.homeoption.clicked.connect(startHomeScreen)
        self.headerlayout.addWidget(self.homeoption, 10)
        self.headerlayout.addStretch(45)


        # create the function
        self.functionlayout = setZeroMargins(QHBoxLayout(self.functionframe))
        self.functionoption = []
        self.functionlayout.addStretch(100)
        for i in range(4):
            self.functionoption.append(QLabelButton())
            self.functionoption[i].setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            self.functionoption[i].setText("Press F" + str(i + 1))
            self.functionoption[i].setStyleSheet(fontstylesheet)
            self.functionoption[i].setCursor(Qt.PointingHandCursor)
            self.functionoption[i].index= "F" + str(i + 1)
            self.functionlayout.addWidget(self.functionoption[i], 170)
            self.functionlayout.addStretch(50)
        self.functionlayout.addStretch(10)


        # create the 3 contents, and stacked them
        self.stackedlayout = QStackedLayout(self.contentframe)
        for i in range(3):
            self.stackedlayout.addWidget(QWidget())

        self.contentoption = [[],[],[]]
        self.contentimage = [[],[],[]]

        self.createLayout0(self.stackedlayout.widget(0))
        self.createLayout1(self.stackedlayout.widget(1))
        self.createLayout2(self.stackedlayout.widget(2))


        # create footer
        self.footerlayout = setZeroMargins(QHBoxLayout(self.footerframe))
        self.pageroption = QLabel()
        self.footeroption = [QLabelButton(), QLabelButton()]
        self.footeroption[0].setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        # self.footeroption[0].setText("Press F5")
        self.footeroption[0].setStyleSheet(fontstylesheet)
        self.footeroption[0].setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.footeroption[0].setCursor(Qt.PointingHandCursor)
        self.footeroption[0].index = "F5"
        self.footeroption[1].setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        # self.footeroption[1].setText("Press F6")
        self.footeroption[1].setStyleSheet(fontstylesheet)
        self.footeroption[1].setCursor(Qt.PointingHandCursor)
        self.footeroption[1].index = "F6"
        self.pageroption.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.pageroption.setText("Pager")
        self.pageroption.setStyleSheet(fontstylesheet)
        self.pageroption.setAlignment(Qt.AlignCenter)

        self.footerlayout.addWidget(self.footeroption[0], 345)
        self.footerlayout.addStretch(60)
        self.footerlayout.addWidget(self.pageroption, 230)
        self.footerlayout.addStretch(60)
        self.footerlayout.addWidget(self.footeroption[1], 325)

        self.createSearchLayout()


    def createLayout0(self, widget):
        # create the grid for the 10 options
        self.contentlayout0 = setZeroMargins(QGridLayout())

        layoutspan= [(4,7,6),(2,7,8),(1,5,6),(2,7,8),(4,7,6),
                     (4,5,2),(11,9,2),(12,10,1),(11,9,2),(4,5,2)]
        for i in range(10):
            btn=QLabelButton()
            self.contentoption[0].append(btn)
            btn.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            btn.setText("Content " + str((i+1) % 10))
            btn.setStyleSheet(self.fontstylesheet)
            btn.setAlignment((Qt.AlignRight if i < 5 else Qt.AlignLeft) | Qt.AlignBottom)
            btn.setCursor(Qt.PointingHandCursor)
            btn.index=i
            hlayout = setZeroMargins(QHBoxLayout())
            hlayout.addStretch(layoutspan[i][0])
            hlayout.addWidget(btn,layoutspan[i][1])
            hlayout.addStretch(layoutspan[i][2])
            self.contentlayout0.addLayout(hlayout, i % 5, i / 5)

        # position it in the content area
        vcontentlayout = setZeroMargins(QVBoxLayout(widget))
        vcontentlayout.addStretch(65)
        vcontentlayout.addLayout(self.contentlayout0, 835)
        vcontentlayout.addStretch(100)


    def createLayout1(self, widget):
        # create the vlayout for the 10 options
        self.contentlayout1 = setZeroMargins(QVBoxLayout())
        for i in range(10):
            btn=QLabelButton()
            self.contentoption[1].append(btn)
            btn.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            # btn.setText("Content number " + str((i + 1) % 10) + " and then a very long string............")
            btn.setStyleSheet(self.fontstylesheet)
            btn.setCursor(Qt.PointingHandCursor)
            btn.index=i
            self.contentlayout1.addWidget(btn, 9)
            self.contentlayout1.addStretch(1)

        # position it in the content area
        vcontentlayout = setZeroMargins(QHBoxLayout(widget))
        vcontentlayout.addStretch(185)
        vcontentlayout.addLayout(self.contentlayout1, 700)
        vcontentlayout.addStretch(115)


    def createLayout2(self, widget):
        # create the grid for the 10 options
        self.contentlayout2 = setZeroMargins(QGridLayout())
        for i in range(10):
            btn1=QLabelButton()
            self.contentimage[2].append(btn1)
            btn1.setScaledContents(True)
            btn1.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            btn1.setCursor(Qt.PointingHandCursor)
            btn1.index=i
            btn2=QLabelButton()
            self.contentoption[2].append(btn2)
            btn2.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            # btn2.setText("Singer " + str((i + 1) % 10))
            btn2.setStyleSheet(self.fontstylesheet)
            btn2.setStyleSheet('color: yellow; background-color: rgba(0, 255, ' + str((i % 2) * 255) + ', 100);')
            btn2.setAlignment(Qt.AlignCenter)
            btn2.setCursor(Qt.PointingHandCursor)
            btn2.index=i
            vlayout = setZeroMargins(QVBoxLayout())
            vlayout.addStretch(45)
            vlayout.addWidget(btn1,162)
            vlayout.addWidget(btn2,38)
            vlayout.addStretch(21)
            hlayout = setZeroMargins(QHBoxLayout())
            hlayout.addStretch(15)
            hlayout.addLayout(vlayout,165)
            hlayout.addStretch(15)
            self.contentlayout2.addLayout(hlayout, i / 5, i % 5)

        # position it in the content area
        vcontentlayout = setZeroMargins(QHBoxLayout(widget))
        vcontentlayout.addStretch(14)
        vcontentlayout.addLayout(self.contentlayout2, 973)
        vcontentlayout.addStretch(13)


    def setTextSize(self):
        """resize text size to label height"""
        self.globalfont.setPixelSize(self.backoption.size().height() * 0.6)
        self.backoption.setFont(self.globalfont)
        self.homeoption.setFont(self.globalfont)
        self.globalfont.setPixelSize(self.functionoption[0].size().height() * 0.7)
        for option in self.functionoption + self.footeroption + [self.pageroption]:
            option.setFont(self.globalfont)
        self.globalfont.setPixelSize(self.contentoption[0][0].size().height()*0.4)
        for option in self.contentoption[0]:
            option.setFont(self.globalfont)
        self.globalfont.setPixelSize(self.contentoption[1][0].size().height()*0.7)
        for option in self.contentoption[1]:
            option.setFont(self.globalfont)
        self.globalfont.setPixelSize(self.contentoption[2][0].size().height()*0.9)
        for option in self.contentoption[2]:
            option.setFont(self.globalfont)
        # self.globalfont.setPixelSize(self.statusframe.size().height()*0.6)
        # self.statusframe.setFont(self.globalfont)
        self.statusframe.setPixelSize(self.statusframe.size().height()*0.6)

        if self.searchframe.isVisible():
            self.setSearchTextSize()


    """
    search functions
    """

    insearch=False
    cell_keyboard = {0: ('1', 'ABC2', 'DEF3', 'GHI4', 'JKL5', 'MNO6', 'PQRS7', 'TUV8', 'WXYZ9', '0'),
                     1: ('1', '2', '3', '4', '5', '6', '7', '8', '9', '0')}
    searchtype = 0
    searchlastkey = [-1, 0]
    searchstring = ''
    searchresponsetime = 0
    searchthreshold = 2
    searchtimer = QTimer()
    searchcallback = None

    def createSearchLayout(self):
        fontstylesheet=self.fontstylesheet

        # create the search window
        self.searchframe = QLabel(self.bglabel)
        self.searchframe.setScaledContents(True)
        self.searchframe.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.searchimage = QPixmap(settings.themeDir + "menu_search.jpg")
        self.searchframe.setPixmap(self.searchimage)
        self.searchframe.hide()

        searchlayout1h = setZeroMargins(QHBoxLayout(self.searchframe))
        searchframe1h_1 = QWidget()
        searchframe1h_2 = QWidget()
        searchframe1h_3 = QWidget()
        searchlayout1h.addStretch(43)
        searchlayout1h.addWidget(searchframe1h_1,730)
        searchlayout1h.addStretch(62)
        searchlayout1h.addWidget(searchframe1h_2,653)
        searchlayout1h.addWidget(searchframe1h_3,94)
        searchlayout1h.addStretch(18)

        searchlayout2v = setZeroMargins(QVBoxLayout(searchframe1h_1))
        self.searchtitle = QLabel()
        self.searchtitle.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.searchtitle.setStyleSheet(fontstylesheet+';font:bold;')
        self.searchtitle.setText(_("Search character:"))
        self.searchlabel = QLabel()
        self.searchlabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.searchlabel.setStyleSheet(fontstylesheet+"; padding: 0 10%;")
        # self.searchlabel.setStyleSheet("color:lightyellow; background-color: rgba(255,0,0,150); padding: 0px 10px")
        # self.searchlabel.setText("A B <font color=\"cyan\">C</font>")
        searchframe2v_3 = QWidget()
        searchlayout2v.addStretch(3)
        searchlayout2v.addWidget(self.searchtitle,40)
        searchlayout2v.addStretch(3)
        searchlayout2v.addWidget(self.searchlabel,56)
        searchlayout2v.addStretch(6)
        searchlayout2v.addWidget(searchframe2v_3,52)
        searchlayout2v.addStretch(3)

        f_text=(_('F1: Ok'),_('F2: Del'),_('F3: Cancel'),_('F4:'))
        searchlayout3h = setZeroMargins(QHBoxLayout(searchframe2v_3))
        self.searchfunctionoption = []
        #create a filler "F4"
        for i in range(4):
            self.searchfunctionoption.append(QLabelButton())
            self.searchfunctionoption[i].setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            self.searchfunctionoption[i].setText(f_text[i])
            self.searchfunctionoption[i].setStyleSheet(fontstylesheet)
            # self.searchfunctionoption[i].setStyleSheet("color:lightyellow; background-color: rgba(255,0,0,150)")
            self.searchfunctionoption[i].setAlignment(Qt.AlignCenter)
            self.searchfunctionoption[i].setCursor(Qt.PointingHandCursor)
            self.searchfunctionoption[i].index="F" + str(i + 1)
            self.searchfunctionoption[i].clicked.connect(self.searchButtonPressedFunction)
        for i in range(3):
            searchlayout3h.addWidget(self.searchfunctionoption[i])

        searchlayout4g = setZeroMargins(QGridLayout(searchframe1h_2))
        self.searchcontentoption = []
        #create a filler btn "0"
        for i in range(10):
            self.searchcontentoption.append(QLabelButton())
            self.searchcontentoption[i].setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            self.searchcontentoption[i].setStyleSheet(fontstylesheet)
            # self.searchcontentoption[i].setStyleSheet("color:lightyellow; background-color: rgba(255,255,0,150)")
            self.searchcontentoption[i].setAlignment(Qt.AlignCenter)
            self.searchcontentoption[i].setCursor(Qt.PointingHandCursor)
            self.searchcontentoption[i].index=i
            self.searchcontentoption[i].clicked.connect(self.searchButtonPressedNumber)
        for i in range(9):
            searchlayout4g.addWidget(self.searchcontentoption[i], i/3, i%3)

        searchlayout5v = setZeroMargins(QVBoxLayout(searchframe1h_3))
        searchlayout5v.addStretch(2)
        searchlayout5v.addWidget(self.searchcontentoption[9],1)

        #fillers
        self.searchbackspaceoption = QLabelButton()
        self.searchbackspaceoption.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.searchbackspaceoption.setStyleSheet(fontstylesheet)
        self.searchbackspaceoption.setText("🡄")
        self.searchbackspaceoption.clicked.connect(self.searchButtonPressedBackspace)

        self.searchenteroption = QLabelButton()
        self.searchenteroption.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.searchenteroption.setStyleSheet(fontstylesheet)
        self.searchenteroption.setText("Enter")
        self.searchenteroption.clicked.connect(self.searchButtonPressedEnter)

        self.searchtimer.setSingleShot(True)
        self.searchtimer.setInterval(self.searchthreshold*1000)
        self.searchtimer.timeout.connect(self.searchButtonPressedTimeout)

    def setSearchTextSize(self):
        self.globalfont.setPixelSize(self.searchfunctionoption[0].size().height() * 0.7)
        for option in self.searchfunctionoption:
            option.setFont(self.globalfont)
        self.globalfont.setPixelSize(self.searchcontentoption[0].size().height() * 0.7)
        for option in self.searchcontentoption:
            option.setFont(self.globalfont)
        self.globalfont.setPixelSize(self.searchtitle.size().height() * 0.9)
        self.searchtitle.setFont(self.globalfont)
        self.globalfont.setPixelSize(self.searchlabel.size().height() * 0.7)
        self.searchlabel.setFont(self.globalfont)


    def setSearchPos(self):
        if self.searchframe.isVisible():
            width = self.geometry().width()
            height = self.geometry().height()
            x = int(width*0.6)
            y = int(height*0.6)
            x = int(width*0)
            y = int(height*0.82)
            self.searchframe.move(x, y)
            self.searchframe.setFixedSize(width-x, height-y)

    def startSearch(self, searchtype=0):
        """display the search bar

        searchtype:
            0=alphanumeric
            1=numbers only
        """
        self.insearch=True
        self.searchstring=''
        self.searchtype=searchtype

        for i in range(10):
            self.searchcontentoption[i].setText(self.cell_keyboard[self.searchtype][i])

        self.searchframe.show()
        self.setSearchPos()
        self.setSearchTextSize()
        self.searchTextDisplay()
        self.callSearchCallback()

    def stopSearch(self):
        self.insearch=False
        self.searchframe.hide()

    def setSearchCallback(self, callback):
        self.searchcallback=callback

    def callSearchCallback(self):
        if callable(self.searchcallback):
            sel = ''
            if 0 <= self.searchlastkey[0] < 10:
                sel = str(self.cell_keyboard[self.searchtype][self.searchlastkey[0]][self.searchlastkey[1]])
            self.searchcallback(self.searchstring+sel)

    def searchTextDisplay(self):
        sel=''
        if 0 <= self.searchlastkey[0] < 10:
            sel = ' <font color="cyan">'+str(self.cell_keyboard[self.searchtype][self.searchlastkey[0]][self.searchlastkey[1]])+'</font>'
        self.searchlabel.setText('<font>'+' '.join(self.searchstring)+'</font>'+sel)

    @pyqtSlot(object)
    def searchKeyPressedAlpha(self, char):
        #A to Z only
        if 65<=ord(char[0])<=90:
            self.searchButtonPressedTimeout()
            self.searchstring += char[0]
            self.searchTextDisplay()
            self.callSearchCallback()

    @pyqtSlot(object)
    def searchButtonPressedNumber(self, index):
        timenow=time.time()
        if 0<=index<10:
            if len(self.cell_keyboard[self.searchtype][index])==1:
                self.searchstring += str(self.cell_keyboard[self.searchtype][index])
            else:
                if index==self.searchlastkey[0]:
                    if timenow-self.searchresponsetime<self.searchthreshold:
                        self.searchlastkey[1]=(self.searchlastkey[1]+1)%len(self.cell_keyboard[self.searchtype][index])
                    else:
                        self.searchstring += str(self.cell_keyboard[self.searchtype][self.searchlastkey[0]][self.searchlastkey[1]])
                        self.searchlastkey[1]=0
                else:
                    if 0<=self.searchlastkey[0]<10:
                        self.searchstring += str(self.cell_keyboard[self.searchtype][self.searchlastkey[0]][self.searchlastkey[1]])
                    self.searchlastkey[0] = index
                    self.searchlastkey[1] = 0
            self.searchtimer.stop()
            self.searchtimer.start()
        self.searchresponsetime = timenow
        self.searchTextDisplay()
        self.callSearchCallback()

    @pyqtSlot()
    def searchButtonPressedTimeout(self):
        if 0 <= self.searchlastkey[0] < 10:
            self.searchstring += str(self.cell_keyboard[self.searchtype][self.searchlastkey[0]][self.searchlastkey[1]])
            self.searchlastkey[0] = -1
            self.searchTextDisplay()

    @pyqtSlot(object)
    def searchButtonPressedFunction(self, index):
        if index=='F1':
            self.searchenteroption.click()
        elif index=='F2':
            self.searchbackspaceoption.click()
        elif index=='F3':
            self.searchstring=''
            self.searchlastkey[0]=-1
            self.stopSearch()
            self.callSearchCallback()

    @pyqtSlot(object)
    def searchButtonPressedBackspace(self, index):
        if 0 <= self.searchlastkey[0] < 10:
            self.searchlastkey[0]=-1
        else:
            self.searchstring=self.searchstring[:-1]
        self.searchtimer.stop()
        self.searchTextDisplay()
        self.callSearchCallback()

    @pyqtSlot(object)
    def searchButtonPressedEnter(self, index):
        self.searchButtonPressedTimeout()
        self.stopSearch()
        self.callSearchCallback()





    def resizeEvent(self, QResizeEvent):
        super().resizeEvent(QResizeEvent)
        self.setSearchPos()
        self.setTextSize()

    def gotoPage(self, u_int):
        self.bglabel.setPixmap(self.backgroundimages[u_int])
        self.stackedlayout.setCurrentIndex(u_int)
        self.setTextSize()

    def setHeaders(self, options):
        for i, option in enumerate(self.functionoption):
            try:
                option.clicked.disconnect()
            except:
                pass
            if i in options.keys():
                try:
                    option.setText(options[i]['text'])
                    if callable(options[i]['func']):
                        option.clicked.connect(options[i]['func'])
                except:
                    print("Error",sys.exc_info())
            else:
                option.setText('')

    def setFooters(self, options):
        for i, option in enumerate(self.footeroption):
            try:
                option.clicked.disconnect()
            except:
                pass
            if i in options.keys():
                try:
                    option.setText(options[i]['text'])
                    if callable(options[i]['func']):
                        option.clicked.connect(options[i]['func'])
                except:
                    print("Error",sys.exc_info())
            else:
                option.setText('')
        if 'pagertext' in options.keys():
            self.pageroption.setText(options['pagertext'])
        else:
            self.pageroption.setText('')

    def setContents(self, screenNum, options):
        if 0 <= screenNum <= 2:
            self.gotoPage(screenNum)
            for i, option in enumerate(self.contentoption[screenNum]):
                try:
                    option.clicked.disconnect()
                except:
                    pass
                if i in options.keys():
                    try:
                        option.setText(options[i]['text'])
                        if callable(options[i]['func']):
                            option.clicked.connect(options[i]['func'])
                            option.connect=options[i]['func']
                    except:
                        print("Error",sys.exc_info())
                else:
                    option.setText('')

            for i, option in enumerate(self.contentimage[screenNum]):
                try:
                    option.clicked.disconnect()
                except:
                    pass
                if i in options.keys():
                    try:
                        qp=QPixmap(options[i]['image'])
                        if qp.isNull():
                            option.setPixmap(self.nosingerimage)
                        else:
                            option.setPixmap(qp)
                    except:
                        option.setPixmap(self.nosingerimage)
                    try:
                        if callable(options[i]['func']):
                            option.clicked.connect(options[i]['func'])
                    except:
                        print("Error", sys.exc_info())
                else:
                    option.clear()


    def setBackCallback(self, backcallback):
        try:
            self.backoption.clicked.disconnect()
        except:
            pass
        try:
            if callable(backcallback):
                self.backoption.clicked.connect(backcallback)
        except:
            print("Error", sys.exc_info())

    def setStatusText(self, p_str):
        self.statustext=p_str
        if not self.timer.isActive():
            self.statusframe.setText(p_str)

    def setTempStatusText(self, p_str, msec):
        if self.timer.isActive():
            self.timer.stop()
        self.timer.setSingleShot(True)
        self.timer.start(msec)

        self.statusframe.setText(p_str)
        self.statusframe.x = 0
        self.statusframe.paused=True
        self.statusframe.repaint()

    @pyqtSlot()
    def setOldStatusText(self):
        self.statusframe.setText(self.statustext)
        self.statusframe.paused=False


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

    # def event(self, event):
    #     if event.type() == QEvent.Enter:
    #         self.paused = True
    #     elif event.type() == QEvent.Leave:
    #         self.paused = False
    #     return super().event(event)

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
    clicked = pyqtSignal(object)
    index = None

    def __init__(self, parent=None):
        super().__init__(parent)

    def mousePressEvent(self, QMouseEvent):
        self.click()

    def click(self):
        try:
            self.clicked.emit(self.index)
        except:
            print(sys.exc_info())


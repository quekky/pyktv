import sys
from PyQt5.QtCore import QTimer, pyqtSignal, pyqtSlot, Qt
from PyQt5.QtGui import QPixmap, QFont, QTextDocument, QFontMetrics, QPainter
from PyQt5.QtWidgets import QWidget, QLabel, QSizePolicy, QHBoxLayout, qApp, QVBoxLayout, QMenu, QStackedLayout, QGridLayout, QStyle
import time

import playlist
import settings
import screen


def setZeroMargins(layout):
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    return layout


class CommonWindow(QWidget):
    """Common window for both windows"""

    def contextMenuEvent(self, QContextMenuEvent):
        func=lambda f: (lambda: settings.ignoreInputKey or f())
        """Right click"""
        menu = QMenu(self)
        menu.addAction(self.style().standardIcon(QStyle.SP_DirHomeIcon), _('Main Menu'), func(self.gohome))
        menu.addAction(self.style().standardIcon(QStyle.SP_ArrowBack), _('Back'), func(settings.selectorWindow.backoption.click))
        menu.addAction(self.style().standardIcon(QStyle.SP_FileDialogDetailedView), _('F3:Playlist'), func(screen.playelistSearch))
        menu.addSeparator()
        menu.addAction(_('Index'), func(screen.indexSearch))
        menu.addAction(_('Title'), func(screen.titleSearch))
        menu.addAction(_('Artist'), func(screen.artistSearch1))
        menu.addAction(_('Language'), func(screen.langSearch1))
        menu.addAction(_('Category'), func(screen.categorySearch1))
        menu.addAction(_('Char number'), func(screen.charSearch1))
        menu.addAction(_('Youtube'), func(screen.youtubeScreen1))
        menu.addSeparator()
        menu.addAction(self.style().standardIcon(QStyle.SP_DialogCloseButton), _("Quit"), qApp.quit)
        action = menu.exec_(self.mapToGlobal(QContextMenuEvent.pos()))

    def keyReleaseEvent(self, QKeyEvent):
        """Key press"""
        key = QKeyEvent.key()
        if not settings.ignoreInputKey:
            #keys affecting selector screen
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
                    # settings.selectorWindow.contentoption[0][index].click()
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
            if key == Qt.Key_F12:
                self.gohome()
        #keys affecting video
        if key == Qt.Key_Space:
            settings.selectorWindow.switchchannel.click()
        elif key == Qt.Key_F10:
            settings.selectorWindow.playnextsong.click()
        elif key == Qt.Key_Plus:
            settings.selectorWindow.pitchup.click()
        elif key == Qt.Key_Minus:
            settings.selectorWindow.pitchdown.click()
        elif key == Qt.Key_Equal:
            settings.selectorWindow.pitchflat.click()

    def closeEvent(self, QCloseEvent):
        settings.mpvMediaPlayer.terminate()
        qApp.quit()

    def gohome(self):
        settings.selectorWindow.stopSearch()
        settings.selectorWindow.homeoption.click()


class VideoWindow(CommonWindow):
    """Video window"""

    timer=QTimer()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Video")

        self.timer.timeout.connect(self.stopStatusTempText)

        self.bglabel = QLabel()
        self.backgroundimage = QPixmap(settings.themeDir + "video.jpg")
        self.bglabel.setScaledContents(True)
        self.bglabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.bglabel.setPixmap(self.backgroundimage)

        self.bglayout = setZeroMargins(QHBoxLayout(self))
        self.bglayout.addWidget(self.bglabel)

        self.videoframe = self.bglabel

        settings.mpvMediaPlayer.wid = int(self.videoframe.winId())

        self.globalfont = QFont()
        self.statuslabel = QLabel(self)
        self.statuslabel.setStyleSheet('color:' + settings.config['font.color'] + '; background:black')
        self.statuslabel.hide()

        self.show()
        geo=list(map(int, settings.config['video.window'].split(',')))
        self.move(geo[0], geo[1])
        self.resize(geo[2], geo[3])
        if settings.config.getboolean('video.frameless'): self.setWindowFlag(Qt.FramelessWindowHint)
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

        self.globalfont=QFont()
        self.fontcolor=settings.config['font.color']
        self.fontstylesheet = 'color: ' + self.fontcolor + ';'
        self.nosingerimage = QPixmap(settings.themeDir + 'default_singer.jpg')

        self.timer.timeout.connect(self.setOldStatusText)

        self.createLayout()

        self.show()
        geo=list(map(int, settings.config['selector.window'].split(',')))
        self.move(geo[0], geo[1])
        self.resize(geo[2], geo[3])
        if settings.config.getboolean('selector.frameless'): self.setWindowFlag(Qt.FramelessWindowHint)
        if settings.config.getboolean('selector.fullscreen'): self.setWindowState(Qt.WindowFullScreen)


    def createLayout(self):
        # background image
        self.bglabel = QLabel()
        self.bglabel.setScaledContents(True)
        self.bglabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.bglabel.setPixmap(QPixmap(settings.themeDir + 'selector.jpg'))
        self.bglayout = setZeroMargins(QHBoxLayout(self))
        self.bglayout.addWidget(self.bglabel)

        # create the vertical frame
        self.vlayout = setZeroMargins(QVBoxLayout(self.bglabel))

        # create the function buttons
        self.functionlayout = setZeroMargins(QHBoxLayout())
        self.functionoption = []
        self.functionlayout.addStretch(30)
        for i in range(4):
            self.functionoption.append(QLabelListButton())
            self.functionoption[i].setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            self.functionoption[i].setLabelText('F'+str(i+1))
            self.functionoption[i].index = "F"+str(i+1)
            self.functionlayout.addWidget(self.functionoption[i], 100)
            self.functionlayout.addStretch(20)
        self.functionlayout.addStretch(10)

        # create the content area, with 2 stacks
        self.contentoption = [[], []]
        self.contentlayout = []
        self.vcontentlayout = setZeroMargins(QHBoxLayout())
        self.stackedlayout = QStackedLayout()
        for i in range(2):
            self.stackedlayout.addWidget(QLabel())
        self.vcontentlayout.addStretch(1)
        self.vcontentlayout.addLayout(self.stackedlayout, 10)
        self.vcontentlayout.addStretch(1)

        # create 1st page of content (10 options vertically align)
        self.contentlayout.append(setZeroMargins(QVBoxLayout(self.stackedlayout.widget(0))))
        for i in range(10):
            btn=QLabelListButton()
            self.contentoption[0].append(btn)
            btn.setLabelText(str((i+1) % 10))
            btn.index=i
            self.contentlayout[0].addWidget(btn)

        # create 2nd page of content (10 image options in 5x2)
        self.contentlayout.append(setZeroMargins(QGridLayout(self.stackedlayout.widget(1))))
        for i in range(10):
            btn=QLabeImageButton()
            self.contentoption[1].append(btn)
            btn.setLabelText(str((i+1) % 10))
            btn.index=i
            self.contentlayout[1].addWidget(btn, i / 5, i % 5)

        self.stackedlayout.setCurrentIndex(1)

        # create footer
        self.pageroption = QLabel()
        self.pageroption.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.pageroption.setStyleSheet(self.fontstylesheet)
        self.pageroption.setAlignment(Qt.AlignCenter)

        self.statusframe = QMarquee()
        self.statusframe.setFontColor(self.fontcolor)


        # add contents to vlayout
        self.vlayout.addStretch(20)
        self.vlayout.addLayout(self.functionlayout, 15)
        self.vlayout.addStretch(5)
        self.vlayout.addLayout(self.vcontentlayout, 200)
        self.vlayout.addStretch(5)
        self.vlayout.addWidget(self.pageroption, 15)
        self.vlayout.addStretch(10)
        self.vlayout.addWidget(self.statusframe, 20)


        # create hidden buttons for keypress
        self.homeoption = QLabelButton()
        self.homeoption.clicked.connect(screen.startHomeScreen)
        self.backoption = QLabelButton()
        #pageup/pagedown
        self.footeroption = [QLabelButton(), QLabelButton()]

        self.switchchannel = QLabelButton()
        self.switchchannel.clicked.connect(playlist.switchChannel)
        self.playnextsong = QLabelButton()
        self.playnextsong.clicked.connect(playlist.playNextSong)
        self.pitchup = QLabelButton()
        self.pitchup.clicked.connect(playlist.setPitchUp)
        self.pitchdown = QLabelButton()
        self.pitchdown.clicked.connect(playlist.setPitchDown)
        self.pitchflat = QLabelButton()
        self.pitchflat.clicked.connect(playlist.setPitchFlat)


        # done
        self.createSearchLayout()


    def setTextSize(self):
        """resize text size to label height"""
        self.globalfont.setPixelSize(self.functionoption[0].size().height() * 0.7)
        for option in self.functionoption + [self.pageroption]:
            option.setFont(self.globalfont)
        self.contentlayout[0].setSpacing(self.size().height()*0.01)
        self.contentlayout[1].setSpacing(self.size().height()*0.03)
        self.globalfont.setPixelSize(self.contentoption[0][0].size().height()*0.4)
        for option in self.contentoption[0]:
            option.setFont(self.globalfont)
        self.globalfont.setPixelSize(self.pageroption.size().height() * 0.7)
        self.pageroption.setFont(self.globalfont)
        self.statusframe.setPixelSize(self.statusframe.size().height()*0.7)

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
                    settings.logger.printException()
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
                    settings.logger.printException()
            else:
                option.setText('')
        if 'pagertext' in options.keys():
            self.pageroption.setText(options['pagertext'])
        else:
            self.pageroption.setText('')

    def setContents(self, screenNum, options):
        if 0 <= screenNum <= 1:
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
                        if isinstance(option, QLabeImageButton):
                            try:
                                qp=QPixmap(options[i]['image'])
                                if qp.isNull():
                                    option.setPixmap(self.nosingerimage)
                                else:
                                    option.setPixmap(qp)
                            except:
                                option.setPixmap(self.nosingerimage)
                    except:
                        settings.logger.printException()
                else:
                    option.setText('')
                    if isinstance(option, QLabeImageButton):
                        option.clearPixmap()


    def setBackCallback(self, backcallback):
        try:
            self.backoption.clicked.disconnect()
        except:
            pass
        try:
            if callable(backcallback):
                self.backoption.clicked.connect(backcallback)
        except:
            settings.logger.printException()

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
    index = None

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)

    def mousePressEvent(self, QMouseEvent):
        self.click()

    def click(self):
        try:
            self.clicked.emit(self.index)
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

        self.label = QLabel(self)
        self.label.move(0, 0)
        self.label.setAlignment(Qt.AlignCenter)
        self.text = QLabel(self)
        self.text.setStyleSheet(self.fontstylesheet+'border-radius: 8px; background-color: qlineargradient(spread:pad, x1:0, x2:1, stop:0 rgba(0, 0, 0, 200), stop:1 rgba(120, 120, 120, 50));padding:2px 0px;')

    def setText(self, p_str):
        self.text.setText(p_str)

    def setLabelText(self, p_str):
        self.label.setText(p_str)

    def setTextSize(self):
        labelwidth=int(self.height()*0.9);
        self.label.resize(labelwidth, labelwidth)
        self.label.setStyleSheet('color: white; border-radius: '+str(labelwidth/2-0.5)+'px; font: bold '+str(int(self.height()*0.7))+'px;padding:0px 4px 4px 0px;'
                                 'background-color: qradialgradient(spread:pad, cx:0.272, cy:0.354515, radius:0.848, fx:0.186, fy:0.256117, stop:0 rgba(220, 220, 220, 255), stop:0.2 rgba(200, 20, 20, 255), stop:1 rgba(20, 0, 0, 220));')

        self.text.move(self.height(), 0)
        self.text.resize(self.width() - self.height(), self.height())
        self.globalfont.setPixelSize(self.height() * 0.7)
        self.text.setFont(self.globalfont)

    def resizeEvent(self, *args, **kwargs):
        super().resizeEvent(*args, **kwargs)
        self.setTextSize()


class QLabeImageButton(QLabelButton):
    """Image and text"""

    def __init__(self, parent=None, havesub=False):
        super().__init__(parent)
        self.fontcolor = settings.config['font.color']
        self.fontstylesheet = 'color: ' + self.fontcolor + ';'
        self.globalfont = QFont()
        self.havesub = havesub

        self.text = QLabel(self)
        self.text.setStyleSheet(self.fontstylesheet+'border-bottom-left-radius: 18px; border-bottom-right-radius: 18px; background-color: qlineargradient(spread:pad, y1:0, y2:1, stop:0 rgba(0, 0, 0, 230), stop:1 rgba(120, 120, 120, 120));padding: 0px;')
        self.text.setAlignment(Qt.AlignCenter)
        self.text.setText('testing')
        self.image = QLabel(self)
        self.image.setScaledContents(True)
        self.image.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.image.setStyleSheet('background-color: qlineargradient(spread:pad, x1:1, y1:0.8, x2:0, y2:0.1, stop:0.00564972 rgba(186, 225, 255, 255), stop:0.4 rgba(255, 255, 255, 230), stop:0.6 rgba(255, 255, 255, 180), stop:1 rgba(134, 203, 255, 120));')
        self.label = QLabel(self)
        self.label.setAlignment(Qt.AlignCenter)

    def setText(self, p_str):
        self.text.setText(p_str)

    def setLabelText(self, p_str):
        self.label.setText(p_str)

    def setPixmap(self, QPixmap):
        self.image.setPixmap(QPixmap)

    def clearPixmap(self):
        self.image.clear()

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

    def resizeEvent(self, *args, **kwargs):
        super().resizeEvent(*args, **kwargs)
        self.setTextSize()


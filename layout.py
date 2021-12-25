from PyQt5.QtGui import QKeySequence, QCursor, QImage
from PyQt5.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QMenu, QStackedLayout, QShortcut, qApp
import time

import playlist
import screen
from functions import setZeroMargins, Hangul, get_ip
from pywidgets import *
import qrcode
import webapp



# raise the correct window
selectorshowntime = 0
raisewindowtimer = QTimer()
raisewindowtimer.setInterval(1000)

def raiseSelectorWindow():
    global selectorshowntime, raisewindowtimer
    selectorshowntime=time.time()
    settings.selectorWindow.raise_()
    raisewindowtimer.timeout.connect(raiseVideoWindow)
    raisewindowtimer.start()

def raiseVideoWindow():
    global selectorshowntime, raisewindowtimer
    #after some time, raise the video in front of selector
    if time.time()-15 > selectorshowntime:
        raisewindowtimer.stop()
        settings.videoWindow.raise_()


class CommonWindow(QWidget):
    """Common window for both windows"""

    ignore_keys=[]
    def getQKeySequence(self, key):
        if key.startswith('0x'):
            try:
                key = int(key, 16)
            except ValueError:
                pass
        seq = QKeySequence(key)
        s = seq.toString()
        if len(s)==1 and s.isalpha():
            self.ignore_keys.append(ord(s))
        return seq


    def __init__(self):
        super().__init__()
        # map keyboard shortcuts
        for key in settings.keyboardshortcut.get('Home','').split('|'):
            QShortcut(self.getQKeySequence(key), self, self.key_home)
        for key in settings.keyboardshortcut.get('Backspace','').split('|'):
            QShortcut(self.getQKeySequence(key), self, self.key_backspace)
        for key in settings.keyboardshortcut.get('Enter','').split('|'):
            QShortcut(self.getQKeySequence(key), self, self.key_enter)
        for key in settings.keyboardshortcut.get('PageUp','').split('|'):
            QShortcut(self.getQKeySequence(key), self, self.key_pageup)
        for key in settings.keyboardshortcut.get('PageDown','').split('|'):
            QShortcut(self.getQKeySequence(key), self, self.key_pagedown)
        for key in settings.keyboardshortcut.get('F1','').split('|'):
            QShortcut(self.getQKeySequence(key), self, self.key_F1)
        for key in settings.keyboardshortcut.get('F2','').split('|'):
            QShortcut(self.getQKeySequence(key), self, self.key_F2)
        for key in settings.keyboardshortcut.get('F3','').split('|'):
            QShortcut(self.getQKeySequence(key), self, self.key_F3)
        for key in settings.keyboardshortcut.get('F4','').split('|'):
            QShortcut(self.getQKeySequence(key), self, self.key_F4)

        for key in settings.keyboardshortcut.get('switchchannel','').split('|'):
            QShortcut(self.getQKeySequence(key), self, playlist.switchChannel)
        for key in settings.keyboardshortcut.get('playnextsong','').split('|'):
            QShortcut(self.getQKeySequence(key), self, playlist.playNextSong)
        for key in settings.keyboardshortcut.get('pitchup','').split('|'):
            QShortcut(self.getQKeySequence(key), self, playlist.setPitchUp)
        for key in settings.keyboardshortcut.get('pitchflat','').split('|'):
            QShortcut(self.getQKeySequence(key), self, playlist.setPitchFlat)
        for key in settings.keyboardshortcut.get('pitchdown','').split('|'):
            QShortcut(self.getQKeySequence(key), self, playlist.setPitchDown)

        for key in settings.keyboardshortcut.get('jumpforward','').split('|'):
            QShortcut(self.getQKeySequence(key), self, playlist.jumpForward).setAutoRepeat(True)
        for key in settings.keyboardshortcut.get('jumpbackward','').split('|'):
            QShortcut(self.getQKeySequence(key), self, playlist.jumpBackward).setAutoRepeat(True)
        for key in settings.keyboardshortcut.get('playpause','').split('|'):
            QShortcut(self.getQKeySequence(key), self, playlist.playpause)


    def contextMenuEvent(self, QContextMenuEvent):
        func=lambda f: (lambda: settings.ignoreInputKey or f())
        """Right click"""
        menu = QMenu(self)
        menu.addAction(self.style().standardIcon(QStyle.SP_DirHomeIcon), _('Main Menu'), func(self.key_home))
        menu.addAction(self.style().standardIcon(QStyle.SP_ArrowBack), _('Back'), func(self.key_backspace))
        menu.addAction(self.style().standardIcon(QStyle.SP_FileDialogDetailedView), _('F3:Playlist'), func(screen.playlistSearch))
        menu.addSeparator()
        menu.addAction(_('Index'), func(screen.indexSearch))
        menu.addAction(_('Title'), func(screen.titleSearch))
        menu.addAction(_('Artist'), func(screen.artistSearch1))
        menu.addAction(_('Language'), func(screen.langSearch1))
        menu.addAction(_('Category'), func(screen.categorySearch1))
        menu.addAction(_('Char number'), func(screen.charSearch1))
        menu.addAction(_('Local Network'), func(screen.networkSearch1))
        menu.addAction(_('Youtube'), func(screen.youtubeScreen1))
        menu.addSeparator()
        menu.addAction(self.style().standardIcon(QStyle.SP_DialogCloseButton), _("Quit"), qApp.quit)
        action = menu.exec_(self.mapToGlobal(QContextMenuEvent.pos()))

    prevtime=0
    def keyReleaseEvent(self, QKeyEvent):
        """Key press"""
        key = QKeyEvent.key()

        # if modifier is pressed, ignore the key
        now = time.time()
        if now-self.prevtime<=1 or QKeyEvent.modifiers()!=Qt.NoModifier:
            return
        if key in (Qt.Key_Shift,Qt.Key_Control,Qt.Key_Meta,Qt.Key_Alt):
            self.prevtime=now

        if not settings.ignoreInputKey:
            #keys affecting selector screen
            if settings.selectorWindow.insearch:
                if Qt.Key_0 <= key <= Qt.Key_9:
                    raiseSelectorWindow()
                    index = key - Qt.Key_0 - 1
                    if index == -1: index = 9
                    settings.selectorWindow.searchcontentoption[index].click()
                if (Qt.Key_A <= key <= Qt.Key_Z) and key not in self.ignore_keys:
                    raiseSelectorWindow()
                    index = key
                    settings.selectorWindow.searchKeyPressedAlpha(chr(index))
            else:
                if Qt.Key_0 <= key <= Qt.Key_9:
                    raiseSelectorWindow()
                    index=key-Qt.Key_0-1
                    if index==-1: index=9
                    settings.selectorWindow.contentoption[settings.selectorWindow.stackedlayout.currentIndex()][index].click()


    @staticmethod
    def key_home():
        if not settings.ignoreInputKey:
            raiseSelectorWindow()
            settings.selectorWindow.stopSearch()
            settings.selectorWindow.homeoption.click()

    @staticmethod
    def key_backspace():
        if not settings.ignoreInputKey:
            raiseSelectorWindow()
            if settings.selectorWindow.insearch:
                settings.selectorWindow.searchbackspaceoption.click()
            else:
                settings.selectorWindow.backoption.click()

    @staticmethod
    def key_enter():
        if not settings.ignoreInputKey:
            if settings.selectorWindow.insearch:
                raiseSelectorWindow()
                settings.selectorWindow.searchenteroption.click()

    @staticmethod
    def key_pageup():
        if not settings.ignoreInputKey:
            if not settings.selectorWindow.insearch:
                raiseSelectorWindow()
                settings.selectorWindow.footeroption[0].click()

    @staticmethod
    def key_pagedown():
        if not settings.ignoreInputKey:
            if not settings.selectorWindow.insearch:
                raiseSelectorWindow()
                settings.selectorWindow.footeroption[1].click()

    @staticmethod
    def key_F1():
        if not settings.ignoreInputKey:
            raiseSelectorWindow()
            if settings.selectorWindow.insearch:
                settings.selectorWindow.searchfunctionoption[0].click()
            else:
                settings.selectorWindow.functionoption[0].click()

    @staticmethod
    def key_F2():
        if not settings.ignoreInputKey:
            raiseSelectorWindow()
            if settings.selectorWindow.insearch:
                settings.selectorWindow.searchfunctionoption[1].click()
            else:
                settings.selectorWindow.functionoption[1].click()

    @staticmethod
    def key_F3():
        if not settings.ignoreInputKey:
            raiseSelectorWindow()
            if settings.selectorWindow.insearch:
                settings.selectorWindow.searchfunctionoption[2].click()
            else:
                settings.selectorWindow.functionoption[2].click()

    @staticmethod
    def key_F4():
        if not settings.ignoreInputKey:
            raiseSelectorWindow()
            if settings.selectorWindow.insearch:
                settings.selectorWindow.searchfunctionoption[3].click()
            else:
                settings.selectorWindow.functionoption[3].click()


    def closeEvent(self, QCloseEvent):
        settings.mpvMediaPlayer.terminate()
        webapp.__shutdown__()
        qApp.quit()


class QRImage(qrcode.image.base.BaseImage):
    def new_image(self, **kwargs):
        image = QImage(self.pixel_size, self.pixel_size, QImage.Format_RGB16)
        image.fill(Qt.white)
        return image

    def pixmap(self):
        return QPixmap.fromImage(self._img)

    def drawrect(self, row, col):
        painter = QPainter(self._img)
        painter.fillRect(
            (col + self.border) * self.box_size,
            (row + self.border) * self.box_size,
            self.box_size, self.box_size,
            Qt.black)


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

        self.qrcodelabel = QLabel(self)
        self.qrcodelabel.hide()
        self.qrcodelabel.setScaledContents(True)
        self.qrcodelabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        print(get_ip())
        qr_image = qrcode.make("http://"+get_ip()+":5000", image_factory=QRImage, border=0).pixmap()
        self.qrcodelabel.setPixmap(qr_image)
        self.qrcodelabel.show()

        self.setCursor(QCursor(Qt.BlankCursor))

        geo=list(map(int, settings.config['video.window'].split(',')))
        if settings.config.getboolean('video.frameless'): self.setWindowFlag(Qt.FramelessWindowHint)
        self.move(geo[0], geo[1])
        self.show()
        self.resize(geo[2], geo[3])
        if settings.config.getboolean('video.fullscreen'): self.setWindowState(Qt.WindowFullScreen)

    def resizeEvent(self, QResizeEvent):
        super().resizeEvent(QResizeEvent)
        height=self.height()
        width=self.width()
        self.globalfont.setPixelSize(height*0.03)
        self.statuslabel.move(width*0.01, height*0.01)
        self.statuslabel.setFont(self.globalfont)
        self.statuslabel.adjustSize()
        qrwidth=width*0.05
        self.qrcodelabel.move(width*0.994-qrwidth, height*0.01)
        self.qrcodelabel.setFixedWidth(qrwidth)
        self.qrcodelabel.setFixedHeight(qrwidth)

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

        geo=list(map(int, settings.config['selector.window'].split(',')))
        if settings.config.getboolean('selector.frameless'): self.setWindowFlag(Qt.FramelessWindowHint)
        self.move(geo[0], geo[1])
        self.show()
        self.resize(geo[2], geo[3])
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

        # create the header toolbar
        self.headerlayout = setZeroMargins(QHBoxLayout())
        self.headeroption = []

        self.homeoption = QLabelButton()
        self.homeoption.clicked.connect(screen.startHomeScreen)
        self.homeoption.setScaledContents(True)
        self.homeoption.setPixmap(QPixmap(settings.themeDir + 'buttons/home.png'))
        self.headeroption.append(self.homeoption)
        self.backoption = QLabelButton()
        self.backoption.setScaledContents(True)
        self.backoption.setPixmap(QPixmap(settings.themeDir + 'buttons/arrow-left.png'))
        self.headeroption.append(self.backoption)

        self.switchchannel = QLabelButton()
        self.switchchannel.clicked.connect(playlist.switchChannel)
        self.switchchannel.setScaledContents(True)
        self.switchchannel.setPixmap(QPixmap(settings.themeDir + 'buttons/music.png'))
        self.headeroption.append(self.switchchannel)
        self.playnextsong = QLabelButton()
        self.playnextsong.clicked.connect(playlist.playNextSong)
        self.playnextsong.setScaledContents(True)
        self.playnextsong.setPixmap(QPixmap(settings.themeDir + 'buttons/step-forward.png'))
        self.headeroption.append(self.playnextsong)
        self.pitchup = QLabelButton()
        self.pitchup.clicked.connect(playlist.setPitchUp)
        self.pitchup.setText('♭')
        self.headeroption.append(self.pitchup)
        self.pitchflat = QLabelButton()
        self.pitchflat.clicked.connect(playlist.setPitchFlat)
        self.pitchflat.setText('♮')
        self.headeroption.append(self.pitchflat)
        self.pitchdown = QLabelButton()
        self.pitchdown.clicked.connect(playlist.setPitchDown)
        self.pitchdown.setText('♯')
        self.headeroption.append(self.pitchdown)

        for opt in self.headeroption:
            opt.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            opt.setAlignment(Qt.AlignCenter)
            opt.setStyleSheet('color: white; font-weight: 800; border-radius: 3px; background-color: rgba(120, 120, 120, 40);')

        self.headerlayout.addStretch(2)
        self.headerlayout.addWidget(self.homeoption, 4)
        self.headerlayout.addStretch(2)
        self.headerlayout.addWidget(self.backoption, 4)
        self.headerlayout.addStretch(100)
        self.headerlayout.addWidget(self.playnextsong, 4)
        self.headerlayout.addStretch(2)
        self.headerlayout.addWidget(self.switchchannel, 4)
        self.headerlayout.addStretch(5)
        self.headerlayout.addWidget(self.pitchup, 4)
        self.headerlayout.addStretch(2)
        self.headerlayout.addWidget(self.pitchflat, 4)
        self.headerlayout.addStretch(2)
        self.headerlayout.addWidget(self.pitchdown, 4)
        self.headerlayout.addStretch(2)



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
        self.stackedlayout = QStackedLayout()
        for i in range(2):
            self.stackedlayout.addWidget(QLabel())

        # create 1st page of content (10 options vertically align)
        self.vcontentlayout1 = setZeroMargins(QHBoxLayout(self.stackedlayout.widget(0)))
        self.contentlayout.append(setZeroMargins(QVBoxLayout()))
        for i in range(10):
            btn=QLabelListButton()
            self.contentoption[0].append(btn)
            btn.setLabelText(str((i+1) % 10))
            btn.index=i
            self.contentlayout[0].addWidget(btn)
        self.vcontentlayout1.addStretch(1)
        self.vcontentlayout1.addLayout(self.contentlayout[0], 10)
        self.vcontentlayout1.addStretch(1)

        # create 2nd page of content (10 image options in 5x2)
        self.vcontentlayout2 = setZeroMargins(QHBoxLayout(self.stackedlayout.widget(1)))
        self.contentlayout.append(setZeroMargins(QGridLayout(self.stackedlayout.widget(1))))
        for i in range(10):
            btn=QLabeImageButton()
            self.contentoption[1].append(btn)
            btn.setLabelText(str((i+1) % 10))
            btn.index=i
            self.contentlayout[1].addWidget(btn, i / 5, i % 5)
        self.vcontentlayout2.addStretch(1)
        self.vcontentlayout2.addLayout(self.contentlayout[1], 15)
        self.vcontentlayout2.addStretch(1)

        self.stackedlayout.setCurrentIndex(1)


        # create footer
        self.footerlayout = setZeroMargins(QHBoxLayout())

        self.pageroption = QLabel()
        self.pageroption.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.pageroption.setStyleSheet(self.fontstylesheet)
        self.pageroption.setAlignment(Qt.AlignCenter)

        #pageup/pagedown
        self.footeroption = [QLabelButton(), QLabelButton()]
        for opt in self.footeroption:
            opt.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            opt.setAlignment(Qt.AlignCenter)
            opt.setStyleSheet(self.fontstylesheet)

        self.footerlayout.addStretch(50)
        self.footerlayout.addWidget(self.footeroption[0], 10)
        self.footerlayout.addStretch(10)
        self.footerlayout.addWidget(self.pageroption, 20)
        self.footerlayout.addStretch(10)
        self.footerlayout.addWidget(self.footeroption[1], 10)
        self.footerlayout.addStretch(50)


        # status bar
        self.statusframe = QMarquee()
        self.statusframe.setFontColor(self.fontcolor)


        # add contents to vlayout
        self.vlayout.addStretch(3)
        self.vlayout.addLayout(self.headerlayout, 12)
        self.vlayout.addStretch(10)
        self.vlayout.addLayout(self.functionlayout, 15)
        self.vlayout.addStretch(5)
        self.vlayout.addLayout(self.stackedlayout, 200)
        self.vlayout.addStretch(5)
        self.vlayout.addLayout(self.footerlayout, 15)
        self.vlayout.addStretch(10)
        self.vlayout.addWidget(self.statusframe, 20)


        # done
        self.createSearchLayout()


    def setTextSize(self):
        """resize text size to label height"""
        self.globalfont.setPixelSize(self.headeroption[0].size().height())
        for option in self.headeroption:
            option.setFont(self.globalfont)
        self.globalfont.setPixelSize(self.functionoption[0].size().height() * 0.7)
        for option in self.functionoption:
            option.setFont(self.globalfont)
        self.contentlayout[0].setSpacing(self.size().height()*0.01)
        self.contentlayout[1].setSpacing(self.size().height()*0.03)
        self.globalfont.setPixelSize(self.contentoption[0][0].size().height()*0.4)
        for option in self.contentoption[0]:
            option.setFont(self.globalfont)
        self.globalfont.setPixelSize(self.pageroption.size().height() * 0.7)
        self.pageroption.setFont(self.globalfont)
        for option in self.footeroption:
            option.setFont(self.globalfont)
        self.statusframe.setPixelSize(self.statusframe.size().height()*0.7)

        if self.searchbg.isVisible():
            self.setSearchTextSize()


    """
    search functions
    """

    insearch=False
    numstylesheet='<span style="color:#999999">'
    search_display = {
        0: [
            ['EN', ('1', 'ABC2', 'DEF3', 'GHI4', 'JKL5', 'MNO6', 'PQRS7', 'TUV8', 'WXYZ9', '0')],
            ['JP', (numstylesheet+'1:</span> あ', numstylesheet+'2:</span> か', numstylesheet+'3:</span> さ',
                    numstylesheet+'4:</span> た', numstylesheet+'5:</span> な', numstylesheet+'6:</span> は',
                    numstylesheet+'7:</span> ま', numstylesheet+'8:</span> や', numstylesheet+'9:</span> ら',
                    numstylesheet+'0:</span> わ')],
            ['KR', (numstylesheet+'1:</span> ㅣ', numstylesheet+'2:</span> ㆍ', numstylesheet+'3:</span> ㅡ',
                    numstylesheet+'4:</span> ㄱㅋ', numstylesheet+'5:</span> ㄴㄹ', numstylesheet+'6:</span> ㄷㅌ',
                    numstylesheet+'7:</span> ㅂㅍ', numstylesheet+'8:</span> ㅅㅎ', numstylesheet+'9:</span> ㅈㅊ',
                    numstylesheet+'0:</span> ㅇㅁ')]
          ],
       1: [['NUM', ('1', '2', '3', '4', '5', '6', '7', '8', '9', '0')]]
     }
    search_keyboard = {
        0: [
            ['EN', ('1', 'ABC2', 'DEF3', 'GHI4', 'JKL5', 'MNO6', 'PQRS7', 'TUV8', 'WXYZ9', '0')],
            ['JP', ('あいうえおぁぃぅぇぉ', 'かきくけこ', 'さしすせそ', 'たちつてとっ', 'なにぬねの', 'はひふへほ', 'まみむめも', 'やゆよゃゅょ', 'らりるれろ', 'わゐゑを')],
            ['KR', ('', '', '', 'ㄱㅋㄲ', 'ㄴㄹ', 'ㄷㅌㄸ', 'ㅂㅍㅃ', 'ㅅㅎㅆ', 'ㅈㅊㅉ', 'ㅇㅁ')]
          ],
       1: [['NUM', ('1', '2', '3', '4', '5', '6', '7', '8', '9', '0')]]
     }
    searchtype = 0
    searchindex = 0
    searchlastkey = [-1, 0]
    searchstring = ''
    searchthreshold = 2
    searchtimer = QTimer()
    searchcallback = None
    search_hangul = Hangul()


    def createSearchLayout(self):
        fontstylesheet=self.fontstylesheet
        btnstylesheet='color: white; border-radius: 5px;' + \
            'background-color: qradialgradient(spread:pad, cx:0.272, cy:0.354515, radius:0.848, fx:0.071, fy:0.199045, stop:0 rgba(130, 130, 130, 255), stop:0.2 rgba(101, 101, 101, 255), stop:1 rgba(27, 27, 27, 170));' + \
            'border: 1px solid #858585;border-right: 1px solid #414141;border-bottom: solid 3px #414141;'

        self.searchbg = QLabel(self)
        self.searchbg.setCursor(Qt.WaitCursor)

        self.searchbglayout = setZeroMargins(QGridLayout(self.searchbg))
        self.searchframe = QLabel()
        self.searchframe.setScaledContents(True)
        self.searchframe.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.searchimage = QPixmap(settings.themeDir + "search.jpg")
        self.searchframe.setCursor(Qt.ArrowCursor)
        self.searchframe.setPixmap(self.searchimage)
        self.searchbglayout.addWidget(QWidget(), 0, 1)
        self.searchbglayout.addWidget(QWidget(), 1, 0)
        self.searchbglayout.addWidget(QWidget(), 2, 1)
        self.searchbglayout.addWidget(QWidget(), 3, 0)
        self.searchbglayout.addWidget(self.searchframe, 1, 1)
        self.searchbglayout.setColumnStretch(0, 70)
        self.searchbglayout.setColumnStretch(1, 40)
        self.searchbglayout.setColumnStretch(2, 1)
        self.searchbglayout.setRowStretch(0, 3)
        self.searchbglayout.setRowStretch(1, 4)
        self.searchbglayout.setRowStretch(2, 1)

        self.searchlayout = QGridLayout(self.searchframe)
        self.searchlayout.setSpacing(10)

        # title
        self.searchtitle = QLabel()
        self.searchtitle.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.searchtitle.setStyleSheet(fontstylesheet+';font:bold;')
        self.searchtitle.setText(_("Search character:"))
        self.searchlayout.addWidget(self.searchtitle, 0, 0, 1, 2)

        # F1 to F4
        f_text=(_('F1: Ok'),_('F2: Del'),_('F3: Cancel'),_('F4: 🌐'))
        self.searchfunctionoption = []
        #create a filler "F4"
        for i in range(4):
            self.searchfunctionoption.append(QLabelButton())
            self.searchfunctionoption[i].setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            self.searchfunctionoption[i].setText(f_text[i])
            self.searchfunctionoption[i].setStyleSheet(btnstylesheet)
            self.searchfunctionoption[i].setAlignment(Qt.AlignCenter)
            self.searchfunctionoption[i].index="F" + str(i + 1)
            self.searchfunctionoption[i].clicked.connect(self.searchButtonPressedFunction)
        for i in range(3):
            self.searchlayout.addWidget(self.searchfunctionoption[i], 1 , i)
        self.searchlayout.addWidget(self.searchfunctionoption[3], 0, 2)

        # display text
        self.searchlabel = QLabel()
        self.searchlabel.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.searchlabel.setStyleSheet(fontstylesheet+"; padding: 0 10%; border: 1px solid blue;")
        self.searchlabel.setStyleSheet(self.fontstylesheet+'border: 3px solid black; border-radius: 5px; background-color: qlineargradient(spread:pad, x1:0, x2:1, stop:0 rgba(0, 0, 0, 200), stop:1 rgba(120, 120, 120, 100));padding: 0px 10%;')
        self.searchlayout.addWidget(self.searchlabel, 2, 0, 1, 3)

        # 0 -9
        self.searchcontentoption = []
        for i in range(10):
            self.searchcontentoption.append(QLabelButton())
            self.searchcontentoption[i].setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
            self.searchcontentoption[i].setStyleSheet(btnstylesheet)
            self.searchcontentoption[i].setAlignment(Qt.AlignCenter)
            self.searchcontentoption[i].index=i
            self.searchcontentoption[i].clicked.connect(self.searchButtonPressedNumber)
        for i in range(9):
            self.searchlayout.addWidget(self.searchcontentoption[i], 3+i/3, i%3)
        self.searchlayout.addWidget(self.searchcontentoption[9], 6, 1)

        # backspace
        self.searchbackspaceoption = QLabelButton()
        self.searchbackspaceoption.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.searchbackspaceoption.setStyleSheet(btnstylesheet)
        self.searchbackspaceoption.setAlignment(Qt.AlignCenter)
        self.searchbackspaceoption.setText("🡄")
        self.searchbackspaceoption.clicked.connect(self.searchButtonPressedBackspace)
        # self.searchlayout.addWidget(self.searchbackspaceoption, 6, 0)

        # enter
        self.searchenteroption = QLabelButton()
        self.searchenteroption.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Ignored)
        self.searchenteroption.setStyleSheet(btnstylesheet)
        self.searchenteroption.setAlignment(Qt.AlignCenter)
        self.searchenteroption.setText("[Enter]")
        self.searchenteroption.clicked.connect(self.searchButtonPressedEnter)
        # self.searchlayout.addWidget(self.searchenteroption, 6, 2)

        self.searchbg.hide()

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
        self.searchbackspaceoption.setFont(self.globalfont)
        self.searchenteroption.setFont(self.globalfont)
        self.globalfont.setPixelSize(self.searchtitle.size().height() * 0.9)
        self.searchtitle.setFont(self.globalfont)
        self.globalfont.setPixelSize(self.searchlabel.size().height() * 0.7)
        self.searchlabel.setFont(self.globalfont)


    def setSearchPos(self):
        if self.searchbg.isVisible():
            self.searchbg.setFixedSize(self.width(), self.height())

    def displaySearchNumbers(self):
        for i in range(10):
            self.searchcontentoption[i].setText(self.search_display[self.searchtype][self.searchindex][1][i])

    def startSearch(self, searchtype=0):
        """display the search bar

        searchtype:
            0=alphanumeric
            1=numbers only
        """
        self.insearch=True
        self.searchstring=''
        self.searchtype=searchtype
        self.searchindex=0
        self.search_hangul = Hangul()

        if len(self.search_keyboard[self.searchtype]) > 1:
            self.searchfunctionoption[3].show()
        else:
            self.searchfunctionoption[3].hide()

        self.displaySearchNumbers()
        self.searchbg.show()
        self.setSearchPos()
        self.setSearchTextSize()
        self.searchTextDisplay()
        self.callSearchCallback()

    def stopSearch(self):
        self.insearch=False
        self.searchbg.hide()

    def searchGetFinalString(self):
        searchstring=self.searchstring
        if self.searchlastkey[0]==-2:
            searchstring+=self.search_hangul.getHangul()
        elif 0 <= self.searchlastkey[0] < 10:
            searchstring+=self.search_keyboard[self.searchtype][self.searchindex][1][self.searchlastkey[0]][self.searchlastkey[1]]
        return searchstring

    def setSearchCallback(self, callback):
        self.searchcallback=callback

    def callSearchCallback(self):
        if callable(self.searchcallback):
            self.searchcallback(self.searchGetFinalString())

    def searchTextDisplay(self):
        searchstring=' '.join(self.searchGetFinalString())
        if self.searchlastkey[0]!=-1:
            searchstring=searchstring[:-1]+'<font color="cyan">' + searchstring[-1] + '</font>'
        self.searchlabel.setText(searchstring)


    @pyqtSlot(object)
    def searchKeyPressedAlpha(self, char):
        #A to Z only
        if 65<=ord(char[0])<=90:
            self.searchButtonPressedTimeout()
            self.searchstring += char[0]
            self.searchTextDisplay()
            self.callSearchCallback()

    def searchKoreanNumber(self, index):
        self.searchlastkey = [-2, 0]
        if 0 <= index <= 2: # Vowels
            if self.search_hangul.step == 2:
                self.searchstring += self.search_hangul.getHangul(1)
                self.search_hangul.chosung = self.search_hangul.jongsung
                self.search_hangul.jungsung = self.search_hangul.jongsung = self.search_hangul.jongsung2 = ""
            elif self.search_hangul.step == 3:
                self.searchstring += self.search_hangul.getHangul(2)
                self.search_hangul.chosung = self.search_hangul.jongsung2
                self.search_hangul.jungsung = self.search_hangul.jongsung = self.search_hangul.jongsung2 = ""

            beforedata = self.search_hangul.jungsung
            self.search_hangul.step = 1
            self.search_hangul.searchlastkey = [-1, 0]

            if index==0: # ㅣ ㅓ ㅕ ㅐ ㅔ ㅖ ㅒ ㅚ ㅟ ㅙ ㅝ ㅞ ㅢ
                if beforedata=="ㆍ": nowdata = "ㅓ"
                elif beforedata==":": nowdata = "ㅕ"
                elif beforedata=="ㅏ": nowdata = "ㅐ"
                elif beforedata=="ㅑ": nowdata = "ㅒ"
                elif beforedata=="ㅓ": nowdata = "ㅔ"
                elif beforedata=="ㅕ": nowdata = "ㅖ"
                elif beforedata=="ㅗ": nowdata = "ㅚ"
                elif beforedata=="ㅜ": nowdata = "ㅟ"
                elif beforedata=="ㅠ": nowdata = "ㅝ"
                elif beforedata=="ㅘ": nowdata = "ㅙ"
                elif beforedata=="ㅝ": nowdata = "ㅞ"
                elif beforedata=="ㅡ": nowdata = "ㅢ"
                else:
                    nowdata = "ㅣ"
            elif index==1: # ㆍ : ㅏ ㅑ ㅜ ㅠ ㅘ
                if beforedata=="ㆍ": nowdata = ":"
                elif beforedata==":": nowdata = "ㆍ"
                elif beforedata=="ㅣ": nowdata = "ㅏ"
                elif beforedata=="ㅏ": nowdata = "ㅑ"
                elif beforedata=="ㅡ": nowdata = "ㅜ"
                elif beforedata=="ㅜ": nowdata = "ㅠ"
                elif beforedata=="ㅚ": nowdata = "ㅘ"
                else:
                    nowdata = "ㆍ"
            elif index==2: # ㅡ ㅗ ㅛ
                if beforedata=="ㆍ": nowdata="ㅗ"
                elif beforedata==":": nowdata="ㅛ"
                else:
                    nowdata = "ㅡ"

            self.search_hangul.jungsung = nowdata

        elif 3 <= index <= 9: # Consonants
            if self.search_hangul.step == 1:
                if self.search_hangul.jungsung=="ㆍ" or self.search_hangul.jungsung==":":
                    self.search_hangul = Hangul()
                else:
                    self.search_hangul.step = 2

            if index==self.search_hangul.searchlastkey[0]:
                self.search_hangul.searchlastkey[1]=(self.search_hangul.searchlastkey[1]+1)%len(self.search_keyboard[self.searchtype][self.searchindex][1][index])
            else:
                self.search_hangul.searchlastkey = [index, 0]
                if self.search_hangul.step == 2 and self.search_hangul.jongsung:
                    self.search_hangul.step = 3
                elif self.search_hangul.step == 3:
                    self.searchstring += self.search_hangul.getHangul()
                    self.search_hangul = Hangul()

            nowdata = self.search_keyboard[self.searchtype][self.searchindex][1][index][self.search_hangul.searchlastkey[1]]
            if self.search_hangul.step==0:   self.search_hangul.chosung = nowdata
            elif self.search_hangul.step==2: self.search_hangul.jongsung = nowdata
            elif self.search_hangul.step==3: self.search_hangul.jongsung2 = nowdata


    def searchFindFromKeyboard(self, index):
        if 0<=index<10:
            if len(self.search_keyboard[self.searchtype][self.searchindex][1][index])==1:
                self.searchstring += str(self.search_keyboard[self.searchtype][self.searchindex][1][index])
            else:
                if index==self.searchlastkey[0]:
                    self.searchlastkey[1]=(self.searchlastkey[1]+1)%len(self.search_keyboard[self.searchtype][self.searchindex][1][index])
                else:
                    if self.searchlastkey[0]!=-1:
                        self.searchstring = self.searchGetJoinString()
                    self.searchlastkey = [index, 0, '']


    @pyqtSlot(object)
    def searchButtonPressedNumber(self, index):
        try:
            self.searchtimer.stop()
            if self.search_keyboard[self.searchtype][self.searchindex][0]=='KR':
                self.searchKoreanNumber(index)
            else:
                self.searchFindFromKeyboard(index)
            self.searchtimer.start()
        except:
            settings.logger.printException()
        self.searchTextDisplay()
        self.callSearchCallback()

    @pyqtSlot()
    def searchButtonPressedTimeout(self):
        self.searchtimer.stop()
        if self.searchlastkey[0]!=-1:
            self.searchstring = self.searchGetFinalString()
            self.searchlastkey = [-1, 0, '']
            self.search_hangul = Hangul()
            self.searchTextDisplay()

    @pyqtSlot(object)
    def searchButtonPressedFunction(self, index):
        if index=='F1':
            self.searchenteroption.click()
        elif index=='F2':
            self.searchbackspaceoption.click()
        elif index=='F3':
            self.searchstring=''
            self.searchlastkey = [-1, 0, '']
            self.searchenteroption.click()
        elif index == 'F4':
            self.searchButtonPressedTimeout()
            self.searchindex = (self.searchindex+1)%len(self.search_keyboard[self.searchtype])
            self.displaySearchNumbers()

    @pyqtSlot(object)
    def searchButtonPressedBackspace(self, index):
        self.searchtimer.stop()
        if self.searchlastkey[0]==-2:
            if self.search_hangul.step==0:
                self.search_hangul=Hangul()
                self.searchlastkey = [-1, 0]
            else:
                self.search_hangul.step -= 1
                self.search_hangul.searchlastkey = [-1, 0]
                if self.search_hangul.step<=2: self.search_hangul.jongsung2 = ''
                if self.search_hangul.step<=1: self.search_hangul.jongsung = ''
                if self.search_hangul.step<=0: self.search_hangul.jungsung = ''
                # if delete vowel and no leading consonant
                if self.search_hangul.step == 0 and not self.search_hangul.chosung: self.searchlastkey = [-1, 0]
                self.searchtimer.start()
        elif self.searchlastkey[0]!=-1:
            self.searchlastkey=[-1, 0, '']
        else:
            self.searchstring=self.searchstring[:-1]
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
                        altimage = self.nosingerimage if type(option) == QLabeImageButton else None
                        try:
                            option.setImage(options[i]['image'], altimage)
                        except:
                            option.setPixmap(altimage)
                    except:
                        settings.logger.printException()
                else:
                    option.setText('')
                    if callable(option.clearPixmap):
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

    def setStatusTempText(self, p_str, msec):
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



from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QInputDialog, QFileDialog, QCheckBox, QMenu, QDialog, \
    qApp, QPushButton, QHeaderView, QGridLayout, QLabel, QStyle, QPlainTextEdit, QCompleter
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIntValidator, QPixmap
from PyQt5.QtCore import Qt, QSortFilterProxyModel, QItemSelectionModel, QRegExp, QPoint, QStringListModel
import os
import fnmatch
from collections import OrderedDict
from pprint import pprint

from pywidgets import QUpperValidator
import settings
import functions




class EditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(settings.programDir, 'editor/EditorWindow.ui'), self)
        qApp.setFont(self.font())

        self.action_Song.triggered.connect(lambda : self.stackedWidget.setCurrentIndex(0))
        self.actionS_inger.triggered.connect(lambda : self.stackedWidget.setCurrentIndex(1))
        self.action_Library.triggered.connect(lambda : self.stackedWidget.setCurrentIndex(2))
        self.action_Youtube.triggered.connect(lambda : self.stackedWidget.setCurrentIndex(3))

        self.actionSearch_new_media.triggered.connect(self.openSearchMedia)
        self.actionRebuild_singers.triggered.connect(self.rebuildSingers)
        self.actionSearch_duplicate_media.triggered.connect(self.searchDuplicateMedia)
        self.actionSearch_duplicate_song.triggered.connect(self.searchDuplicateSong)


        self.__song__init__()
        self.__singer__init__()
        self.__library__init__()
        self.__youtube__init__()

        self.show()


    def openSearchMedia(self):
        self.searchmedia = SearchMedia()
        self.searchmedia.accepted.connect(self.songRefresh)


    def closeEvent(self, QCloseEvent):
        settings.mpvMediaPlayer.terminate()
        qApp.quit()



    """common functions"""

    @staticmethod
    def selectRows(tblview, ids):
        tblview.selectionModel().clearSelection()
        for id in ids:
            for idx in tblview.model().match(tblview.model().index(0, 1), Qt.UserRole, id):
                tblview.selectionModel().select(idx, QItemSelectionModel.Select | QItemSelectionModel.Rows)
                tblview.scrollTo(idx)

    @staticmethod
    def refreshFromDB(table, columns, model, columnfunc=None):
        rows = settings.dbconn.execute("select * from "+ table)
        model.clear()
        for r in rows:
            newrow = []
            for k in columns:
                s = columnfunc(k, r) if k.startswith('func_') and callable(columnfunc) else r[k]
                item = QStandardItem(str(s))
                item.setData(s, Qt.UserRole+4)
                item.setData(r['id'], Qt.UserRole)
                item.setData(table, Qt.UserRole+1)
                item.setData(k, Qt.UserRole+2)
                if k.startswith('func_'): item.setFlags( item.flags() & ~Qt.ItemIsEditable )
                newrow.append(item)
            model.appendRow(newrow)

        for i, v in enumerate(columns.values()):
            model.setHeaderData(i, Qt.Horizontal, v)


    def tblSelectionChanged(self, table, tblview, columns):
        rows = [r.row() for r in tblview.selectionModel().selectedRows()]
        rows.sort()

        status = str(len(rows))+" selected of "+str(tblview.model().rowCount())+" "+table+"(s)"
        obj=getattr(self, 'page_'+table)
        if obj:
            obj.setStatusTip(status)
            self.statusBar.showMessage(status)
        wname = table.capitalize()

        for i, k in enumerate(columns):
            # find the label or combobox
            if hasattr(self, 'txt'+wname+str(k).title()):
                obj = getattr(self, 'txt'+wname+str(k).title())
                func=obj.setText
                funcplaceholder=obj.setPlaceholderText
            elif hasattr(self, 'cmb'+wname+str(k).title()):
                obj = getattr(self, 'cmb'+wname + str(k).title())
                func=obj.setCurrentText
                funcplaceholder=obj.lineEdit().setPlaceholderText if obj.lineEdit() else None
            elif hasattr(self, 'chk' + wname + str(k).title()):
                obj = getattr(self, 'chk' + wname + str(k).title())
            else:
                obj = func = None

            if obj:
                # if found, update the label/combobox with the item selected
                values1=[tblview.model().data(tblview.model().index(j, i)) for j in rows]
                values2=set(values1)

                if isinstance(obj, QCheckBox):
                    if len(values2)==1:
                        obj.setTristate(False)
                        obj.setChecked(values1[0]!='' and values1[0]!='0')
                    else:
                        obj.setTristate(True)
                        obj.setCheckState(Qt.PartiallyChecked)
                else:
                    # if value is same in all rows, display it
                    if len(values2)==1:
                        func(values1[0])
                    else:
                        func('')
                    if funcplaceholder:
                        if len(values2)>1:
                            funcplaceholder(values1[0])
                        else:
                            funcplaceholder('')


    @staticmethod
    def addItem(tblview, columns, model):
        newrow = [QStandardItem('') for _ in range(len(columns))]
        model.appendRow(newrow)

        # loop through all the parents and call mapFromSource
        def getIndex(i, m):
            return m.mapFromSource(getIndex(i, m.sourceModel())) if hasattr(m, 'sourceModel') else i

        idx=getIndex(model.indexFromItem(newrow[0]), tblview.model())
        tblview.repaint()
        tblview.selectRow(idx.row())
        tblview.scrollTo(idx)


    @staticmethod
    def deleteItems(table, tblview, refreshfunc=None):
        rows = [r.data(Qt.UserRole) for r in tblview.selectionModel().selectedRows()]
        rows = list(filter(None, rows))
        if len(rows)>0:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Warning)
            msg.setText("Delete "+table+"(s)")
            msg.setInformativeText(str(len(rows))+' '+table+'(s) will be deleted.\nAre you sure?')
            msg.setWindowTitle("Delete "+table+"(s)")
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            if msg.exec() == QMessageBox.Ok:
                settings.dbconn.execute("delete from "+table+" where id in (%s)" % ','.join('?'*len(rows)), rows)
                settings.dbconn.commit()
                if callable(refreshfunc):
                    refreshfunc()

    @staticmethod
    def saveItem(item):
        data=item.data(Qt.DisplayRole)
        id=item.data(Qt.UserRole)
        table=item.data(Qt.UserRole+1)
        col=item.data(Qt.UserRole+2)
        settings.dbconn.execute("update "+table+" set ["+col+"]=? where id = ?", (data, id,))
        settings.dbconn.commit()
        item.setData(int(data) if data.isdigit() else data, Qt.UserRole+4)


    def saveItems(self, table, tblview, columns, refreshfunc=None, columnfunc=None):
        rows = [r.data(Qt.UserRole) for r in tblview.selectionModel().selectedRows()]
        if len(rows)>0:
            wname=table.capitalize()
            cols={}
            for k in columns:
                # find the label or combobox
                if hasattr(self, 'txt' + wname + str(k).title()):
                    txt = getattr(self, 'txt' + wname + str(k).title()).text()
                elif hasattr(self, 'cmb' + wname + str(k).title()):
                    txt = getattr(self, 'cmb' + wname + str(k).title()).currentText()
                elif hasattr(self, 'chk' + wname + str(k).title()):
                    state = getattr(self, 'chk' + wname + str(k).title()).checkState()
                    if state==Qt.Unchecked:
                        txt = '0'
                    elif state==Qt.Checked:
                        txt = '1'
                    else:
                        txt = ''
                else:
                    txt = ''
                # if more then 1 row selected, update only non-empty fields
                if k!='id' and (len(rows)==1 or txt):
                    cols['['+k+']'] = txt.strip()
                    if k.startswith('func_') and callable(columnfunc):
                        columnfunc(cols)


            # disallow duplicate index unless is '0'
            if len(rows)>1 and '[index]' in cols and cols['[index]']!='0':
                cols.pop('[index]')

            if len(cols)>0:
                # update those that are already in db
                id_to_update=list(filter(None, rows))
                if len(id_to_update)>0:
                    try:
                        # print(cols, id_to_update)
                        settings.dbconn.execute("update "+table+" set %s=? where id in (%s)" % ('=?,'.join(cols), ','.join('?'*len(id_to_update))),
                                                list(cols.values()) + id_to_update)
                    except:
                        settings.logger.printException()

                id_newly_added=[]
                # do not save new rows if everything is empty
                if len(list(filter(None, cols.values()))) > 0:
                    # newly added rows which have not been saved to db
                    for _ in range(rows.count(None)):
                        try:
                            # print(cols)
                            c=settings.dbconn.execute("insert into "+table+" (%s) values (%s)" % (','.join(cols), ','.join('?'*len(cols))),
                                                      list(cols.values()))
                            id_newly_added.append(c.lastrowid)
                        except:
                            settings.logger.printException()

                settings.dbconn.commit()
                valueV = tblview.verticalScrollBar().value()
                valueH = tblview.horizontalScrollBar().value()
                if callable(refreshfunc):
                    refreshfunc()
                tblview.repaint()
                tblview.verticalScrollBar().setValue(valueV)
                tblview.horizontalScrollBar().setValue(valueH)
                #after refresh, select back the rows
                self.selectRows(tblview, id_to_update+id_newly_added)


    def setSearchChar(self, table, colkey, columns, tblview, refreshfunc=None):
        rows = [r.data(Qt.UserRole) for r in tblview.selectionModel().selectedRows()]
        if len(rows)==1:
            wname = table.capitalize()
            txt = getattr(self, 'txt' + wname + colkey.title()).text()
            search = functions.get_initials(txt)
            getattr(self, 'txt' + wname + 'Search').setText(search)
        elif len(rows)>1:
            pos_title=list(columns.keys()).index(colkey)
            for id in filter(None, rows):
                try:
                    title=tblview.model().match(tblview.model().index(0, pos_title), Qt.UserRole, id)[0].data()
                    search = functions.get_initials(title)
                    settings.dbconn.execute("update "+table+" set [search]=? where [id]=?", (search, id,))
                except:
                    settings.logger.printException()
            settings.dbconn.commit()
            valueV = tblview.verticalScrollBar().value()
            valueH = tblview.horizontalScrollBar().value()
            if callable(refreshfunc):
                refreshfunc()
            tblview.repaint()
            tblview.verticalScrollBar().setValue(valueV)
            tblview.horizontalScrollBar().setValue(valueH)
            # after refresh, select back the rows
            self.selectRows(tblview, rows)



    """ songs functions """


    songColumns = OrderedDict({'id':'ID', 'index':'Index', 'title':'Title', 'chars':'Chars', 'search':'Search letter',
                                'func_singers':'Singers', 'language':'Language', 'style':'Category', 'channel':'Channel',
                                'library':'Library', 'media_file':'Media file', 'remark':'Remark'})

    channel = ''


    def __song__init__(self):
        self.songModel = QStandardItemModel()
        self.songModel.itemChanged.connect(self.saveItem)
        self.songModelProxy1 = QSortFilterProxyModel()
        self.songModelProxy1.setSourceModel(self.songModel)
        self.songModelProxy2 = QSortFilterProxyModel()
        self.songModelProxy2.setSourceModel(self.songModelProxy1)
        self.songModelProxy3 = QSortFilterProxyModel()
        self.songModelProxy3.setSourceModel(self.songModelProxy2)
        self.songModelProxy4 = QSortFilterProxyModel()
        self.songModelProxy4.setSortRole(Qt.UserRole+4)
        self.songModelProxy4.setSortCaseSensitivity(Qt.CaseInsensitive)
        self.songModelProxy4.setSourceModel(self.songModelProxy3)

        self.tblSong.setModel(self.songModelProxy4)
        self.tblSong.selectionModel().selectionChanged.connect(self.songSelectionChanged)

        self.txtSongSearchTitle.textChanged.connect(self.songSearch)
        self.cmbSongSearchSinger.editTextChanged.connect(self.songSearch)
        self.cmbSongSearchSinger.setCompleter(None)
        self.cmbSongSearchLanguage.currentIndexChanged.connect(self.songSearch)
        self.cmbSongSearchStyle.currentIndexChanged.connect(self.songSearch)
        self.btnSongAdd.clicked.connect(self.songAdd)
        self.btnSongDelete.clicked.connect(self.songDelete)
        self.btnSongSave.clicked.connect(self.songSave)

        self.btnSongIndex.clicked.connect(self.songReindex)
        self.btnSongSearch.clicked.connect(self.songSetSearchChar)
        self.btnSongMedia.clicked.connect(self.songFindMedia)
        self.txtSongTitle.textEdited.connect(self.songTitleEdited)


        self.txtSongIndex.setValidator(QIntValidator())
        self.txtSongChars.setValidator(QIntValidator(1, 100))
        self.txtSongSearch.setValidator(QUpperValidator(QRegExp('[0-9a-zA-Z]+')))
        self.cmbSongChannel.setValidator(QUpperValidator(QRegExp('[lrLR]|[0-9]')))

        self.songCompleter = QCompleter()
        self.songCompleter.setCaseSensitivity(Qt.CaseInsensitive)
        self.txtSongFunc_Singers.setCompleter(self.songCompleter)

        self.btnSongPlayPause.clicked.connect(self.songPlayPause)
        self.lblSongVideoFrame.clicked.connect(self.songPlayPause)
        self.lblSongVideoFrame.setCursor(Qt.ArrowCursor)
        self.btnSongAudio.clicked.connect(self.songAudioSelector)
        self.slideSongVideo.sliderPressed.connect(self.songSliderPressed)
        self.slideSongVideo.sliderMoved.connect(self.songSliderMoved)
        self.slideSongVideo.sliderReleased.connect(self.songSliderReleased)
        self.mpvMediaPlayer=settings.mpvMediaPlayer
        self.mpvMediaPlayer.wid = int(self.lblSongVideoFrame.winId())
        self.mpvMediaPlayer.observe_property('percent-pos', self.songVideoPositionChanged)


        self.songRefresh()
        self.tblSong.sortByColumn(1, Qt.AscendingOrder)



    def songRefresh(self):
        def joinsingers(k, r):
            return ', '.join(
                filter(None, [r['singer'], r['singer2'], r['singer3'], r['singer4'], r['singer5'], r['singer6'], r['singer7'], r['singer8'], r['singer9']])
              ) if k == 'func_singers' else r[k]

        self.refreshFromDB('song', self.songColumns, self.songModel, joinsingers)

        self.tblSong.resizeColumnsToContents()
        self.tblSong.setColumnHidden(0, True)
        self.updateSongCombobox()
        self.page_song.setStatusTip("0 selected of "+str(self.songModel.rowCount())+" song(s)")


    def updateSongCombobox(self):
        txt = self.cmbSongSearchSinger.currentText()
        rows = settings.dbconn.execute('select "" union select distinct name from singer order by name')
        model = QStringListModel([r[0] for r in rows])
        self.cmbSongSearchSinger.setModel(model)
        self.cmbSongSearchSinger.setCurrentText(txt)
        self.songCompleter.setModel(model)

        txt = self.cmbSongSearchLanguage.currentText()
        rows = settings.dbconn.execute('select "" union select distinct language from song order by language')
        model = QStringListModel([r[0] for r in rows])
        self.cmbSongSearchLanguage.setModel(model)
        self.cmbSongSearchLanguage.setCurrentText(txt)
        self.cmbSongLanguage.setModel(model)

        txt = self.cmbSongSearchStyle.currentText()
        rows = settings.dbconn.execute('select "" union select distinct style from song order by style')
        model = QStringListModel([r[0] for r in rows])
        self.cmbSongSearchStyle.setModel(model)
        self.cmbSongSearchStyle.setCurrentText(txt)
        self.cmbSongStyle.setModel(model)

        self.cmbSongChannel.insertItems(0, ['','L','R','0','1','2','3','4','5','6','7','8','9'])

        rows = settings.dbconn.execute('select "" union select distinct root_path from library where enabled=1 order by root_path')
        model = QStringListModel([r[0] for r in rows])
        self.cmbSongLibrary.setModel(model)


    def songSelectionChanged(self, selected, deselected):
        self.tblSelectionChanged('song', self.tblSong, self.songColumns)


    def songSearch(self):
        self.songModelProxy1.setFilterWildcard(self.txtSongSearchTitle.text())
        self.songModelProxy1.setFilterKeyColumn(list(self.songColumns).index('title'))
        self.songModelProxy2.setFilterWildcard(self.cmbSongSearchSinger.currentText())
        self.songModelProxy2.setFilterKeyColumn(list(self.songColumns).index('func_singers'))
        self.songModelProxy3.setFilterFixedString(self.cmbSongSearchLanguage.currentText())
        self.songModelProxy3.setFilterKeyColumn(list(self.songColumns).index('language'))
        self.songModelProxy4.setFilterFixedString(self.cmbSongSearchStyle.currentText())
        self.songModelProxy4.setFilterKeyColumn(list(self.songColumns).index('style'))


    def songAdd(self):
        self.txtSongSearchTitle.setText('')
        self.cmbSongSearchSinger.setCurrentText('')
        self.cmbSongSearchLanguage.setCurrentText('')
        self.cmbSongSearchStyle.setCurrentText('')

        self.addItem(self.tblSong, self.songColumns, self.songModel)


    def songDelete(self):
        self.deleteItems('song', self.tblSong, self.songRefresh)


    def songSave(self):
        # split singers
        def splitsingers(cols):
            if '[func_singers]' in cols:
                singers=cols.pop('[func_singers]').split(',')+['']*10
                cols['singer'] = singers[0].strip()
                for i in range(1,10):
                    cols['singer'+str(i+1)] = singers[i].strip()

        self.saveItems('song', self.tblSong, self.songColumns, self.songRefresh, splitsingers)


    def songReindex(self):
        rows = [r.row() for r in self.tblSong.selectionModel().selectedRows()]
        if len(rows)>0:
            try:
                start = settings.dbconn.execute("select max([index]) from song").fetchone()[0]
            except:
                start = 0
            if not start: start=0
            start+=1

            start, ok = QInputDialog.getInt(self, "Index", 'Start from Index number?', start, 0)
            if ok:
                rows.sort()
                ids=[]
                for r in rows:
                    id=self.tblSong.model().index(r, 1).data(Qt.UserRole)
                    # ignore rows that have not been saved (they're empty anyway)
                    if id:
                        try:
                            settings.dbconn.execute("update song set [index]=? where [id]=?", (start, id,))
                            start += 1
                        except:
                            settings.logger.printException()
                        ids.append(id)
                settings.dbconn.commit()
                valueV = self.tblSong.verticalScrollBar().value()
                valueH = self.tblSong.horizontalScrollBar().value()
                self.songRefresh()
                self.tblSong.verticalScrollBar().setValue(valueV)
                self.tblSong.horizontalScrollBar().setValue(valueH)
                #after refresh, select back the rows
                self.selectRows(self.tblSong, ids)


    def songSetSearchChar(self):
        self.setSearchChar('song', 'title', self.songColumns, self.tblSong, self.songRefresh)


    def songFindMedia(self):
        path=lib=self.cmbSongLibrary.currentText()
        filename=self.txtSongMedia_File.text()
        if lib and os.path.isdir(lib) or filename:
            lib = os.path.normcase(lib)
            path = os.path.dirname(os.path.join(lib, filename))

        qfd=QFileDialog(self, "Open Video", path, "Video (*.avi *.wmv *.mov *.mp* *.mkv *.webm *.rm *.dat *.flv);;All files (*.*)")
        if path:
            qfd.directoryEntered.connect(lambda dir: os.path.normcase(dir).startswith(lib) or qfd.setDirectory(lib))
        if qfd.exec():
            filename = os.path.normcase(qfd.selectedFiles()[0])
            if lib and filename.startswith(lib):
                filename=os.path.sep+filename[len(lib):]
            self.txtSongMedia_File.setText(filename)


    def songTitleEdited(self, txt):
        l=len(txt.strip())
        self.txtSongChars.setText(str(l) if l else '')


    previousplaying=-1
    def songPlayPause(self):
        rows = self.tblSong.selectionModel().selectedRows()
        player=self.mpvMediaPlayer
        if len(rows)==1 and (player.idle_active or self.previousplaying!=rows[0].data()):
            library = rows[0].sibling(rows[0].row(), list(self.songColumns.keys()).index('library')).data()
            mediafile = rows[0].sibling(rows[0].row(), list(self.songColumns.keys()).index('media_file')).data()
            if library=='':
                videopath=mediafile
            else:
                mediafile=mediafile.lstrip(os.path.sep)
                videopath=os.path.join(library,mediafile)
            # print(videopath, rows[0].data())
            player.play(videopath)
            player.aid = 1
            player.command('af', 'clr', '')
            self.channel=''
            self.previousplaying=rows[0].data()
            self.statusBar.showMessage(videopath)
        else:
            if player.duration:
                player.cycle('pause')

    sliderpressed=False
    def songVideoPositionChanged(self, prop, pos):
        if not self.sliderpressed and type(pos)==float:
            self.slideSongVideo.setValue(pos*10)

    def songSliderPressed(self):
        self.sliderpressed=True
        self.previouspaused = self.mpvMediaPlayer.pause
        self.mpvMediaPlayer.pause = True

    def songSliderMoved(self, v):
        self.mpvMediaPlayer.percent_pos=v/10

    def songSliderReleased(self):
        self.mpvMediaPlayer.pause = self.previouspaused
        self.sliderpressed=False

    def songAudioSelector(self, item):
        menu = QMenu(self)
        action = menu.addAction('Stereo')
        if self.channel=='':
            action.setCheckable(True)
            action.setChecked(True)
        action = menu.addAction('Left')
        if self.channel=='L':
            action.setCheckable(True)
            action.setChecked(True)
        action = menu.addAction('Right')
        if self.channel=='R':
            action.setCheckable(True)
            action.setChecked(True)

        try:
            tracks = len(list(filter(lambda t: t['type']=='audio', self.mpvMediaPlayer.track_list)))
        except:
            tracks = 1

        if tracks > 1:
            menu.addSeparator()
            for i in range(tracks):
                action=menu.addAction('Track '+str(i))
                if self.channel==i or (not self.channel.isdigit() and i==0):
                    action.setCheckable(True)
                    action.setChecked(True)

        action = menu.exec_(self.btnSongAudio.mapToGlobal(QPoint(0,0)))

        if action:
            action = action.text()
            self.mpvMediaPlayer.aid = 1
            if action=='Stereo':
                self.mpvMediaPlayer.command('af', 'clr', '')
                self.channel=''
            elif action=='Left':
                self.mpvMediaPlayer.command('af', 'set', 'pan="mono|c0=c0"')
                self.channel='L'
            elif action == 'Right':
                self.mpvMediaPlayer.command('af', 'set', 'pan="mono|c0=c1"')
                self.channel='R'
            elif action.startswith('Track '):
                try:
                    ch = int(action[6:])
                    self.mpvMediaPlayer.aid = ch+1
                    self.mpvMediaPlayer.command('af', 'clr', '')
                    self.channel = '' if ch==0 else ch
                except:
                    pass




    """ singer functions """


    singerColumns = OrderedDict({'id':'ID', 'name':'Name', 'search':'Search letter',
                                'region':'Region', 'type':'Category', 'remark':'Remark'})


    def __singer__init__(self):
        self.singerModel = QStandardItemModel()
        self.singerModel.itemChanged.connect(self.saveItem)
        self.singerModelProxy1 = QSortFilterProxyModel()
        self.singerModelProxy1.setSourceModel(self.singerModel)
        self.singerModelProxy2 = QSortFilterProxyModel()
        self.singerModelProxy2.setSourceModel(self.singerModelProxy1)
        self.singerModelProxy3 = QSortFilterProxyModel()
        self.singerModelProxy3.setSortRole(Qt.UserRole+4)
        self.singerModelProxy3.setSortCaseSensitivity(Qt.CaseInsensitive)
        self.singerModelProxy3.setSourceModel(self.singerModelProxy2)

        self.tblSinger.setModel(self.singerModelProxy3)
        self.tblSinger.selectionModel().selectionChanged.connect(self.singerSelectionChanged)

        self.txtSingerSearchName.textChanged.connect(self.singerSearch)
        self.cmbSingerSearchRegion.currentIndexChanged.connect(self.singerSearch)
        self.cmbSingerSearchCategory.currentIndexChanged.connect(self.singerSearch)
        self.btnSingerAdd.clicked.connect(self.singerAdd)
        self.btnSingerDelete.clicked.connect(self.singerDelete)
        self.btnSingerSave.clicked.connect(self.singerSave)

        self.btnSingerSearch.clicked.connect(self.singerSetSearchChar)
        self.txtSingerSearch.setValidator(QUpperValidator(QRegExp('[0-9a-zA-Z]+')))



        self.singerRefresh()
        self.tblSinger.sortByColumn(1, Qt.AscendingOrder)


    def singerRefresh(self):
        self.refreshFromDB('singer', self.singerColumns, self.singerModel)

        self.tblSinger.resizeColumnsToContents()
        self.tblSinger.setColumnHidden(0, True)
        self.updateSingerCombobox()
        self.page_singer.setStatusTip("0 selected of "+str(self.singerModel.rowCount())+" singer(s)")


    def updateSingerCombobox(self):
        txt = self.cmbSingerSearchRegion.currentText()
        rows = settings.dbconn.execute('select "" union select distinct region from singer order by region')
        model = QStringListModel([r[0] for r in rows])
        self.cmbSingerSearchRegion.setModel(model)
        self.cmbSingerSearchRegion.setCurrentText(txt)
        self.cmbSingerRegion.setModel(model)

        txt = self.cmbSingerSearchCategory.currentText()
        rows = settings.dbconn.execute('select "" union select type region from singer order by type')
        model = QStringListModel([r[0] for r in rows])
        self.cmbSingerSearchCategory.setModel(model)
        self.cmbSingerSearchCategory.setCurrentText(txt)
        self.cmbSingerType.setModel(model)


    def singerSelectionChanged(self, selected, deselected):
        self.tblSelectionChanged('singer', self.tblSinger, self.singerColumns)

        self.lblSingerImage.clear()
        self.lblSingerImage.setText('image')
        rows = self.tblSinger.selectionModel().selectedRows()
        if len(rows)==1:
            name = rows[0].sibling(rows[0].row(), list(self.singerColumns.keys()).index('name')).data()
            image = os.path.join(settings.config['singer.picture'], name + '.jpg')
            if os.path.isfile(image):
                self.lblSingerImage.setPixmap(QPixmap(image))



    def singerSearch(self):
        self.singerModelProxy1.setFilterWildcard(self.txtSingerSearchName.text())
        self.singerModelProxy1.setFilterKeyColumn(list(self.singerColumns).index('name'))
        self.singerModelProxy2.setFilterWildcard(self.cmbSingerSearchRegion.currentText())
        self.singerModelProxy2.setFilterKeyColumn(list(self.singerColumns).index('region'))
        self.singerModelProxy3.setFilterFixedString(self.cmbSingerSearchCategory.currentText())
        self.singerModelProxy3.setFilterKeyColumn(list(self.singerColumns).index('type'))


    def singerAdd(self):
        self.txtSingerSearchName.setText('')
        self.cmbSingerSearchRegion.setCurrentText('')
        self.cmbSingerSearchCategory.setCurrentText('')

        self.addItem(self.tblSinger, self.singerColumns, self.singerModel)


    def singerDelete(self):
        self.deleteItems('singer', self.tblSinger, self.singerRefresh)


    def singerSave(self):
        self.saveItems('singer', self.tblSinger, self.singerColumns, self.singerRefresh)


    def singerSetSearchChar(self):
        self.setSearchChar('singer', 'name', self.singerColumns, self.tblSinger, self.singerRefresh)



    """ library functions """


    libraryColumns = OrderedDict({'id':'ID', 'root_path':'Root Path', 'enabled':'Enable', 'mirror1':'Mirror1',
                                  'mirror2':'Mirror2', 'mirror3':'Mirror3', 'mirror4':'Mirror4', 'mirror5':'Mirror5',
                                  'mirror6':'Mirror6', 'mirror7':'Mirror7', 'mirror8':'Mirror8', 'mirror9':'Mirror9',
                                  'mirror10':'Mirror10'})


    def __library__init__(self):
        self.libraryModel = QStandardItemModel()
        self.libraryModelProxy1 = QSortFilterProxyModel()
        self.libraryModelProxy1.setSortRole(Qt.UserRole+4)
        self.libraryModelProxy1.setSortCaseSensitivity(Qt.CaseInsensitive)
        self.libraryModelProxy1.setSourceModel(self.libraryModel)

        self.tblLibrary.setModel(self.libraryModelProxy1)
        self.tblLibrary.selectionModel().selectionChanged.connect(self.librarySelectionChanged)

        self.btnLibraryAdd.clicked.connect(self.libraryAdd)
        self.btnLibraryDelete.clicked.connect(self.libraryDelete)
        self.btnLibrarySave.clicked.connect(self.librarySave)

        for btn in [self.btnLibraryRoot_Path, self.btnLibraryMirror1, self.btnLibraryMirror2, self.btnLibraryMirror3, self.btnLibraryMirror4, self.btnLibraryMirror5, self.btnLibraryMirror6, self.btnLibraryMirror7, self.btnLibraryMirror8, self.btnLibraryMirror9, self.btnLibraryMirror10]:
            btn.clicked.connect(self.libraryBrowse)

        self.libraryRefresh()
        self.tblLibrary.sortByColumn(1, Qt.AscendingOrder)


    def libraryRefresh(self):
        self.refreshFromDB('library', self.libraryColumns, self.libraryModel)

        self.tblLibrary.resizeColumnsToContents()
        self.tblLibrary.setColumnHidden(0, True)
        self.page_library.setStatusTip("0 selected of "+str(self.libraryModel.rowCount())+" library(s)")


    def librarySelectionChanged(self, selected, deselected):
        self.tblSelectionChanged('library', self.tblLibrary, self.libraryColumns)


    def libraryAdd(self):
        self.addItem(self.tblLibrary, self.libraryColumns, self.libraryModel)


    def libraryDelete(self):
        self.deleteItems('library', self.tblLibrary, self.libraryRefresh)


    def librarySave(self):
        self.saveItems('library', self.tblLibrary, self.libraryColumns, self.libraryRefresh)


    def libraryBrowse(self):
        lblname='txt'+self.sender().objectName()[3:]
        lbl=getattr(self, lblname)
        dirname=lbl.text()

        dir=QFileDialog.getExistingDirectory(self, "Select directory", dirname)
        if dir:
            lbl.setText(os.path.normcase(dir))



    """ youtube functions """


    youtubeColumns = OrderedDict({'id':'ID', 'name':'Name', 'user':'User', 'url':'URL', 'enable':'Enable'})


    def __youtube__init__(self):
        self.youtubeModel = QStandardItemModel()
        self.youtubeModel.itemChanged.connect(self.saveItem)
        self.youtubeModelProxy1 = QSortFilterProxyModel()
        self.youtubeModelProxy1.setSortRole(Qt.UserRole+4)
        self.youtubeModelProxy1.setSortCaseSensitivity(Qt.CaseInsensitive)
        self.youtubeModelProxy1.setSourceModel(self.youtubeModel)

        self.tblYoutube.setModel(self.youtubeModelProxy1)
        self.tblYoutube.selectionModel().selectionChanged.connect(self.youtubeSelectionChanged)

        self.btnYoutubeAdd.clicked.connect(self.youtubeAdd)
        self.btnYoutubeDelete.clicked.connect(self.youtubeDelete)
        self.btnYoutubeSave.clicked.connect(self.youtubeSave)


        self.youtubeRefresh()
        self.tblYoutube.sortByColumn(1, Qt.AscendingOrder)


    def youtubeRefresh(self):
        self.refreshFromDB('youtube', self.youtubeColumns, self.youtubeModel)

        self.tblYoutube.resizeColumnsToContents()
        self.tblYoutube.setColumnHidden(0, True)
        self.page_youtube.setStatusTip("0 selected of "+str(self.youtubeModel.rowCount())+" youtube(s)")


    def youtubeSelectionChanged(self, selected, deselected):
        self.tblSelectionChanged('youtube', self.tblYoutube, self.youtubeColumns)


    def youtubeAdd(self):
        self.addItem(self.tblYoutube, self.youtubeColumns, self.youtubeModel)


    def youtubeDelete(self):
        self.deleteItems('youtube', self.tblYoutube, self.youtubeRefresh)


    def youtubeSave(self):
        self.saveItems('youtube', self.tblYoutube, self.youtubeColumns, self.youtubeRefresh)


    """ other functions """

    def rebuildSingers(self):
        rows = settings.dbconn.execute('select distinct * from (' 
            'select singer from song union ' 
            'select singer2 from song union ' 
            'select singer3 from song union ' 
            'select singer4 from song union ' 
            'select singer5 from song union ' 
            'select singer6 from song union ' 
            'select singer7 from song union ' 
            'select singer8 from song union ' 
            'select singer9 from song ' 
            ') where singer<>"" and singer not in (select name from singer)')

        newsingers=[]
        for r in rows:
            newsingers.append((r[0], functions.get_initials(r[0]),))

        if len(newsingers)>0:
            settings.dbconn.executemany('insert into singer (name,search) values (?,?)', newsingers)
            settings.dbconn.commit()
            self.singerRefresh()
            QMessageBox.information(self, "Rebuild singers", str(len(newsingers))+" singer(s) have been added")
        else:
            QMessageBox.warning(self, "Rebuild singers", "No new singer found")


    def searchDuplicateMedia(self):
        rows = settings.dbconn.execute("select count(id), library, media_file from song where media_file<>'' group by library, media_file having count(id)>1")
        medias=['('+str(r[0])+' dups)\t'+r[1]+'\t'+r[2] for r in rows]
        if medias:
            self.dupmediadialog = QDialog(self, Qt.Tool)
            self.dupmediadialog.setWindowTitle("Search duplicate media")
            self.dupmediadialog.setMinimumWidth(600)
            self.dupmediadialog.setMinimumHeight(400)
            # self.dupmediadialog.setWindowFlags()
            layout=QGridLayout(self.dupmediadialog)
            label=QLabel()
            label.setPixmap(self.style().standardIcon(QStyle.SP_MessageBoxWarning).pixmap(100,100))
            layout.addWidget(label, 0, 0)
            layout.addWidget(QLabel(str(len(medias)) + " media(s) are found in duplicates:"), 0, 1)
            layout.setColumnStretch(1,100)
            textedit=QPlainTextEdit("\n".join(medias))
            textedit.setReadOnly(True)
            layout.addWidget(textedit, 1, 0, 1, 2)
            self.dupmediadialog.show()
        else:
            QMessageBox.information(self, "Search duplicate media", "No duplicate media found")


    def searchDuplicateSong(self):
        rows = settings.dbconn.execute("select count(id), trim(title) title from song where title<>'' group by title having count(id)>1")
        songs = rows.fetchall()
        if songs:
            titles=[r[1] for r in songs]
            rows = settings.dbconn.execute("select singer, trim(title) from song where trim(title) in (%s)" % ','.join('?'*len(titles)), titles)
            singers = rows.fetchall()
            message=['('+str(r[0])+' dups)\t'+r[1]+'\t' + ','.join([s[0] for s in singers if s[1]==r[1]])
                     for r in songs]

            self.dupmediadialog = QDialog(self, Qt.Tool)
            self.dupmediadialog.setWindowTitle("Search duplicate song")
            self.dupmediadialog.setMinimumWidth(600)
            self.dupmediadialog.setMinimumHeight(400)
            # self.dupmediadialog.setWindowFlags()
            layout=QGridLayout(self.dupmediadialog)
            label=QLabel()
            label.setPixmap(self.style().standardIcon(QStyle.SP_MessageBoxWarning).pixmap(100,100))
            layout.addWidget(label, 0, 0)
            layout.addWidget(QLabel(str(len(songs)) + " song(s) are found in duplicates:"), 0, 1)
            layout.setColumnStretch(1,100)
            textedit=QPlainTextEdit("\n".join(message))
            textedit.setReadOnly(True)
            layout.addWidget(textedit, 1, 0, 1, 2)
            self.dupmediadialog.show()
        else:
            QMessageBox.information(self, "Search duplicate song", "No duplicate song found")



class SearchMedia(QDialog):
    def __init__(self):
        super().__init__()
        uic.loadUi(os.path.join(settings.programDir, 'editor/SearchMedia.ui'), self)

        self.mediaModel = QStandardItemModel()
        self.mediaModelProxy1 = QSortFilterProxyModel()
        self.mediaModelProxy1.setSourceModel(self.mediaModel)
        self.tblMedia.setModel(self.mediaModelProxy1)

        self.cmbSongChannel.setValidator(QUpperValidator(QRegExp('[lrLR]|[0-9]')))
        self.btnSearch.clicked.connect(self.searchMedia)

        self.updateCombobox()
        self.show()


    def updateCombobox(self):
        rows = settings.dbconn.execute('select distinct root_path from library where enabled=1 order by root_path')
        model = QStringListModel([r[0] for r in rows])
        self.cmbLibrary.setModel(model)

        rows = settings.dbconn.execute('select "" union select distinct language from song order by language')
        model = QStringListModel([r[0] for r in rows])
        self.cmbSongLanguage.setModel(model)

        rows = settings.dbconn.execute('select "" union select distinct style from song order by style')
        model = QStringListModel([r[0] for r in rows])
        self.cmbSongStyle.setModel(model)

        self.cmbSongChannel.insertItems(0, ['','L','R','0','1','2','3','4','5','6','7','8','9'])


    def searchMedia(self):
        lib = self.cmbLibrary.currentText()

        if not (os.path.isdir(lib) and os.path.exists(lib)):
            QMessageBox.critical(self, "Search new media", "Directory does not exist!")
            return

        # get files from db
        rows=settings.dbconn.execute("select distinct media_file from song where library=?", (lib,))
        dbfiles=[r['media_file'] for r in rows]

        try:
            file_exts = '.avi *.wmv *.mov *.mp* *.mkv *.webm *.rm *.dat *.flv'.split(' ')
            # find all files that match ext
            lib = os.path.join(lib,'')
            files = []
            for root,dirs,f1 in os.walk(lib):
                f1=list(filter(lambda f:f[0] not in ['~','.'], f1))
                for f2 in [fnmatch.filter(f1, ext) for ext in file_exts]:
                    files.extend([os.path.join(root, f3) for f3 in f2])
        except:
            QMessageBox.critical(self, "Search new media", "Error reading directory!\nMake sure it exist and readable.")
            return

        # remove lib
        files = map(lambda f: os.path.sep+f[len(lib):], files)
        # remove files that's already in db
        files = list(filter(lambda f: f not in dbfiles, files ))

        self.mediaModel.clear()
        for f in files:
            newrow = []

            item = QStandardItem()
            item.setCheckable(True)
            item.setCheckState(Qt.Checked)
            newrow.append(item)

            # try to split the filename to singer+title
            filename = os.path.splitext(os.path.basename(f))[0]
            for s1 in ('-','_',')',']','}',' ','.'):
                title = filename.split(s1, 1)
                if len(title)==2:
                    singer=title[0]
                    title=title[1]
                    break

            if type(title)==list:
                title=title[0]
                singer=''

            for ext in file_exts:
                if fnmatch.fnmatch(title, ext):
                    title=os.path.splitext(title)[0]

            title=title.strip('.|_- ')
            singer=singer.strip('.|_- ').replace('&',',').replace('_',',')

            item = QStandardItem(title)
            newrow.append(item)
            swap = QStandardItem('')
            newrow.append(swap)
            item = QStandardItem(singer)
            newrow.append(item)
            item = QStandardItem(f)
            item.setFlags(item.flags() & ~Qt.ItemIsEditable)
            newrow.append(item)

            self.mediaModel.appendRow(newrow)
            swapbutton = QPushButton('<=>')
            swapbutton.swapStandardItem=swap.index()
            swapbutton.clicked.connect(self.swapTitleSinger)
            self.tblMedia.setIndexWidget(self.mediaModelProxy1.mapFromSource(swap.index()), swapbutton)

        if files:
            self.mediaModel.setHeaderData(0, Qt.Horizontal, '')
            self.mediaModel.setHeaderData(1, Qt.Horizontal, 'Title')
            self.mediaModel.setHeaderData(2, Qt.Horizontal, '')
            self.mediaModel.setHeaderData(3, Qt.Horizontal, 'Singers')
            self.mediaModel.setHeaderData(4, Qt.Horizontal, 'Media File')

            self.tblMedia.resizeColumnsToContents()
            self.tblMedia.horizontalHeader().resizeSection(0, 25)
            self.tblMedia.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
            self.tblMedia.horizontalHeader().resizeSection(2, 30)
            self.tblMedia.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)
        else:
            QMessageBox.information(self, "Search new media", "No new media found")



    def swapTitleSinger(self):
        r=self.sender().swapStandardItem.row()
        t=self.mediaModel.item(r, 1).data(Qt.DisplayRole)
        self.mediaModel.item(r, 1).setData(self.mediaModel.item(r, 3).data(Qt.DisplayRole), Qt.DisplayRole)
        self.mediaModel.item(r, 3).setData(t, Qt.DisplayRole)


    def accept(self):
        library = self.cmbLibrary.currentText()
        language=self.cmbSongLanguage.currentText()
        style=self.cmbSongStyle.currentText()
        channel=self.cmbSongChannel.currentText()

        saved=False
        for j in range(self.mediaModel.rowCount()):
            if self.mediaModel.item(j, 0).checkState()==Qt.Checked:
                title=self.mediaModel.item(j, 1).data(Qt.DisplayRole).strip()
                singers=self.mediaModel.item(j, 3).data(Qt.DisplayRole)
                singers=singers.split(',')+['']*10
                singers=[i.strip() for i in singers[:10]]
                chars=len(title)
                search=functions.get_initials(title)
                media=self.mediaModel.item(j, 4).data(Qt.DisplayRole)

                settings.dbconn.execute("insert into song ([index],title,chars,search,library,media_file,language,style,channel,"
                                        "singer,singer2,singer3,singer4,singer5,singer6,singer7,singer8,singer9,singer10) "
                                        "values (0,?,?,?,?,?,?,?,?, ?,?,?,?,?,?,?,?,?,?)",
                                    [title,chars,search,library,media,language,style,channel]+singers)
                saved=True


        if saved:
            settings.dbconn.commit()
            super().accept()





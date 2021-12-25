from PyQt5 import uic
from PyQt5.QtWidgets import QMainWindow, QMessageBox, QInputDialog, QFileDialog, QCheckBox, QMenu, QDialog, \
    qApp, QPushButton, QHeaderView, QCompleter, QLineEdit, QComboBox, QSplitter
from PyQt5.QtGui import QStandardItemModel, QStandardItem, QIntValidator, QRegExpValidator, QPixmap
from PyQt5.QtCore import Qt, QSortFilterProxyModel, QItemSelectionModel, QRegExp, QPoint, QStringListModel, QRunnable, \
    QThreadPool, QItemSelection, QItemSelectionRange, pyqtSignal, QSettings
import os
import sys
import time
import fnmatch
from collections import OrderedDict
import re
from opencc import OpenCC
import concurrent.futures
#import multiprocessing
from tqdm import tqdm
from pprint import pprint

from pywidgets import QUpperValidator, QLineEditDelegate, QComboBoxDelegate, QTagCompleterLineEditDelegate, \
    QLargeMessageBox, QStatusDialog
import settings
import functions



NUL = 'NUL' if sys.platform == "win32" else '/dev/null'

class EditorWindow(QMainWindow):
    refreshcomboboxes = pyqtSignal()

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
        self.refreshcomboboxes.emit()

        qsettings=QSettings()
        try:
            self.restoreGeometry(qsettings.value('editorWindowGeometry'))
            for split in self.findChildren(QSplitter):
                split.restoreState(qsettings.value('editorWindow_' + split.objectName()))
        except:
            pass
        self.show()
        self.stackedWidget.setCurrentIndex(0)


    def openSearchMedia(self):
        self.searchmedia = SearchMedia()
        self.searchmedia.accepted.connect(self.songRefresh)


    def closeEvent(self, QCloseEvent):
        settings.mpvMediaPlayer.terminate()
        qsettings=QSettings()
        qsettings.setValue('editorWindowGeometry', self.saveGeometry())
        for split in self.findChildren(QSplitter):
            qsettings.setValue('editorWindow_'+split.objectName(), split.saveState())
        qApp.quit()



    """common functions"""

    @staticmethod
    def selectRows(tblview, ids):
        tblview.selectionModel().clearSelection()
        firstidx=tblview.model().index(0, 1)
        selections = QItemSelection()
        for id in ids:
            for idx in tblview.model().match(firstidx, Qt.UserRole, id, 1, Qt.MatchExactly):
                selections.append(QItemSelectionRange(idx))
        tblview.selectionModel().select(selections, QItemSelectionModel.Select | QItemSelectionModel.Rows)
        try:
            tblview.scrollTo(tblview.model().match(firstidx, Qt.UserRole, ids[0], 1, Qt.MatchExactly)[0])
        except:
            pass

    @staticmethod
    def refreshAndSelectRows(refreshfunc, tblview, rows):
        if callable(refreshfunc):
            valueV = tblview.verticalScrollBar().value()
            valueH = tblview.horizontalScrollBar().value()
            refreshfunc()
            tblview.repaint()
            tblview.verticalScrollBar().setValue(valueV)
            tblview.horizontalScrollBar().setValue(valueH)
        # after refresh, select back the rows
        EditorWindow.selectRows(tblview, rows)

    @staticmethod
    def refreshFromDB(table, tblview, columns, model, columnjoinfunc=None, columnsplitfunc=None):
        rows = settings.dbconn.execute("select * from "+ table)
        model.clear()
        for r in rows:
            newrow = []
            for k in columns:
                s = columnjoinfunc(k, r) if k.startswith('func_') and callable(columnjoinfunc) else r[k]
                item = QStandardItem(str(s))
                item.setData(r['id'], Qt.UserRole)
                item.setData(s, Qt.UserRole+1)
                if 'type' in columns[k].keys():
                    try:
                        item.setData(columns[k]['type'](s), Qt.UserRole + 1)
                    except:
                        pass
                item.setData(table, Qt.UserRole+2)
                item.setData(k, Qt.UserRole+3)
                if k.startswith('func_') and callable(columnjoinfunc):
                    item.setData(columnjoinfunc, Qt.UserRole + 4)
                if k.startswith('func_') and callable(columnsplitfunc):
                    item.setData(columnsplitfunc, Qt.UserRole + 5)
                newrow.append(item)
            model.appendRow(newrow)

        for i, v in enumerate(columns.values()):
            model.setHeaderData(i, Qt.Horizontal, v['title'])
            if 'itemdelegateclass' in v:
                validator=imodel=None
                if 'validator' in v:
                    validator=v['validator']
                if 'getmodel' in v:
                    imodel=v['getmodel']()
                tblview.setItemDelegateForColumn(i, v['itemdelegateclass'](tblview, validator, imodel))

        tblview.resizeColumnsToContents()
        tblview.setColumnHidden(0, True)


    def setInputValidators(self, table, columns):
        for k, v in columns.items():
            if 'validator' in v:
                wname = table.capitalize()
                if hasattr(self, 'txt'+wname+str(k).title()):
                    obj = getattr(self, 'txt'+wname+str(k).title())
                    obj.setValidator(v['validator'])
                elif hasattr(self, 'cmb'+wname+str(k).title()):
                    obj = getattr(self, 'cmb'+wname + str(k).title())
                    if obj.lineEdit():
                        obj.lineEdit().setValidator(v['validator'])
                else:
                    obj = None


    def setComboBoxModal(self, table, columns):
        for k, v in columns.items():
            if 'getmodel' in v:
                wname = table.capitalize()
                model = v['getmodel']()
                if hasattr(self, 'txt'+wname+str(k).title()):
                    obj = getattr(self, 'txt'+wname+str(k).title())
                    comp=obj.completer()
                    if comp:
                        comp.setModel(model)
                elif hasattr(self, 'cmb'+wname+str(k).title()):
                    obj = getattr(self, 'cmb'+wname + str(k).title())
                    obj.setModel(model)
                if hasattr(self, 'cmb'+wname+'Search'+str(k).title()):
                    obj = getattr(self, 'cmb'+wname +'Search'+ str(k).title())
                    txt=obj.currentText()
                    obj.setModel(model)
                    obj.setCurrentIndex(obj.findText(txt))
                    obj.setCurrentText(txt)


    def setPageStatusTip(self, table, selectedrows, total):
        obj=getattr(self, 'page_'+table)
        if obj:
            status = "%s selected of %s %s(s)" % (selectedrows, total, table)
            obj.setStatusTip(status)
            self.statusBar.showMessage(status)


    def tblSelectionChanged(self, table, tblview, columns):
        rows = [r.row() for r in tblview.selectionModel().selectedRows()]
        rows.sort()

        self.setPageStatusTip(table, len(rows), tblview.model().rowCount())
        wname = table.capitalize()

        for i, k in enumerate(columns):
            # find the inputbox
            obj = None
            for w in ('txt','cmb','chk'):
                if hasattr(self, w + wname + str(k).title()):
                    obj = getattr(self, w + wname + str(k).title())

            if obj:
                # if found, update the label/combobox with the item selected
                values1=[tblview.model().data(tblview.model().index(j, i)) for j in rows]
                values2=set(values1)

                if isinstance(obj, QLineEdit):
                    obj.setText(values1[0] if len(values2)==1 else '')
                    obj.setPlaceholderText('No change' if len(values2)>1 else '')
                elif isinstance(obj, QComboBox):
                    obj.setCurrentIndex(obj.findText(values1[0] if len(values2) == 1 else ''))
                    obj.setCurrentText(values1[0] if len(values2) == 1 else '')
                    if obj.lineEdit():
                        obj.lineEdit().setPlaceholderText('No change' if len(values2)>1 else '')
                elif isinstance(obj, QCheckBox):
                    if len(values2)==1:
                        obj.setTristate(False)
                        obj.setChecked(values1[0]!='' and values1[0]!='0')
                    else:
                        obj.setTristate(True)
                        obj.setCheckState(Qt.PartiallyChecked)


    @staticmethod
    def addItem(tblview, columns, model):
        newrow=[]
        for v in columns.keys():
            s=0 if v=='index' else ''
            item = QStandardItem(str(s))
            item.setData(s, Qt.UserRole+1)
            newrow.append(item)
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


    def saveItem(self, item):
        data=item.data(Qt.DisplayRole)
        id=item.data(Qt.UserRole)
        table=item.data(Qt.UserRole+2)
        col=item.data(Qt.UserRole+3)
        columnsplitfunc=item.data(Qt.UserRole+5)
        if columnsplitfunc:
            cols=columnsplitfunc(col, data)
            # print("update " + table + " set [%s]=? where id = ?" % ']=?,['.join(cols),
            #       list(cols.values()) + [id])
            settings.dbconn.execute("update " + table + " set [%s]=? where id = ?" % ']=?,['.join(cols),
                                    list(cols.values()) + [id])
        else:
            settings.dbconn.execute("update "+table+" set ["+col+"]=? where id = ?", (data, id,))
        settings.dbconn.commit()
        item.setData(int(data) if data.isdigit() else data, Qt.UserRole+1)

        self.refreshcomboboxes.emit()
        if hasattr(self, table+'SelectionChanged'):
            obj = getattr(self, table+'SelectionChanged')
            if callable(obj):
                obj()


    def saveItems(self, table, tblview, columns, refreshfunc=None, columnsplitfunc=None):
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
                    if k.startswith('func_') and callable(columnsplitfunc):
                        cols.update(columnsplitfunc(k, txt))
                    else:
                        cols[k] = txt.strip()

            # disallow duplicate index unless is '0'
            if len(rows)>1 and 'index' in cols and cols['index']!='0':
                cols.pop('index')

            if 'index' in cols and not cols['index'].isdigit():
                cols['index']=0

            if len(cols)>0:
                # update those that are already in db
                id_to_update=list(filter(None, rows))
                if len(id_to_update)>0:
                    #https://www.sqlite.org/limits.html#max_variable_number
                    for i in range(0,len(id_to_update),500):
                        try:
                            # print("update "+table+" set [%s]=? where id in (%s)" % (']=?[,'.join(cols), ','.join('?'*len(id_to_update[i:i+500]))),
                            #       list(cols.values()) + id_to_update[i:i+500])
                            settings.dbconn.execute("update "+table+" set [%s]=? where id in (%s)" % (']=?,['.join(cols), ','.join('?'*len(id_to_update[i:i+500]))),
                                                    list(cols.values()) + id_to_update[i:i+500])
                        except:
                            settings.logger.printException()

                id_newly_added=[]
                # do not save new rows if everything is empty
                if len(list(filter(None, cols.values()))) > 0:
                    # newly added rows which have not been saved to db
                    for _ in range(rows.count(None)):
                        try:
                            # print("insert into "+table+" ([%s]) values (%s)" % ('],['.join(cols), ','.join('?'*len(cols))),
                            #       list(cols.values()))
                            c=settings.dbconn.execute("insert into "+table+" ([%s]) values (%s)" % ('],['.join(cols), ','.join('?'*len(cols))),
                                                      list(cols.values()))
                            id_newly_added.append(c.lastrowid)
                        except:
                            settings.logger.printException()

                settings.dbconn.commit()
                self.refreshcomboboxes.emit()
                self.refreshAndSelectRows(refreshfunc, tblview, rows+id_newly_added)


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
            self.refreshAndSelectRows(refreshfunc, tblview, rows)



    """ songs functions """

    @staticmethod
    def getSongSingerModel():
        rows = settings.dbconn.execute('select "" union select distinct name from singer order by name')
        return QStringListModel([r[0] for r in rows])

    @staticmethod
    def getSongLanguageModel():
        rows = settings.dbconn.execute('select "" union select distinct language from song order by language')
        return QStringListModel([r[0] for r in rows])

    @staticmethod
    def getSongStyleModel():
        rows = settings.dbconn.execute('select "" union select distinct style from song order by style')
        return QStringListModel([r[0] for r in rows])

    @staticmethod
    def getSongChannelModel():
        return QStringListModel(['','L','R','0','1','2','3','4','5','6','7','8','9'])

    @staticmethod
    def getSongLibraryModel():
        rows = settings.dbconn.execute('select "" union select distinct root_path from library where enabled=1 order by root_path')
        model=QStringListModel([r[0] for r in rows])
        model.disallowedit=True
        return model


    songColumns = OrderedDict({
        'id': {'title': 'ID'},
        'index': {'title': 'Index', 'itemdelegateclass': QLineEditDelegate, 'validator': QIntValidator()},
        'title': {'title': 'Title', 'type': str},
        'chars': {'title': 'Chars', 'itemdelegateclass': QLineEditDelegate, 'validator': QIntValidator()},
        'search': {'title': 'Search letter', 'itemdelegateclass': QLineEditDelegate, 'validator': QUpperValidator(QRegExp('[0-9a-zA-Z]+')), 'type': str},
        'func_singers': {'title': 'Singers', 'itemdelegateclass': QTagCompleterLineEditDelegate, 'getmodel': getSongSingerModel.__func__},
        'language': {'title': 'Language', 'itemdelegateclass': QComboBoxDelegate, 'getmodel': getSongLanguageModel.__func__, 'type': str},
        'style': {'title': 'Category', 'itemdelegateclass': QComboBoxDelegate, 'getmodel': getSongStyleModel.__func__, 'type': str},
        'channel': {'title': 'Channel', 'itemdelegateclass': QComboBoxDelegate, 'validator':QUpperValidator(QRegExp('[lrLR]|[0-9]')), 'getmodel': getSongChannelModel.__func__, 'type': str},
        'volume': {'title': 'Volume (±dB)', 'itemdelegateclass': QLineEditDelegate, 'validator': QRegExpValidator(QRegExp('^([-]?\d+(\.\d*)?)(,\s*[-]?\d+(\.\d*)?)?$')), 'type': str},
        'library': {'title': 'Library', 'itemdelegateclass': QComboBoxDelegate, 'getmodel': getSongLibraryModel.__func__},
        'media_file': {'title': 'Media file'},
        'library2': {'title': 'Library2', 'itemdelegateclass': QComboBoxDelegate, 'getmodel': getSongLibraryModel.__func__},
        'media_file2': {'title': 'Media file2'},
        'remark': {'title': 'Remark', 'type': str}
    })

    channel = ''


    def __song__init__(self):
        self.songModel = QStandardItemModel()
        self.songModel.itemChanged.connect(self.saveItem)
        self.songModelProxy1 = QSortFilterProxyModel()
        self.songModelProxy1.setSourceModel(self.songModel)
        self.songModelProxy1.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.songModelProxy2 = QSortFilterProxyModel()
        self.songModelProxy2.setSourceModel(self.songModelProxy1)
        self.songModelProxy2.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.songModelProxy3 = QSortFilterProxyModel()
        self.songModelProxy3.setSourceModel(self.songModelProxy2)
        self.songModelProxy4 = QSortFilterProxyModel()
        self.songModelProxy4.setSortRole(Qt.UserRole+1)
        self.songModelProxy4.setSortCaseSensitivity(Qt.CaseInsensitive)
        self.songModelProxy4.setSourceModel(self.songModelProxy3)

        self.tblSong.setModel(self.songModelProxy4)
        self.tblSong.selectionModel().selectionChanged.connect(self.songSelectionChanged)
        self.tblSong.customContextMenuRequested.connect(self.tblSongMenuRequested)

        self.txtSongSearchTitle.textChanged.connect(self.songSearch)
        self.cmbSongSearchFunc_Singers.editTextChanged.connect(self.songSearch)
        self.cmbSongSearchLanguage.currentIndexChanged.connect(self.songSearch)
        self.cmbSongSearchStyle.currentIndexChanged.connect(self.songSearch)
        self.btnSongAdd.clicked.connect(self.songAdd)
        self.btnSongDelete.clicked.connect(self.songDelete)
        self.btnSongSave.clicked.connect(self.songSave)

        self.btnSongIndex.clicked.connect(self.songReindex)
        self.btnSongSearch.clicked.connect(self.songSetSearchChar)
        self.btnSongMedia.clicked.connect(self.songFindMedia)
        self.btnSongMedia2.clicked.connect(self.songFindMedia2)
        self.txtSongTitle.textEdited.connect(self.songTitleEdited)

        self.songCompleter = QCompleter()
        self.songCompleter.setCaseSensitivity(Qt.CaseInsensitive)
        self.txtSongFunc_Singers.setCompleter(self.songCompleter)

        self.setInputValidators('song', self.songColumns)

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

        self.menuSong.menuAction().setVisible(False)
        self.actionConvert_to_Simplified_Chinese.triggered.connect(self.convert2Simplified)
        self.actionConvert_to_Traditional_Chinese.triggered.connect(self.convert2Traditional)
        self.actionCheck_medias.triggered.connect(self.checkMedias)
        self.actionAuto_set_volume.triggered.connect(self.setVolume)


        self.refreshcomboboxes.connect(lambda:self.setComboBoxModal('song', self.songColumns))

        self.songRefresh()
        self.tblSong.sortByColumn(1, Qt.AscendingOrder)


    @staticmethod
    def joinsingers(key, row):
        return ', '.join(
            filter(None, [row['singer'], row['singer2'], row['singer3'], row['singer4'], row['singer5'], row['singer6'], row['singer7'], row['singer8'], row['singer9']])
          ) if key == 'func_singers' else row[key]


    # split singers
    @staticmethod
    def splitsingers(key, singers):
        if key=='func_singers':
            row=singers.split(',') + [''] * 10
            r = {'singer':row[0].strip()}
            for i in range(1,10):
                r['singer' + str(i + 1)] = row[i].strip()
            return r


    def songRefresh(self):
        self.refreshFromDB('song', self.tblSong, self.songColumns, self.songModel, self.joinsingers, self.splitsingers)
        self.setPageStatusTip('song', 0, self.songModel.rowCount())


    def songSelectionChanged(self, selected=None, deselected=None):
        self.tblSelectionChanged('song', self.tblSong, self.songColumns)


    def songSearch(self):
        self.songModelProxy1.setFilterWildcard(self.txtSongSearchTitle.text().strip())
        self.songModelProxy1.setFilterKeyColumn(list(self.songColumns).index('title'))
        self.songModelProxy2.setFilterWildcard(self.cmbSongSearchFunc_Singers.currentText().strip())
        self.songModelProxy2.setFilterKeyColumn(list(self.songColumns).index('func_singers'))
        slang=self.cmbSongSearchLanguage.currentText()
        if slang:
            self.songModelProxy3.setFilterRegExp(QRegExp('^%s$'%slang))
            self.songModelProxy3.setFilterKeyColumn(list(self.songColumns).index('language'))
        else:
            self.songModelProxy3.setFilterWildcard('')
        sstyle=self.cmbSongSearchStyle.currentText()
        if sstyle:
            self.songModelProxy4.setFilterRegExp(QRegExp('^%s$'%sstyle))
            self.songModelProxy4.setFilterKeyColumn(list(self.songColumns).index('style'))
        else:
            self.songModelProxy4.setFilterWildcard('')
        self.setPageStatusTip('song', 0, self.tblSong.model().rowCount())


    def songAdd(self):
        self.txtSongSearchTitle.setText('')
        self.cmbSongSearchFunc_Singers.setCurrentText('')
        self.cmbSongSearchLanguage.setCurrentText('')
        self.cmbSongSearchStyle.setCurrentText('')

        self.addItem(self.tblSong, self.songColumns, self.songModel)


    def songDelete(self):
        self.deleteItems('song', self.tblSong, self.songRefresh)


    def songSave(self):
        self.saveItems('song', self.tblSong, self.songColumns, self.songRefresh, self.splitsingers)


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
                self.refreshAndSelectRows(self.songRefresh, self.tblSong, ids)


    def songSetSearchChar(self):
        self.setSearchChar('song', 'title', self.songColumns, self.tblSong, self.songRefresh)


    def songFindMedia(self):
        path=lib=self.cmbSongLibrary.currentText()
        filename=self.txtSongMedia_File.text()
        if lib and os.path.isdir(lib) or filename:
            lib = os.path.normpath(lib)
            path = os.path.dirname(os.path.join(lib, filename.lstrip(os.path.sep)))

        qfd=QFileDialog(self, "Open Video", path, "Video (*.avi *.wmv *.mov *.mp* *.mkv *.webm *.rm *.dat *.flv *.vob *.divx *.cdg);;All files (*.*)")
        if lib:
            qfd.directoryEntered.connect(lambda dir: os.path.normpath(dir).startswith(lib) or qfd.setDirectory(lib))
        if qfd.exec():
            filename = os.path.normpath(qfd.selectedFiles()[0])
            if lib and filename.startswith(lib):
                filename=filename[len(lib):]
            self.txtSongMedia_File.setText(filename)


    def songFindMedia2(self):
        path=lib=self.cmbSongLibrary2.currentText()
        filename=self.txtSongMedia_File2.text()
        if lib and os.path.isdir(lib) or filename:
            lib = os.path.normpath(lib)
            path = os.path.dirname(os.path.join(lib, filename.lstrip(os.path.sep)))

        qfd=QFileDialog(self, "Open Video", path, "Video (*.avi *.wmv *.mov *.mp* *.mkv *.webm *.rm *.dat *.flv *.vob *.divx *.cdg);;All files (*.*)")
        if lib:
            qfd.directoryEntered.connect(lambda dir: os.path.normpath(dir).startswith(lib) or qfd.setDirectory(lib))
        if qfd.exec():
            filename = os.path.normpath(qfd.selectedFiles()[0])
            if lib and filename.startswith(lib):
                filename=filename[len(lib):]
            self.txtSongMedia_File2.setText(filename)


    def songTitleEdited(self, txt):
        l=len(txt.strip())
        self.txtSongChars.setText(str(l) if l else '')


    def tblSongMenuRequested(self, pos):
        self.menuSong.exec_(self.sender().viewport().mapToGlobal(pos))


    def convertChinese(self, str, type):
        if QMessageBox.question(self, 'Convert to %s'%str, 'Are you sure?', QMessageBox.YesToAll|QMessageBox.NoToAll)==QMessageBox.NoToAll:
            return
        openCC = OpenCC(type)
        rows = [r.row() for r in self.tblSong.selectionModel().selectedRows()]
        ids=[]
        pos_singers=list(self.songColumns.keys()).index('func_singers')
        pos_title=list(self.songColumns.keys()).index('title')
        for r in rows:
            id=self.tblSong.model().index(r, 1).data(Qt.UserRole)
            cols = self.splitsingers('func_singers', openCC.convert(self.tblSong.model().index(r, pos_singers).data()))
            cols['title'] = openCC.convert(self.tblSong.model().index(r, pos_title).data()).strip()
            settings.dbconn.execute("update song set [%s]=? where id = ?" % ']=?,['.join(cols), list(cols.values()) + [id])
            ids.append(id)
        settings.dbconn.commit()
        self.refreshAndSelectRows(self.songRefresh, self.tblSong, ids)

    def convert2Simplified(self):
        self.convertChinese('Simplified Chinese', 't2s')

    def convert2Traditional(self):
        self.convertChinese('Traditional Chinese', 's2t')

    @staticmethod
    def checkSingleMedia(cmd, file):
        """

        :param cmd: CommandRunner
        :param file: video to check
        :return: error message, None if no error
        """
        if not os.path.isfile(file):
            return 'File not found'
        try:
            cmd.run_command(['ffmpeg', '-i', file, '-c', 'copy', '-f', 'null', NUL])
        except Exception as e:
            settings.logger.printException('Error in %s' % file)
            return 'ffmpeg error: ' + str(e)
        dur=None
        try:
            dur = functions.to_sec(cmd.DUR_REGEX.search(cmd.output).group(1))
        except:
            pass
        try:
            vtime = functions.to_sec(re.search(r'.*\stime=(\d\d:\d\d:\d\d.\d\d)', cmd.output, re.DOTALL).group(1))
        except:
            return 'ffmpeg cant find the video time'
        if not dur and vtime<120:
            return 'Video time seems too short (%.2fs)'%vtime
        if not vtime-2 <= dur <= vtime+2:
            return 'Video time does not match duration (%.2fs)'%(vtime-dur)

    def checkMedias(self):
        rows = [r.row() for r in self.tblSong.selectionModel().selectedRows()]
        progress = QStatusDialog('Checking medias...', 'Stop', 0, len(rows), self, Qt.Dialog | Qt.WindowTitleHint | Qt.CustomizeWindowHint)
        cmd = functions.CommandRunner()
        pos_title=list(self.songColumns.keys()).index('title')
        pos_library=list(self.songColumns.keys()).index('library')
        pos_media=list(self.songColumns.keys()).index('media_file')
        pos_library2=list(self.songColumns.keys()).index('library2')
        pos_media2=list(self.songColumns.keys()).index('media_file2')
        errors=[]

        for i, r in enumerate(tqdm(rows, file=progress.getUpdateClass())):
            progress.setValue(i)
            if progress.wasCanceled():
                break
            library = self.tblSong.model().index(r, pos_library).data()
            mediafile = self.tblSong.model().index(r, pos_media).data()
            videopath = functions.getVideoPath(library, mediafile)
            error=self.checkSingleMedia(cmd, videopath)
            if error:
                errors.append('<tr><td>%s</td><td>%s</td><td>%s</td><td>%s</td></tr>'%(self.tblSong.model().index(r, pos_title).data(),library,mediafile,error))
        progress.setValue(len(rows))
        if errors:
            QLargeMessageBox.warning(self, 'Check medias', 'Errors in these medias', '<table><tr><th>Title</th><th>Library</th><th>Media</th><th>Error</th></tr>'+'\n'.join(errors)+'</table>')
        else:
            QMessageBox.information(self, 'Check medias', 'No errors found.')


    def setVolume(self):
        rows = [r.row() for r in self.tblSong.selectionModel().selectedRows()]
        if len(rows)>1 and QMessageBox.question(self, 'Set volume', 'Program will scan each file to find the suitable volume.<br><b>This will take very long.</b><br><br>Are you sure?', QMessageBox.YesToAll|QMessageBox.NoToAll)==QMessageBox.NoToAll:
            return

        def getVolume(videopath, maxbar, pbar):
            goalLUFS = -14
            maxPeak = -1
            prevp = 0

            cmd = functions.CommandRunner()
            cmd.run_command(['ffmpeg', '-hide_banner', '-i', videopath])
            numaudiotracks=len(re.findall(r"\s*Stream .* Audio:", cmd.output))

            gain=[]
            for i in range(numaudiotracks):
                for p in cmd.run_ffmpeg_command(['ffmpeg', '-hide_banner', '-i', videopath, '-vn', '-filter_complex', '[0:a:%i]ebur128=dualmono=true:peak=true'%i, '-f', 'null', NUL]):
                    p2=int((i/numaudiotracks+p/numaudiotracks)/maxbar)
                    if prevp != p2:
                        pbar.update(p2 - prevp)
                        prevp = p2

                summaryList = cmd.output[cmd.output.rfind('Summary:'):].split()
                LUFS = float(summaryList[summaryList.index('I:') + 1])
                Peak = float(summaryList[summaryList.index('Peak:') + 1])

                gainDB = goalLUFS - LUFS
                if gainDB > 0 and Peak + gainDB > maxPeak:
                    if Peak < maxPeak:
                        gainDB = maxPeak - Peak
                    else:
                        gainDB = 0
                gain.append(str(round(gainDB,3)))

                if prevp < maxbar:
                    pbar.update(maxbar - prevp)

            return gain

        def setVolumeTask(id, videopath, videopath2, pbar):
            gain = []

            try:
                maxbar = 2 if videopath2 else 1
                gain.extend(getVolume(videopath, maxbar, pbar))
                if videopath2:
                    gain.extend(getVolume(videopath2, maxbar, pbar))

                # new thread, need to create new SQLite objects
                dbconn = functions.createDatabase()
                dbconn.execute("update song set [volume]=? where id = ?", (",".join(gain), id,))
                dbconn.commit()
                dbconn.close()
            except:
                settings.logger.printException()

        ids = [r.data(Qt.UserRole) for r in self.tblSong.selectionModel().selectedRows()]
        progress = QStatusDialog('Scanning medias for volume...', 'Stop', 0, len(rows) * 100, self,
                                 Qt.Dialog | Qt.WindowTitleHint | Qt.CustomizeWindowHint)
        progress.setMinimumDuration(0)
        pos_library = list(self.songColumns.keys()).index('library')
        pos_media = list(self.songColumns.keys()).index('media_file')
        pos_library2=list(self.songColumns.keys()).index('library2')
        pos_media2=list(self.songColumns.keys()).index('media_file2')
        pbar = tqdm(total=len(rows) * 100, file=progress.getUpdateClass())

        # m = multiprocessing.Manager()
        # lock = m.Lock()
        numthreads=1 ### to-do - crash when running multithread
        with concurrent.futures.ThreadPoolExecutor(numthreads) as executor:
            furtures=[]
            for r in rows:
                library = self.tblSong.model().index(r, pos_library).data()
                mediafile = self.tblSong.model().index(r, pos_media).data()
                videopath = functions.getVideoPath(library, mediafile, True)
                library2 = self.tblSong.model().index(r, pos_library2).data()
                mediafile2 = self.tblSong.model().index(r, pos_media2).data()
                videopath2 = functions.getVideoPath(library2, mediafile2, True)
                id = self.tblSong.model().index(r, 1).data(Qt.UserRole)
                furtures.append(executor.submit(setVolumeTask, id, videopath, videopath2, pbar))

            progress.setLabelSubText('Processing %s of %s' % (0, len(rows)))
            while len(furtures)>0:
                if progress.wasCanceled():
                    pbar.close()
                    progress.setCancelButton(None)
                    progress.setLabelMainText('Cancelling, please wait...')
                    [furtures.remove(f) for f in furtures if f.cancel()]
                try:
                    f = next(concurrent.futures.as_completed(furtures, 0.25))
                    if f:
                        furtures.remove(f)
                        progress.setLabelSubText('Processing %s of %s' %(len(rows)-len(furtures), len(rows)))
                except concurrent.futures.TimeoutError:
                    pass
                qApp.processEvents()

        progress.setValue(len(rows) * 100)
        self.refreshAndSelectRows(self.songRefresh, self.tblSong, ids)

        # Alternative code using QThreadPool, but does not show the number of files processed
        #
        # class setVolumeTask(QRunnable):
        #     goalLUFS = -14
        #     maxPeak = -1
        #
        #     def __init__(self, id, videopath, pbar):
        #         super().__init__()
        #         self.id=id
        #         self.videopath=videopath
        #         self.pbar=pbar
        #
        #     def run(self):
        #         try:
        #             prevp = 0
        #             cmd = functions.CommandRunner()
        #             for p in cmd.run_ffmpeg_command(['ffmpeg', '-i', self.videopath, '-vn', '-filter_complex', 'ebur128=dualmono=true:peak=true', '-f', 'null', NUL]):
        #                 if prevp!=p:
        #                     self.pbar.update(p-prevp)
        #                     prevp=p
        #             summaryList = cmd.output[cmd.output.rfind('Summary:'):].split()
        #             LUFS = float(summaryList[summaryList.index('I:') + 1])
        #             Peak = float(summaryList[summaryList.index('Peak:') + 1])
        #
        #             gainDB = self.goalLUFS-LUFS
        #             if gainDB>0 and Peak+gainDB > self.maxPeak:
        #                 if Peak<self.maxPeak:
        #                     gainDB=self.maxPeak-Peak
        #                 else:
        #                     gainDB=0
        #
        #             # new thread, need to create new SQLite objects
        #             dbconn=functions.createDatabase()
        #             dbconn.execute("update song set [volume]=? where id = ?", (round(gainDB,3), id,))
        #             dbconn.commit()
        #         except:
        #             settings.logger.printException()
        #
        # rows = [r.row() for r in self.tblSong.selectionModel().selectedRows()]
        # ids=[r.data(Qt.UserRole) for r in self.tblSong.selectionModel().selectedRows()]
        # progress = QStatusDialog('Scanning medias for volume...', 'Stop', 0, len(rows)*100, self, Qt.Dialog | Qt.WindowTitleHint | Qt.CustomizeWindowHint)
        # progress.setMinimumDuration(0)
        # pos_library=list(self.songColumns.keys()).index('library')
        # pos_media=list(self.songColumns.keys()).index('media_file')
        # pbar = tqdm(total=len(rows) * 100, file=progress.getUpdateClass())
        # pool = QThreadPool()
        # pool.setMaxThreadCount(int(os.cpu_count()*2))
        #
        # for r in rows:
        #     library = self.tblSong.model().index(r, pos_library).data()
        #     mediafile = self.tblSong.model().index(r, pos_media).data()
        #     videopath=mediafile if library=='' else os.path.join(library, mediafile.lstrip(os.path.sep))
        #     id = self.tblSong.model().index(r, 1).data(Qt.UserRole)
        #     pool.start(setVolumeTask(id, videopath, pbar))
        #
        # while not pool.waitForDone(25):
        #     if progress.wasCanceled():
        #         pool.clear()
        #         pbar.close()
        #         progress.setCancelButton(None)
        #         progress.setLabelMainText('Stopping current ffmpeg, please wait...')
        #     qApp.processEvents()
        #
        # progress.setValue(len(rows) * 100)
        # self.refreshAndSelectRows(self.songRefresh, self.tblSong, ids)


    ### media player functions

    previousplaying=-1
    sliderpressed=False
    volumestr=''


    def songPlayPause(self):
        rows = self.tblSong.selectionModel().selectedRows()
        player=self.mpvMediaPlayer
        if len(rows)==1 and (player.idle_active or self.previousplaying!=rows[0].data()):
            library = rows[0].sibling(rows[0].row(), list(self.songColumns.keys()).index('library')).data()
            mediafile = rows[0].sibling(rows[0].row(), list(self.songColumns.keys()).index('media_file')).data()
            library2 = rows[0].sibling(rows[0].row(), list(self.songColumns.keys()).index('library2')).data()
            mediafile2 = rows[0].sibling(rows[0].row(), list(self.songColumns.keys()).index('media_file2')).data()
            self.volume = rows[0].sibling(rows[0].row(), list(self.songColumns.keys()).index('volume')).data().split(',')
            if not self.volume or not self.volume[0]:
                self.volume=['0']
            videopath = functions.getVideoPath(library, mediafile)
            videopath2 = functions.getVideoPath(library2, mediafile2, True)
            mpv_opts = {'external_files': videopath2} if videopath2 else {}
            print(mpv_opts)
            player.loadfile(videopath, **mpv_opts)
            time.sleep(0.2) # not sure why some songs need to wait, else it'll crash
            player.aid = 1
            volumestr='lavfi="volume=volume=%sdB"'%self.volume[0]
            player.command('af', 'set', volumestr)
            self.channel=''
            self.previousplaying=rows[0].data()
            self.statusBar.showMessage(videopath)
        else:
            if player.duration:
                player.cycle('pause')

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
                if self.channel==i or (self.channel in ['','L','R'] and i==0):
                    action.setCheckable(True)
                    action.setChecked(True)

        action = menu.exec_(self.btnSongAudio.mapToGlobal(QPoint(0,0)))

        if action:
            action = action.text()
            self.mpvMediaPlayer.aid = 1
            if action=='Stereo':
                self.mpvMediaPlayer.command('af', 'set', 'lavfi="volume=volume=%sdB"'%self.volume[0])
                self.channel=''
            elif action=='Left':
                self.mpvMediaPlayer.command('af', 'set', 'pan="mono|c0=c0",' + 'lavfi="volume=volume=%sdB"'%self.volume[0])
                self.channel='L'
            elif action == 'Right':
                self.mpvMediaPlayer.command('af', 'set', 'pan="mono|c0=c1",' + 'lavfi="volume=volume=%sdB"'%self.volume[0])
                self.channel='R'
            elif action.startswith('Track '):
                try:
                    ch = int(action[6:])
                    self.mpvMediaPlayer.aid = ch+1
                    volumestr = 'lavfi="volume=volume=%sdB"'%self.volume[ch] if ch<len(self.volume) else 'lavfi="volume=volume=0dB"'
                    self.mpvMediaPlayer.command('af', 'set', volumestr)
                    self.channel = '' if ch==0 else ch
                except:
                    pass




    """ singer functions """

    @staticmethod
    def getSingerRegionModel():
        rows = settings.dbconn.execute('select "" union select distinct region from singer order by region')
        return QStringListModel([r[0] for r in rows])

    @staticmethod
    def getSingerTypeModel():
        rows = settings.dbconn.execute('select "" union select type region from singer order by type')
        return QStringListModel([r[0] for r in rows])


    singerColumns = OrderedDict({
        'id': {'title': 'ID'},
        'name': {'title': 'Name', 'type': str},
        'search': {'title': 'Search letter', 'itemdelegateclass': QLineEditDelegate, 'validator': QUpperValidator(QRegExp('[0-9a-zA-Z]+')), 'type': str},
        'region': {'title': 'Region', 'itemdelegateclass': QComboBoxDelegate, 'getmodel': getSingerRegionModel.__func__, 'type': str},
        'type': {'title': 'Category', 'itemdelegateclass': QComboBoxDelegate, 'getmodel': getSingerTypeModel.__func__, 'type': str},
        'remark': {'title': 'Remark', 'type': str}
    })


    def __singer__init__(self):
        self.singerModel = QStandardItemModel()
        self.singerModel.itemChanged.connect(self.saveItem)
        self.singerModelProxy1 = QSortFilterProxyModel()
        self.singerModelProxy1.setSourceModel(self.singerModel)
        self.singerModelProxy2 = QSortFilterProxyModel()
        self.singerModelProxy2.setSourceModel(self.singerModelProxy1)
        self.singerModelProxy3 = QSortFilterProxyModel()
        self.singerModelProxy3.setSortRole(Qt.UserRole+1)
        self.singerModelProxy3.setSortCaseSensitivity(Qt.CaseInsensitive)
        self.singerModelProxy3.setSourceModel(self.singerModelProxy2)

        self.tblSinger.setModel(self.singerModelProxy3)
        self.tblSinger.selectionModel().selectionChanged.connect(self.singerSelectionChanged)

        self.txtSingerSearchName.textChanged.connect(self.singerSearch)
        self.cmbSingerSearchRegion.currentIndexChanged.connect(self.singerSearch)
        self.cmbSingerSearchType.currentIndexChanged.connect(self.singerSearch)
        self.btnSingerAdd.clicked.connect(self.singerAdd)
        self.btnSingerDelete.clicked.connect(self.singerDelete)
        self.btnSingerSave.clicked.connect(self.singerSave)

        self.btnSingerSearch.clicked.connect(self.singerSetSearchChar)

        self.setInputValidators('singer', self.singerColumns)


        self.refreshcomboboxes.connect(lambda:self.setComboBoxModal('singer', self.singerColumns))
        self.singerRefresh()
        self.tblSinger.sortByColumn(1, Qt.AscendingOrder)


    def singerRefresh(self):
        self.refreshFromDB('singer', self.tblSinger, self.singerColumns, self.singerModel)
        self.setPageStatusTip('singer', 0, self.singerModel.rowCount())


    def singerSelectionChanged(self, selected=None, deselected=None):
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
        self.singerModelProxy1.setFilterWildcard(self.txtSingerSearchName.text().strip())
        self.singerModelProxy1.setFilterKeyColumn(list(self.singerColumns).index('name'))
        sregion=self.cmbSingerSearchRegion.currentText()
        if sregion:
            self.singerModelProxy2.setFilterRegExp(QRegExp('^%s$'%sregion))
            self.singerModelProxy2.setFilterKeyColumn(list(self.singerColumns).index('region'))
        else:
            self.singerModelProxy2.setFilterWildcard('')
        stype=self.cmbSingerSearchType.currentText()
        if stype:
            self.singerModelProxy3.setFilterRegExp(QRegExp('^%s$'%stype))
            self.singerModelProxy3.setFilterKeyColumn(list(self.singerColumns).index('type'))
        else:
            self.singerModelProxy3.setFilterWildcard('')
        self.setPageStatusTip('singer', 0, self.tblSinger.model().rowCount())


    def singerAdd(self):
        self.txtSingerSearchName.setText('')
        self.cmbSingerSearchRegion.setCurrentText('')
        self.cmbSingerSearchType.setCurrentText('')

        self.addItem(self.tblSinger, self.singerColumns, self.singerModel)


    def singerDelete(self):
        self.deleteItems('singer', self.tblSinger, self.singerRefresh)


    def singerSave(self):
        self.saveItems('singer', self.tblSinger, self.singerColumns, self.singerRefresh)


    def singerSetSearchChar(self):
        self.setSearchChar('singer', 'name', self.singerColumns, self.tblSinger, self.singerRefresh)



    """ library functions """


    libraryColumns = OrderedDict({'id':{'title':'ID'}, 'root_path':{'title':'Root Path'},
                                  'enabled':{'title':'Enable','itemdelegateclass': QLineEditDelegate, 'validator': QIntValidator(0, 1)},
                                  'mirror1':{'title':'Mirror1'}, 'mirror2':{'title':'Mirror2'}, 'mirror3':{'title':'Mirror3'},
                                  'mirror4':{'title':'Mirror4'}, 'mirror5':{'title':'Mirror5'}, 'mirror6':{'title':'Mirror6'},
                                  'mirror7':{'title':'Mirror7'}, 'mirror8':{'title':'Mirror8'}, 'mirror9':{'title':'Mirror9'},
                                  'mirror10':{'title':'Mirror10'}})


    def __library__init__(self):
        self.libraryModel = QStandardItemModel()
        self.libraryModelProxy1 = QSortFilterProxyModel()
        self.libraryModelProxy1.setSortRole(Qt.UserRole+1)
        self.libraryModelProxy1.setSortCaseSensitivity(Qt.CaseInsensitive)
        self.libraryModelProxy1.setSourceModel(self.libraryModel)

        self.tblLibrary.setModel(self.libraryModelProxy1)
        self.tblLibrary.selectionModel().selectionChanged.connect(self.librarySelectionChanged)

        self.btnLibraryAdd.clicked.connect(self.libraryAdd)
        self.btnLibraryDelete.clicked.connect(self.libraryDelete)
        self.btnLibrarySave.clicked.connect(self.librarySave)

        for btn in [self.btnLibraryRoot_Path, self.btnLibraryMirror1, self.btnLibraryMirror2, self.btnLibraryMirror3, self.btnLibraryMirror4, self.btnLibraryMirror5, self.btnLibraryMirror6, self.btnLibraryMirror7, self.btnLibraryMirror8, self.btnLibraryMirror9, self.btnLibraryMirror10]:
            btn.clicked.connect(self.libraryBrowse)

        self.setInputValidators('library', self.libraryColumns)

        self.libraryRefresh()
        self.tblLibrary.sortByColumn(1, Qt.AscendingOrder)


    def libraryRefresh(self):
        self.refreshFromDB('library', self.tblLibrary, self.libraryColumns, self.libraryModel)
        self.setPageStatusTip('library', 0, self.libraryModel.rowCount())


    def librarySelectionChanged(self, selected=None, deselected=None):
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
            lbl.setText(os.path.normpath(dir))



    """ youtube functions """


    youtubeColumns = OrderedDict({'id':{'title':'ID'}, 'name':{'title':'Name', 'type': str},
                                  'user':{'title':'User', 'type': str}, 'url':{'title':'URL', 'type': str},
                                  'enable': {'title': 'Enable', 'itemdelegateclass': QLineEditDelegate,'validator': QIntValidator(0, 1)}})


    def __youtube__init__(self):
        self.youtubeModel = QStandardItemModel()
        self.youtubeModel.itemChanged.connect(self.saveItem)
        self.youtubeModelProxy1 = QSortFilterProxyModel()
        self.youtubeModelProxy1.setSortRole(Qt.UserRole+1)
        self.youtubeModelProxy1.setSortCaseSensitivity(Qt.CaseInsensitive)
        self.youtubeModelProxy1.setSourceModel(self.youtubeModel)

        self.tblYoutube.setModel(self.youtubeModelProxy1)
        self.tblYoutube.selectionModel().selectionChanged.connect(self.youtubeSelectionChanged)

        self.btnYoutubeAdd.clicked.connect(self.youtubeAdd)
        self.btnYoutubeDelete.clicked.connect(self.youtubeDelete)
        self.btnYoutubeSave.clicked.connect(self.youtubeSave)

        self.setInputValidators('youtube', self.youtubeColumns)

        self.youtubeRefresh()
        self.tblYoutube.sortByColumn(1, Qt.AscendingOrder)


    def youtubeRefresh(self):
        self.refreshFromDB('youtube', self.tblYoutube, self.youtubeColumns, self.youtubeModel)
        self.setPageStatusTip('youtube', 0, self.youtubeModel.rowCount())


    def youtubeSelectionChanged(self, selected=None, deselected=None):
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
        medias=['<tr><td>'+str(r[0])+'</td><td>'+r[1]+'</td><td>'+r[2]+'</td></tr>' for r in rows]
        if medias:
            QLargeMessageBox.warning(self, 'Search duplicate media',
                                     str(len(medias)) + " media(s) are found in duplicates:",
                                     "<table><tr><th>Duplicates</th><th>Library</th><th>Media</th></tr>"+"\n".join(medias)+"</table>")
        else:
            QMessageBox.information(self, "Search duplicate media", "No duplicate media found")


    def searchDuplicateSong(self):
        rows = settings.dbconn.execute("select count(id), trim(title) title from song where title<>'' group by title having count(id)>1")
        songs = rows.fetchall()
        if songs:
            titles=[r[1] for r in songs]
            rows = settings.dbconn.execute("select singer, singer2, singer3, singer4, singer5, singer6, singer7, singer8, singer9, singer10, "
                                           "trim(title) title from song where trim(title) in (%s)" % ','.join('?'*len(titles)), titles)
            singers = rows.fetchall()
            message=['<tr><td>'+str(r[0])+'</td><td>'+r[1]+'</td><td>' +
                     ','.join( [','.join(filter(None,s[:-1])) for s in singers if s['title']==r[1]] ) +
                     '</td></tr>'
                     for r in songs]

            QLargeMessageBox.warning(self, 'Search duplicate song',
                                     str(len(songs)) + " song(s) are found in duplicates:",
                                     "<table><tr><th>Duplicates</th><th>Song</th><th>Singers</th></tr>"+"\n".join(message)+"</table>")
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
        self.tblMedia.horizontalHeader().sectionClicked.connect(self.headerClicked)
        self.tblMedia.horizontalHeader().sortIndicatorChanged.connect(self.checkSortOrder)

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
            file_exts = '.avi *.wmv *.mov *.mp* *.mkv *.webm *.rm *.dat *.flv *.vob *.divx *.cdg'.split(' ')
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
            swapbutton = QPushButton('⮀')
            swapbutton.swapStandardItem=swap.index()
            swapbutton.clicked.connect(self.swapTitleSinger)
            self.tblMedia.setIndexWidget(self.mediaModelProxy1.mapFromSource(swap.index()), swapbutton)

        if files:
            self.mediaModel.setHeaderData(0, Qt.Horizontal, '☑') # ☐
            self.mediaModel.setHeaderData(1, Qt.Horizontal, 'Title')
            self.mediaModel.setHeaderData(2, Qt.Horizontal, '⮀')
            self.mediaModel.setHeaderData(3, Qt.Horizontal, 'Singers')
            self.mediaModel.setHeaderData(4, Qt.Horizontal, 'Media File')

            self.tblMedia.resizeColumnsToContents()
            self.tblMedia.horizontalHeader().resizeSection(0, 25)
            self.tblMedia.horizontalHeader().setSectionResizeMode(0, QHeaderView.Fixed)
            self.tblMedia.horizontalHeader().resizeSection(2, 25)
            self.tblMedia.horizontalHeader().setSectionResizeMode(2, QHeaderView.Fixed)

            self.previoussortscection = 5
            self.previoussortorder = 1
        else:
            QMessageBox.information(self, "Search new media", "No new media found")


    def swapTitleSinger(self, checked=False, row=None):
        if row is None:
            row=self.sender().swapStandardItem.row()
        t=self.mediaModel.item(row, 1).data(Qt.DisplayRole)
        self.mediaModel.item(row, 1).setData(self.mediaModel.item(row, 3).data(Qt.DisplayRole), Qt.DisplayRole)
        self.mediaModel.item(row, 3).setData(t, Qt.DisplayRole)


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


    def headerClicked(self, index):
        if index==0:
            if self.mediaModel.headerData(0, Qt.Horizontal)=='☑':
                c=Qt.Unchecked
                self.mediaModel.setHeaderData(0, Qt.Horizontal, '☐')
            else:
                c=Qt.Checked
                self.mediaModel.setHeaderData(0, Qt.Horizontal, '☑')
            for j in range(self.mediaModel.rowCount()):
                self.mediaModel.item(j, 0).setCheckState(c)
        elif index==2:
            for j in range(self.mediaModel.rowCount()):
                self.swapTitleSinger(False, j)


    def checkSortOrder(self, index, order):
        if index==0 or index==2:
            self.tblMedia.horizontalHeader().setSortIndicator(self.previoussortscection, self.previoussortorder)
        else:
            self.previoussortscection=self.tblMedia.horizontalHeader().sortIndicatorSection()
            self.previoussortorder=self.tblMedia.horizontalHeader().sortIndicatorOrder()


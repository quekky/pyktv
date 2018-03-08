
import sys
import os
import math
import re
from PyQt5.QtCore import pyqtSlot, QTimer, QThread
from PyQt5.QtWidgets import QApplication
from youtube_dl import YoutubeDL
from pprint import pprint

import settings
import playlist
from xpinyin import Pinyin




"""implemnet history, for the back button"""
browserhistory = []

def addHistory(func, data, allowduplicate=False):
    global browserhistory
    if allowduplicate or len(browserhistory)==0 or browserhistory[len(browserhistory)-1][0]!=func:
        browserhistory.append([func, data, -1])

def setHistoryPage(page):
    global browserhistory
    browserhistory[len(browserhistory)-1][2]=page

def getHistoryPage():
    global browserhistory
    return browserhistory[len(browserhistory)-1][2]

def backcallback(data):
    global browserhistory
    try:
        browserhistory.pop()
        (func,data,page) = browserhistory.pop()
        while not callable(func):
            (func, data, page) = browserhistory.pop()
        if page>=0:
            func(data, page)
        else:
            func(data)
    except IndexError:
        startHomeScreen(None)


"""
Home page
"""

@pyqtSlot(object, int)
def startHomeScreen(data=None, page=None):
    h_options = {0: {'text': _('F1:Search Songs'), 'func': titleSearch},
                 1: {'text': _('F2:Index Search'), 'func': indexSearch},
                 2: {'text': _('F3:Playlist'), 'func': playelistSearch}
                 #3: {'text': _('F4:Video'), 'func':None}
                 }
    # c_options = {0: {'text': 'Index', 'func': indexSearch},
    #              1: {'text': 'Title', 'func': titleSearch},
    #              2: {'text': 'Artist', 'func': artistSearch1},
    #              3: {'text': 'Language', 'func': None},
    #              4: {'text': 'Category', 'func': None},
    #              5: {'text': 'Char number', 'func': None},
    #              6: {'text': 'Popular', 'func': None},
    #              7: {'text': 'Media file', 'func': None},
    #              8: {'text': 'Playlist', 'func': None},
    #              9: {'text': 'More functions', 'func': None}}

    c_options = {0: {'text': _('Index'), 'func': indexSearch},
                 1: {'text': _('Title'), 'func': titleSearch},
                 2: {'text': _('Artist'), 'func': artistSearch1},
                 3: {'text': _('Language'), 'func': langSearch1},
                 4: {'text': _('Category'), 'func': categorySearch1},
                 5: {'text': _('Char number'), 'func': charSearch1},
                 # 6: {'text': _('Popular'), 'func': None},
                 9: {'text': _('Youtube'), 'func': youtubeScreen1}
                 }
    global browserhistory
    browserhistory.clear()
    settings.selectorWindow.setHeaders(h_options)
    settings.selectorWindow.setContents(0, c_options)
    settings.selectorWindow.setFooters({})
    settings.selectorWindow.setBackCallback(backcallback)

"""
Generic Functions
"""

def extractSingersAndSetDisplay(song, prefix=''):
    singers=[song['singer']]
    for i in range(2,11):
        if song['singer'+str(i)]!='':
            singers.append(song['singer'+str(i)])
    song['singers']=singers
    setDisplaySongText(song, prefix)

def setDisplaySongText(song, prefix=''):
    song['display'] = prefix + song['title'] + " 《" + ",".join(song['singers']) + '》  （' + song['language'] + '）'


"""
Functions related to searching songs
"""

def getCommon1_h_options():
    return {0: {'text': _('F1:Search Songs'), 'func': titleSearch},
            1: {'text': _('F2:Index Search'), 'func': indexSearch},
            2: {'text': _('F3:Playlist'), 'func': playelistSearch}
            #3: {'text': _('F4:Video'), 'func': None}
            }

def getCommon2_h_options():
    return {0: {'text': _('F1:Search'), 'search': 1}, #if ['search']=1, then calls the builtin pagerContent.searcher
            1: {'text': _('F2:Index Search'), 'func': indexSearch},
            2: {'text': _('F3:Playlist'), 'func': playelistSearch}
            #3: {'text': 'F4:Video', 'func': None}
            }

@pyqtSlot(object, int)
def titleSearch(data=None, page=0):
    addHistory(titleSearch, data)

    rows = settings.dbconn.execute("select * from song where [index]!=0 order by title COLLATE NOCASE")

    tracks = []
    for r in rows:
        d=dict(r)
        extractSingersAndSetDisplay(d)
        tracks.append(d)

    try:
        pager = pagerContent(tracks, 1, getCommon1_h_options(), playlist.addVideo)
        pager.startSearch(page,0 )
    except:
        print("error", sys.exc_info())


@pyqtSlot(object, int)
def indexSearch(data=None, page=0):
    # print('find music by index')
    addHistory(indexSearch, data)

    rows = settings.dbconn.execute("select * from song where [index]!=0 order by [index]")

    tracks = []
    for r in rows:
        d=dict(r)
        extractSingersAndSetDisplay(d, str(d['index']) + ' - ')
        tracks.append(d)

    try:
        pager = pagerContent(tracks, 1, getCommon1_h_options(), playlist.addVideo)
        pager.startSearch(page,1 )
    except:
        print("error", sys.exc_info())


@pyqtSlot(object, int)
def artistSearch1(data=None, page=0):
    # print('find music by artist 1')
    addHistory(artistSearch1, data)

    rows = settings.dbconn.execute("select distinct region from singer where region!='' order by region COLLATE NOCASE")

    artists = [{'display': _('All Artist'), 'region': ''}]
    for r in rows:
        artists.append({'display':r[0],'region':r[0]})

    try:
        pager = pagerContent(artists, 1, getCommon1_h_options(), artistSearch2)
        pager.startDisplay(page)
    except:
        print("error", sys.exc_info())


@pyqtSlot(object, int)
def artistSearch2(data, page=0):
    # print('find music by artist 2', data)
    addHistory(artistSearch2, data)
    region=data['region']
    if region=='':
        rows = settings.dbconn.execute("select distinct type from singer where type!='' order by type COLLATE NOCASE")
    else:
        rows = settings.dbconn.execute("select distinct type from singer where type!='' and region=? order by type", (region,))

    artists = [{'display': _('All Category'), 'region': region, 'type': ''}]
    for r in rows:
        artists.append({'display':r[0], 'region':region, 'type':r[0]})

    try:
        pager = pagerContent(artists, 1, getCommon1_h_options(), artistSearch3)
        pager.startDisplay(page)
    except:
        print("error", sys.exc_info())


@pyqtSlot(object, int)
def artistSearch3(data, page=0):
    # print('find music by artist 3', data)
    addHistory(artistSearch3, data)
    region = data['region']
    type1 = data['type']
    if region=='' and type1=='':
        query="?=?"
    elif region=='':
        query="?='' and type==?"
    elif type1=='':
        query="region=? and ?=''"
    else:
        query="region=? and type=?"

    try:
        rows = settings.dbconn.execute("select * from singer where " + query + " and name!='' order by name COLLATE NOCASE", (region, type1,))
        singerdir = settings.config['singer.picture']

        artists = []
        for r in rows:
            d = dict(r)
            d['display'] = d['name']
            image = os.path.join(singerdir, r['name']+'.jpg')
            if os.path.isfile(image):
                d['image']=image
            artists.append(d)
    except:
        print(sys.exc_info())

    try:
        pager = pagerContent(artists, 2, getCommon2_h_options(), artistSearch4)
        pager.startDisplay(page)
    except:
        print("error", sys.exc_info())


@pyqtSlot(object, int)
def artistSearch4(data, page=0):
    # print('find music by artist 4', data)
    addHistory(artistSearch4, data)
    rows = settings.dbconn.execute(
        "select * from song where [index]!=0 and (singer=? or singer2=? or singer3=? or singer4=? or singer5=? or singer6=? or singer7=? or singer8=? or singer9=? or singer10=? ) order by title COLLATE NOCASE",
        [data['name']] * 10)

    tracks = []
    for r in rows:
        d=dict(r)
        extractSingersAndSetDisplay(d)
        tracks.append(d)

    try:
        h_options=getCommon2_h_options()
        h_options[0]['search']=2
        pager = pagerContent(tracks, 1, h_options, playlist.addVideo)
        pager.startDisplay(page)
    except:
        print("error", sys.exc_info())


@pyqtSlot(object, int)
def langSearch1(data=None, page=0):
    # print('find music by lang 1')
    addHistory(langSearch1, data)

    rows = settings.dbconn.execute("select distinct language from song where language!='' order by language COLLATE NOCASE")

    langs = []
    #langs.append({'display':'All Language','language':''})
    for r in rows:
        langs.append({'display':r[0],'language':r[0]})

    try:
        pager = pagerContent(langs, 1, getCommon1_h_options(), langSearch2)
        pager.startDisplay(page)
    except:
        print("error", sys.exc_info())


@pyqtSlot(object, int)
def langSearch2(data, page=0):
    # print('find music by lang 2', data)
    addHistory(langSearch2, data)
    language = data['language']
    rows = settings.dbconn.execute("select * from song where [index]!=0 and language=? order by title COLLATE NOCASE", (language,))

    tracks = []
    for r in rows:
        d=dict(r)
        d['display ']= d['title']+" 《"+d['singer']+'》  （'+d['language']+'）'
        tracks.append(d)

    try:
        pager = pagerContent(tracks, 1, getCommon2_h_options(), playlist.addVideo)
        pager.startDisplay(page)
    except:
        print("error", sys.exc_info())


@pyqtSlot(object, int)
def categorySearch1(data=None, page=0):
    # print('find music by category 1')
    addHistory(categorySearch1, data)

    rows = settings.dbconn.execute("select distinct style from song where style!='' order by style COLLATE NOCASE")

    cats = []
    #cats.append({'display':'All Category','style':''})
    for r in rows:
        cats.append({'display':r[0],'style':r[0]})

    try:
        pager = pagerContent(cats, 1, getCommon1_h_options(), categorySearch2)
        pager.startDisplay(page)
    except:
        print("error", sys.exc_info())


@pyqtSlot(object, int)
def categorySearch2(data, page=0):
    # print('find music by category 2', data)
    addHistory(categorySearch2, data)
    style = data['style']
    rows = settings.dbconn.execute("select * from song where [index]!=0 and style=? order by title COLLATE NOCASE", (style,))

    tracks = []
    for r in rows:
        d=dict(r)
        d['display ']= d['title']+" 《"+d['singer']+'》  （'+d['language']+'）'
        tracks.append(d)

    try:
        pager = pagerContent(tracks, 1, getCommon2_h_options(), playlist.addVideo)
        pager.startDisplay(page)
    except:
        print("error", sys.exc_info())


@pyqtSlot(object, int)
def charSearch1(data=None, page=0):
    # print('find music by char 1')
    addHistory(charSearch1, data)

    chars = []
    for r in range(1,10):
        chars.append({'display':_('{} character').format(r),'index':r})
    chars.append({'display':_('{} character').format(10)+_('s and above'),'index':10})

    try:
        pager = pagerContent(chars, 1, getCommon1_h_options(), charSearch2)
        pager.startDisplay(page)
    except:
        print("error", sys.exc_info())


@pyqtSlot(object, int)
def charSearch2(data, page=0):
    # print('find music by char 2', data)
    addHistory(charSearch2, data)
    index = data['index']
    if index==10:
        rows = settings.dbconn.execute("select * from song where [index]!=0 and chars>=10 order by title COLLATE NOCASE")
    else:
        rows = settings.dbconn.execute("select * from song where [index]!=0 and chars=? order by title COLLATE NOCASE", (index,))

    tracks = []
    for r in rows:
        d=dict(r)
        extractSingersAndSetDisplay(d)
        tracks.append(d)

    try:
        pager = pagerContent(tracks, 1, getCommon2_h_options(), playlist.addVideo)
        pager.startDisplay(page)
    except:
        print("error", sys.exc_info())

"""
Functions related to playlist
"""

@pyqtSlot(object, int)
def playelistSearch(data=None, page=0):
    # print('show playlist')
    global playlistSelection
    addHistory(playelistSearch, None)

    playlistSelection=''
    h_options = {0: {'text': _('F1:Priority'), 'func': prioritySongPlaylist},
                 2: {'text': _('F3:Delete'), 'func': deleteSongPlaylist}}

    try:
        pager = pagerContent(list(playlist.video_playlist), 1, h_options, songPlaylistSelected)
        pager.startDisplay(page)
    except:
        print("error", sys.exc_info())


@pyqtSlot(object, int)
def prioritySongPlaylist(data=None, page=0):
    global playlistSelection
    playlistSelection='priority'
    h_options = {0: {'text': _('[Priority]')},
                 1: {'text': _('Choose song')},
                 3: {'text': _('F4:Cancel'), 'func': cancelSongPlaylist}}
    settings.selectorWindow.setHeaders(h_options)


@pyqtSlot(object, int)
def deleteSongPlaylist(data=None, page=0):
    global playlistSelection
    playlistSelection='delete'
    h_options = {0: {'text': _('[Delete]')},
                 1: {'text': _('Choose song')},
                 3: {'text': _('F4:Cancel'), 'func': cancelSongPlaylist}}
    settings.selectorWindow.setHeaders(h_options)


@pyqtSlot(object, int)
def cancelSongPlaylist(data=None, page=0):
    global playlistSelection
    playlistSelection=''
    playelistSearch()


@pyqtSlot(object, int)
def songPlaylistSelected(data, page=0):
    global playlistSelection
    if playlistSelection=='priority':
        playlist.piroritySong(data)
        playelistSearch()
    elif playlistSelection=='delete':
        playlist.deleteSong(data)
        playelistSearch(page=getHistoryPage())


"""
Functions related to youtube
"""

class youtubeLogger(object):
    def debug(self, msg):
        settings.selectorWindow.setTempStatusText(msg, 500)
        #refresh the app, if not the video will hang while processing
        QApplication.processEvents()

    def warning(self, msg):
        pass

    def error(self, msg):
        print("Error:",msg)

@pyqtSlot(object, int)
def youtubeScreen1(data=None, page=0):
    addHistory(youtubeScreen1, data)
    rows = settings.dbconn.execute("select * from youtube where enable!=0 order by name COLLATE NOCASE, user COLLATE NOCASE")

    try:
        pinyin=Pinyin()
        youtubelists = []
        for r in rows:
            d = dict(r)
            d['display'] = d['name']+" 《"+d['user']+'》'
            d['search'] = pinyin.get_initials(d['name'], '').upper()
            youtubelists.append(d)

        pager = pagerContent(youtubelists, 1, getCommon2_h_options(), youtubeScreen2)
        pager.startDisplay(page)
    except:
        print("error", sys.exc_info())

@pyqtSlot(object, int)
def youtubeScreen2(data=None, page=0):
    addHistory(youtubeScreen2, data, True)

    try:
        settings.selectorWindow.setTempStatusText("Youtube: downloading list...", 1000)
        ydl = YoutubeDL({'quiet':False,'extract_flat':True,'dump_single_json':True,'logger':youtubeLogger()})

        res = ydl.extract_info(data['url'])
        if(res['_type']=='url'):
            res = ydl.extract_info(res['url'])

        pinyin=Pinyin()
        if res['entries'][0]['ie_key']=='YoutubePlaylist':
            tracks=res['entries']
            for t in tracks:
                t['display'] = t['title']+" (Playlist)"
                t['search'] = pinyin.get_initials(t['title'],'').upper()
            pager = pagerContent(tracks, 1, getCommon2_h_options(), youtubeScreen2)

        else:
            #remove "[Deleted video]" and "[Private video]"
            tracks=list(filter(lambda t:not re.match('\[.* video\]',t['title']),res['entries']))
            for t in tracks:
                t['display'] = t['title']
                t['search'] = pinyin.get_initials(t['title'],'').upper()
                t['youtube'] = True
            pager = pagerContent(tracks, 1, getCommon2_h_options(), playlist.addVideo)

        pager.startDisplay(page)
    except:
        print("error", sys.exc_info())




"""
Classes below
"""

class pagerContent:
    """shows the list on the selector window, with options for multi-page
    """
    displaylist = []
    filterlist = []
    page = 0
    maxpage = 0
    screenNum = 1
    h_options = None
    contentcallback = None
    searchtype = 0


    def __init__(self, displaylist, screenNum=1, h_options=None, callback=None):
        if h_options is None:
            h_options = {}
        self.displaylist = displaylist
        self.filterlist = displaylist
        self.maxpage = math.ceil(len(self.filterlist) / 10)
        assert screenNum==1 or screenNum==2, "Invalid screenNum"
        self.screenNum = screenNum
        self.h_options = h_options
        self.contentcallback = callback

    def startDisplay(self, page=0, searchtype=0):
        for option in self.h_options.values():
            if 'search' in option.keys() and option['search']:
                option['func']=self.showSearch
        self.searchtype=searchtype
        settings.selectorWindow.setHeaders(self.h_options)
        self.contentDisplay(page)

    def startSearch(self, page=0, searchtype=0):
        self.startDisplay(page, searchtype)
        self.showSearch()

    def showSearch(self, data=None):
        settings.selectorWindow.setSearchCallback(self.filterList)
        settings.selectorWindow.startSearch(self.searchtype)

    def contentDisplay(self, page=0):
        if page>=self.maxpage: page = self.maxpage-1
        if page<0: page=0

        c_options = {}
        for i in range(10):
            j=page*10+i
            if j<len(self.filterlist):
                c_options[i]={}
                c_options[i]['text'] = self.filterlist[j]['display']
                c_options[i]['func'] = self.__callback__
                if 'image' in self.filterlist[j].keys():
                    c_options[i]['image'] = self.filterlist[j]['image']

        f_options = {}
        if self.maxpage>1:
            f_options['pagertext'] = "%d / %d" % (page+1, self.maxpage)
            f_options[0] = {'text': _('F5:Page up'), 'func': self.pageUp}
            f_options[1] ={'text': _('F6:Page down'), 'func': self.pageDown}
        self.page=page
        setHistoryPage(page)

        settings.selectorWindow.setContents(self.screenNum, c_options)
        settings.selectorWindow.setFooters(f_options)

    def pageUp(self):
        if self.page>0:
            self.page -= 1
            self.contentDisplay(self.page)

    def pageDown(self):
        if self.page<self.maxpage-1:
            self.page += 1
            self.contentDisplay(self.page)

    def __callback__(self, index):
        if callable(self.contentcallback):
            if type(index)==int:
                data = self.filterlist[self.page*10+index]
            else:
                data = None
            self.contentcallback(data)

    def filterList(self, searchstring):
        if searchstring=='':
            self.filterlist = self.displaylist
        elif self.searchtype==2:
            self.filterlist = list(
                filter(lambda i: 'search' in i.keys() and i['search'].find(searchstring)>=0, self.displaylist))
        else:
            self.filterlist = list(filter(lambda i: 'search' in i.keys() and i['search'].startswith(searchstring), self.displaylist))
        self.maxpage = math.ceil(len(self.filterlist) / 10)
        self.contentDisplay(self.page)

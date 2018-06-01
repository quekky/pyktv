import os
import math
import re
from PyQt5.QtCore import pyqtSlot, QTimer, QThread, QEventLoop
from PyQt5.QtWidgets import QApplication
from youtube_dl import YoutubeDL
import time
from pprint import pprint

import settings
import playlist
import upnp_dlna
import functions




"""implemnet history, for the back button"""
browserhistory = []

def addHistory(func, data, allowduplicate=False):
    global browserhistory
    if allowduplicate or len(browserhistory)==0 or browserhistory[len(browserhistory)-1][0]!=func:
        browserhistory.append([func, data, -1])

def setHistoryPage(page):
    global browserhistory
    if len(browserhistory)>0:
        browserhistory[len(browserhistory)-1][2]=page

def getHistoryPage():
    global browserhistory
    if len(browserhistory)>0:
        return browserhistory[len(browserhistory)-1][2]

def getHistoryLastObject():
    global browserhistory
    if len(browserhistory)>0:
        return browserhistory[len(browserhistory)-1]
    else:
        return

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
                 2: {'text': _('F3:Playlist'), 'func': playlistSearch},
                 3: {'text': _('Artist'), 'func':artistSearch1}
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
                 6: {'text': _('Popular'), 'func': popularSearch},
                 8: {'text': _('Local Network'), 'func': networkSearch1},
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
    return song

def setDisplaySongText(song, prefix=''):
    song['display'] = prefix + song['title'] + "<span style='color:"+settings.config['font.secondarycolor']+"'> 《" + ",".join(song['singers']) + '》  （' + song['language'] + '）</span>'


"""
Functions related to searching songs
"""

def getCommon1_h_options():
    return {0: {'text': _('F1:Search Songs'), 'func': titleSearch},
            1: {'text': _('F2:Index Search'), 'func': indexSearch},
            2: {'text': _('F3:Playlist'), 'func': playlistSearch},
            3: {'text': _('Artist'), 'func': artistSearch1}
            }

def getCommon2_h_options():
    return {0: {'text': _('F1:Search'), 'search': 1}, #if ['search']=1, then calls the builtin pagerContent.searcher
            1: {'text': _('F2:Index Search'), 'func': indexSearch},
            2: {'text': _('F3:Playlist'), 'func': playlistSearch},
            3: {'text': _('Artist'), 'func': artistSearch1}
            }

@pyqtSlot(object, int)
def titleSearch(data=None, page=0):
    addHistory(titleSearch, data)

    rows = settings.dbconn.execute("select * from song where [index]!=0 order by title COLLATE NOCASE")

    tracks = [extractSingersAndSetDisplay(dict(r)) for r in rows]

    try:
        pager = pagerContent(tracks, 0, getCommon1_h_options(), playlist.addVideo)
        pager.startSearch(page, 0, 1)
    except:
        settings.logger.printException()


@pyqtSlot(object, int)
def indexSearch(data=None, page=0):
    # print('find music by index')
    addHistory(indexSearch, data)

    rows = settings.dbconn.execute("select * from song where [index]!=0 order by [index]")

    tracks = [extractSingersAndSetDisplay(dict(r), str(r['index'])+' - ') for r in rows]
    for d in tracks:
        d['search'] = str(d['index'])

    try:
        pager = pagerContent(tracks, 0, getCommon1_h_options(), playlist.addVideo)
        pager.startSearch(page, 1, 0)
    except:
        settings.logger.printException()


@pyqtSlot(object, int)
def artistSearch1(data=None, page=0):
    # print('find music by artist 1')
    addHistory(artistSearch1, data)

    rows = settings.dbconn.execute("select distinct region from singer where region!='' order by region COLLATE NOCASE")

    artists = [{'display': _('All Artist'), 'region': ''}] + [{'display':r[0],'region':r[0]} for r in rows]

    try:
        pager = pagerContent(artists, 0, getCommon1_h_options(), artistSearch2)
        pager.startDisplay(page)
    except:
        settings.logger.printException()


@pyqtSlot(object, int)
def artistSearch2(data, page=0):
    # print('find music by artist 2', data)
    addHistory(artistSearch2, data)
    region=data['region']
    if region=='':
        rows = settings.dbconn.execute("select distinct type from singer where type!='' order by type COLLATE NOCASE")
    else:
        rows = settings.dbconn.execute("select distinct type from singer where type!='' and region=? order by type", (region,))

    artists = [{'display': _('All Category'), 'region': region, 'type': ''}] + \
              [{'display':r[0], 'region':region, 'type':r[0]} for r in rows]

    try:
        pager = pagerContent(artists, 0, getCommon1_h_options(), artistSearch3)
        pager.startDisplay(page)
    except:
        settings.logger.printException()


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

        artists = []
        for r in rows:
            d = dict(r)
            d['display'] = d['name']
            image = os.path.join(settings.singerdir, r['name']+'.jpg')
            d['image']=image
            artists.append(d)

        pager = pagerContent(artists, 1, getCommon2_h_options(), artistSearch4)
        pager.startDisplay(page)
    except:
        settings.logger.printException()


@pyqtSlot(object, int)
def artistSearch4(data, page=0):
    # print('find music by artist 4', data)
    addHistory(artistSearch4, data)
    rows = settings.dbconn.execute(
        "select * from song where [index]!=0 and (singer=? or singer2=? or singer3=? or singer4=? or singer5=? or singer6=? or singer7=? or singer8=? or singer9=? or singer10=? ) order by title COLLATE NOCASE",
        [data['name']] * 10)

    tracks = [extractSingersAndSetDisplay(dict(r)) for r in rows]

    try:
        h_options=getCommon2_h_options()
        h_options[0]['search']=2
        pager = pagerContent(tracks, 0, h_options, playlist.addVideo)
        pager.startDisplay(page, 0, 1)
    except:
        settings.logger.printException()


@pyqtSlot(object, int)
def langSearch1(data=None, page=0):
    # print('find music by lang 1')
    addHistory(langSearch1, data)

    rows = settings.dbconn.execute("select distinct language from song where language!='' order by language COLLATE NOCASE")

    langs = [{'display':r[0],'language':r[0]} for r in rows]

    try:
        pager = pagerContent(langs, 0, getCommon1_h_options(), langSearch2)
        pager.startDisplay(page)
    except:
        settings.logger.printException()


@pyqtSlot(object, int)
def langSearch2(data, page=0):
    # print('find music by lang 2', data)
    addHistory(langSearch2, data)
    language = data['language']
    rows = settings.dbconn.execute("select * from song where [index]!=0 and language=? order by title COLLATE NOCASE", (language,))

    tracks = [extractSingersAndSetDisplay(dict(r)) for r in rows]

    try:
        pager = pagerContent(tracks, 0, getCommon2_h_options(), playlist.addVideo)
        pager.startDisplay(page, 0, 1)
    except:
        settings.logger.printException()


@pyqtSlot(object, int)
def categorySearch1(data=None, page=0):
    # print('find music by category 1')
    addHistory(categorySearch1, data)

    rows = settings.dbconn.execute("select distinct style from song where style!='' order by style COLLATE NOCASE")

    cats = [{'display':r[0],'style':r[0]} for r in rows]

    try:
        pager = pagerContent(cats, 0, getCommon1_h_options(), categorySearch2)
        pager.startDisplay(page)
    except:
        settings.logger.printException()


@pyqtSlot(object, int)
def categorySearch2(data, page=0):
    # print('find music by category 2', data)
    addHistory(categorySearch2, data)
    style = data['style']
    rows = settings.dbconn.execute("select * from song where [index]!=0 and style=? order by title COLLATE NOCASE", (style,))

    tracks = [extractSingersAndSetDisplay(dict(r)) for r in rows]

    try:
        pager = pagerContent(tracks, 0, getCommon2_h_options(), playlist.addVideo)
        pager.startDisplay(page, 0, 1)
    except:
        settings.logger.printException()


@pyqtSlot(object, int)
def charSearch1(data=None, page=0):
    # print('find music by char 1')
    addHistory(charSearch1, data)

    chars = [{'display':_('{} character').format(r),'index':r} for r in range(1,10)] + \
            [{'display':_('{} character').format(10)+_('s and above'),'index':10}]

    try:
        pager = pagerContent(chars, 0, getCommon1_h_options(), charSearch2)
        pager.startDisplay(page)
    except:
        settings.logger.printException()


@pyqtSlot(object, int)
def charSearch2(data, page=0):
    # print('find music by char 2', data)
    addHistory(charSearch2, data)
    index = data['index']
    if index==10:
        rows = settings.dbconn.execute("select * from song where [index]!=0 and chars>=10 order by title COLLATE NOCASE")
    else:
        rows = settings.dbconn.execute("select * from song where [index]!=0 and chars=? order by title COLLATE NOCASE", (index,))

    tracks = [extractSingersAndSetDisplay(dict(r)) for r in rows]

    try:
        pager = pagerContent(tracks, 0, getCommon2_h_options(), playlist.addVideo)
        pager.startDisplay(page, 0, 1)
    except:
        settings.logger.printException()


@pyqtSlot(object, int)
def popularSearch(data=None, page=0):
    # print('find music by popular')
    addHistory(popularSearch, data)

    rows = settings.dbconn.execute("select * from song where [index]!=0 order by order_time desc, title limit 100")

    tracks = [extractSingersAndSetDisplay(dict(r)) for r in rows]

    try:
        pager = pagerContent(tracks, 0, getCommon2_h_options(), playlist.addVideo)
        pager.startDisplay(page, 0, 1)
    except:
        settings.logger.printException()

"""
Functions related to playlist
"""

playlistTimer = QTimer()
playlist_h_options = {}


@pyqtSlot(object, int)
def playlistSearch(data=None, page=0):
    # print('show playlist')
    global playlistSelection, playlistTimer, playlist_h_options
    addHistory(playlistSearch, None)

    playlistSelection=''
    playlist_h_options = {0: {'text': _('F1:Priority'), 'func': prioritySongPlaylist},
                          1: {'text': _('F3:Delete'), 'func': deleteSongPlaylist}}

    playlistTimer.start(200)


def playlistDisplay(data=None, page=0):
    try:
        pager = pagerContent(list(playlist.video_playlist), 0, playlist_h_options, songPlaylistSelected)
        pager.startDisplay(page)
    except:
        settings.logger.printException()

@pyqtSlot()
def playlistRefresh():
    # if the screen on playlist, refresh it
    browserhistory=getHistoryLastObject()
    if browserhistory and browserhistory[0]==playlistSearch:
        playlistDisplay(browserhistory[1], browserhistory[2])
    else:
        global playlistTimer
        playlistTimer.stop()

playlistTimer.timeout.connect(playlistRefresh)


@pyqtSlot(object, int)
def prioritySongPlaylist(data=None, page=0):
    global playlistSelection, playlist_h_options
    playlistSelection='priority'
    playlist_h_options = {0: {'text': _('[Priority]'), 'func': None},
                          1: {'text': _('Choose song'), 'func': None},
                          3: {'text': _('F4:Cancel'), 'func': cancelSongPlaylist}}


@pyqtSlot(object, int)
def deleteSongPlaylist(data=None, page=0):
    global playlistSelection, playlist_h_options
    playlistSelection='delete'
    playlist_h_options = {0: {'text': _('[Delete]'), 'func': None},
                          1: {'text': _('Choose song'), 'func': None},
                          3: {'text': _('F4:Cancel'), 'func': cancelSongPlaylist}}


@pyqtSlot(object, int)
def cancelSongPlaylist(data=None, page=0):
    global playlistSelection, playlist_h_options
    playlistSelection=''
    playlist_h_options = {0: {'text': _('F1:Priority'), 'func': prioritySongPlaylist},
                          1: {'text': _('F3:Delete'), 'func': deleteSongPlaylist}}



@pyqtSlot(object, int)
def songPlaylistSelected(data, page=0):
    global playlistSelection
    if playlistSelection=='priority':
        playlist.piroritySong(data)
    elif playlistSelection=='delete':
        playlist.deleteSong(data)


"""
Functions related to youtube below
"""

class youtubeLogger(object):
    @staticmethod
    def debug(msg):
        settings.selectorWindow.setStatusTempText(msg, 500)
        #refresh the app, if not the video will appear hang while processing
        QApplication.processEvents(QEventLoop.AllEvents)

    @staticmethod
    def warning(msg):
        pass

    @staticmethod
    def error(msg):
        settings.logger.error("Youtube error:",msg)

@pyqtSlot(object, int)
def youtubeScreen1(data=None, page=0):
    addHistory(youtubeScreen1, data)
    rows = settings.dbconn.execute("select * from youtube where enable!=0 order by name COLLATE NOCASE, user COLLATE NOCASE")

    try:
        youtubelists = []
        for r in rows:
            d = dict(r)
            d['display'] = d['name']+" 《"+d['user']+'》'
            d['search'] = functions.get_initials(d['name'])
            youtubelists.append(d)

        pager = pagerContent(youtubelists, 0, getCommon2_h_options(), youtubeScreen2)
        pager.startDisplay(page)
    except:
        settings.logger.printException()

@pyqtSlot(object, int)
def youtubeScreen2(data=None, page=0):
    addHistory(youtubeScreen2, data, True)

    try:
        settings.ignoreInputKey=True
        settings.selectorWindow.setStatusTempText("Youtube: downloading list...", 1000)
        ydl = YoutubeDL({'quiet':False,'extract_flat':True,'dump_single_json':True,'logger':youtubeLogger()})

        res = ydl.extract_info(data['url'])
        if res['_type']== 'url':
            res = ydl.extract_info(res['url'])

        if res['entries'][0]['ie_key']=='YoutubePlaylist':
            tracks=res['entries']
            for t in tracks:
                t['display'] = t['title']+" (Playlist)"
                t['search'] = functions.get_initials(t['title'])
            pager = pagerContent(tracks, 0, getCommon2_h_options(), youtubeScreen2)

        else:
            #remove "[Deleted video]" and "[Private video]"
            tracks=list(filter(lambda t:not re.match('\[.* video\]',t['title']),res['entries']))
            for t in tracks:
                t['display'] = t['title']
                t['search'] = functions.get_initials(t['title'])
                t['network'] = 'youtube'
            pager = pagerContent(tracks, 0, getCommon2_h_options(), playlist.addVideo)

        pager.startDisplay(page, 0, 1)
    except:
        settings.logger.printException()
    else:
        settings.ignoreInputKey=False


"""
Functions related to local network (DLNA) below
"""

networktimer = QTimer()
networkservers = []
networkpreviousshown = 0


class networkRefresh(QThread):
    """Keep looking for DLNA servers"""
    waittime = 5000
    def run(self):
        global networkservers, networktimer
        while True:
            servers = upnp_dlna.discoverDLNA()
            if len(servers) != len(networkservers):
                for s in servers:
                    s['display'] = s['name']
                networkservers = servers
            time.sleep(self.waittime)
# start the thread immediately
networktimerrefresh = networkRefresh()
networktimerrefresh.start()


@pyqtSlot(object, int)
def networkSearch1(data=None, page=0):
    global networktimer, networkservers
    addHistory(networkSearch1, data)
    pager = pagerContent(networkservers, 0, getCommon1_h_options(), networkSearch2)
    pager.startDisplay(0)
    networktimer.start(100)


@pyqtSlot()
def networkSearch1timer():
    """Keep refresing the page9"""
    global networktimer, networkservers, networkpreviousshown
    try:
        if getHistoryLastObject()[0] == networkSearch1:
            # if by now it is still at this page, then display the contents
            if networkpreviousshown != len(networkservers):
                # refresh only if there's any change
                pager = pagerContent(networkservers, 0, getCommon1_h_options(), networkSearch2)
                pager.startDisplay(getHistoryPage())
                networkpreviousshown = len(networkservers)
        else:
            networktimer.stop()
    except:
        networktimer.stop()
networktimer.timeout.connect(networkSearch1timer)


@pyqtSlot(object, int)
def networkSearch2(data=None, page=0):
    #find root of the server
    addHistory(networkSearch2, data)

    try:
        children = upnp_dlna.find_directories(data)
        for child in children:
            child['display'] = child['title']
            child['search'] = functions.get_initials(child['title'])
            child['server'] = data
            child['location'] = '//' + data['name'] + '/' + child['title'] + '/'
        pager = pagerContent(children, 0, getCommon2_h_options(), networkSearch3)
        pager.startDisplay(page, 0, 1)
    except:
        settings.logger.printException()


@pyqtSlot(object, int)
def networkSearch3(data=None, page=0):
    # print(data)
    try:
        if data['class'].startswith('object.container'):
            # folder
            addHistory(networkSearch3, data, True)
            children = upnp_dlna.find_directories(data['server'], data['id'])
            for child in children:
                child['display'] = child['title']
                child['search'] = functions.get_initials(child['title'])
                child['server'] = data['server']
                child['location'] = data['location'] + child['title'] + '/'
                if 'artist' in child.keys():
                    child['display'] += "<span style='color:"+settings.config['font.secondarycolor']+"'> 《" + child['artist'] + '》</span>'
            pager = pagerContent(children, 0, getCommon2_h_options(), networkSearch3)
            pager.startDisplay(page, 0, 1)
        elif data['class'].startswith('object.item'):
            #something playable
            data['network'] = 'dlna'
            playlist.addVideo(data)
    except:
        settings.logger.printException()


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
        assert 0<=screenNum<=1, "Invalid screenNum"
        self.screenNum = screenNum
        self.h_options = h_options
        self.contentcallback = callback

    def startDisplay(self, page=0, searchtype=0, searchfilter=0):
        """

        :param page:
        :param searchtype:
            0=alphanumeric
            1=numbers only
        :param searchfilter:
            0=startswith
            1=find anywhere
        :return:
        """
        for option in self.h_options.values():
            if 'search' in option.keys() and option['search']:
                option['func']=self.showSearch
        self.searchtype=searchtype
        self.searchfilter=searchfilter
        settings.selectorWindow.setHeaders(self.h_options)
        self.contentDisplay(page)

    def startSearch(self, page=0, searchtype=0, searchfilter=0):
        self.startDisplay(page, searchtype, searchfilter)
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
            f_options[0] = {'text': _('F5:Page up') if page>0 else '', 'func': self.pageUp}
            f_options[1] = {'text': _('F6:Page down') if page<self.maxpage else '', 'func': self.pageDown}
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
        elif self.searchfilter==1:
            self.filterlist = list(
                filter(lambda i: 'search' in i.keys() and i['search'].find(searchstring)>=0, self.displaylist))
        else:
            self.filterlist = list(filter(lambda i: 'search' in i.keys() and i['search'].startswith(searchstring), self.displaylist))
        self.maxpage = math.ceil(len(self.filterlist) / 10)
        self.contentDisplay(self.page)

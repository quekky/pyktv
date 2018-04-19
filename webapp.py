import flask
import flask_compress
from gevent.pywsgi import WSGIServer
import threading
import sqlite3
import os
import sys
import json
from queue import deque
import gettext
from pprint import pprint

import settings
import screen
import playlist


dbconn = None


def extractSingers(song):
    song2={'id':song['id'], 'index':song['index'], 'title':song['title'], 'search':song['search'], 'language':song['language']}
    singers=[song['singer']]
    for i in range(2,11):
        if song['singer'+str(i)]!='':
            singers.append(song['singer'+str(i)])
    song2['singers_str']=",".join(singers)
    return song2


def extractSingersFromPlaylist(song):
    if('media_file' in song.keys()):
        # normal files
        song2=extractSingers(song)
    else:
        song2={'title':song['title'], 'network':song['network']}
        if song['network']=='youtube':
            subtitle = song['url']
            if not (subtitle.startswith('http://') or subtitle.startswith('https://')):
                subtitle = 'http://youtu.be/' + subtitle
            song2['subtitle'] = subtitle
        elif song['network']=='dlna':
            song2['subtitle'] = song['location']
            # try:
            #     song2['subtitle'] = "DLNA://"+song['server']['name']
            # except:
            #     song2['subtitle'] = ''
    song2['playlist_uuid']=song['playlist_uuid']
    return song2


"""flask start"""

fapp = flask.Flask(__name__, static_folder=os.path.join(settings.programDir, 'html/static'), template_folder=os.path.join(settings.programDir, 'html/template'))
flask_compress.Compress(fapp)


@fapp.route("/")
def homePage():
    return flask.render_template('index.html')


@fapp.route("/title")
def titleSearch1():
    return flask.render_template('titleSearch.html', json_tracks=titleSearchApi())

@fapp.route("/api/title")
def titleSearchApi():
    rows = dbconn.execute("select * from song where [index]!=0 order by title COLLATE NOCASE")
    tracks = [extractSingers(dict(r)) for r in rows]
    return json.dumps(tracks)


@fapp.route("/artist")
def artistSearch1():
    return flask.render_template('artistSearch1.html', json_artists=artistSearchApi())

@fapp.route("/api/artist")
def artistSearchApi():
    rows = dbconn.execute("select * from singer where name!='' order by name COLLATE NOCASE")
    singerdir = settings.config['singer.picture']
    artists = []
    for r in rows:
        d = {'id':r['id'], 'name':r['name'], 'search':r['search'], 'region':r['region'], 'type':r['type']}
        d['display'] = d['name']
        image = os.path.join(singerdir, r['name'] + '.jpg')
        if os.path.isfile(image):
            d['image'] = r['name'] + '.jpg'
        artists.append(d)
    return json.dumps(artists)


@fapp.route("/artist/<artist>")
def artistSearch2(artist):
    rows = dbconn.execute(
        "select * from song where [index]!=0 and (singer=? or singer2=? or singer3=? or singer4=? or singer5=? or singer6=? or singer7=? or singer8=? or singer9=? or singer10=? ) order by title COLLATE NOCASE",
        [artist] * 10)
    tracks = [extractSingers(dict(r)) for r in rows]
    return flask.render_template('artistSearch2.html', tracks=tracks, artist=artist)


@fapp.route("/index")
def indexSearch1():
    return flask.render_template('indexSearch.html', json_tracks=indexSearchApi())

@fapp.route("/api/index")
def indexSearchApi():
    rows = dbconn.execute("select * from song where [index]!=0 order by [index] COLLATE NOCASE")
    tracks = [extractSingers(dict(r)) for r in rows]
    for d in tracks:
        d['search'] = str(d['index'])
    return json.dumps(tracks)


@fapp.route("/network")
def networkSearch1():
    return flask.render_template('page4.html')


@fapp.route("/playlist")
def playlistSearch():
    return flask.render_template('playlist.html')


@fapp.route("/api/playlist")
def playlistSearch2():
    return json.dumps([extractSingersFromPlaylist(r) for r in playlist.video_playlist])

@fapp.route("/api/playlistsort")
def playlistSort():
    try:
        uuids=list(map(int, flask.request.args.getlist('uuid[]')))

        # 1st line: get the list of items that match the request
        # 2nd line: find items in playlist that's not in the request, put them in the back of the queue
        newplaylist = [v for uuid in uuids for v in playlist.video_playlist if v['playlist_uuid'] == uuid] + \
                      [v for v in playlist.video_playlist if v['playlist_uuid'] not in uuids]
        playlist.video_playlist = deque(newplaylist)
    except:
        pass
    else:
        return ''

@fapp.route("/api/playlistmovetotop")
def playlistMoveToTop():
    try:
        uuid=int(flask.request.args.get('uuid'))
        item = [v for v in playlist.video_playlist if v['playlist_uuid'] == uuid][0]
        playlist.video_playlist.remove(item)
        playlist.video_playlist.appendleft(item)
    except:
        pass
    else:
        return ''

@fapp.route("/api/playlistdelete")
def playlistDelete():
    try:
        uuid=int(flask.request.args.get('uuid'))
        item = [v for v in playlist.video_playlist if v['playlist_uuid'] == uuid][0]
        playlist.video_playlist.remove(item)
    except:
        pass
    else:
        return ''


@fapp.route("/api/addvideo")
def addVideo():
    songindex = flask.request.args.get('index')
    if songindex and songindex.isdigit():
        row = dbconn.execute("select * from song where [index]!=0 and [index]=? order by title COLLATE NOCASE", [songindex]).fetchone()
        if row:
            playlist.addVideo(screen.extractSingersAndSetDisplay(dict(row)), False)
    return ""


@fapp.route("/api/switchchannel")
def switchchannel():
    playlist.switchChannel()
    return ""

@fapp.route("/api/playnextsong")
def playnextsong():
    playlist.playNextSong()
    return ""

@fapp.route("/api/pitchdown")
def pitchdown():
    playlist.setPitchDown()
    return ""

@fapp.route("/api/pitchflat")
def pitchflat():
    try:
        playlist.setPitchFlat()
    except:
        settings.logger.printException()
    return ""

@fapp.route("/api/pitchup")
def pitchup():
    playlist.setPitchUp()
    return ""




# singer image

@fapp.route("/image/singer/")
def image_nosinger():
    return flask.send_file(os.path.join(settings.programDir, settings.themeDir+'default_singer.jpg'))

@fapp.route("/image/singer/<artist>")
def image_singer(artist):
    try:
        return flask.send_from_directory(settings.config['singer.picture'], artist)
    except:
        return flask.send_file(os.path.join(settings.programDir, settings.themeDir+'default_singer.jpg'))



# start/stop server
http_server = None

def startServer():
    global dbconn, http_server
    dbconn = sqlite3.connect(settings.config['sqlitefile'])
    dbconn.row_factory = sqlite3.Row
    if getattr(sys, "frozen", False): #if debug, allow refresh page
        http_server = WSGIServer(('0.0.0.0', 5000), fapp)
        http_server.serve_forever()
    else:
        fapp.run(host='0.0.0.0', debug=True, use_reloader=False)

def __init__():
    # translate based on program language (not browser language)
    translate = gettext.translation('messages', os.path.join(settings.programDir, 'locale'), languages=[settings.config['language']])
    @fapp.context_processor
    def inject_gettext():
        return dict(_=translate.gettext, gettext=translate.gettext)

    thread=threading.Thread(target=startServer)
    thread.daemon=True
    thread.start()


def __shutdown__():
    global http_server
    if http_server: http_server.stop()
    pass



if __name__ == "__main__":
    playlistSort()
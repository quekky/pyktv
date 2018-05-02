"""Playlist functions

"""

from collections import deque
import os
import time
from PyQt5.QtCore import QTimer, pyqtSlot

import settings
import screen
import functions

#Song structure is a dict:
songstructure_enum={
    'index': 0,
    'display': '',
    'title': '',
    'search': '', #search letter
    'chars': '', #how many char number in the title
    'singers': '', #tuple of strings
    'language': '',
    'style': '', #category
    'grade': 0, #Rating
    'channel': '', #which channel is the music-only track (L, R, 0, 1, 2)
    'region': '',
    'library': '',
    'media_file': '',
    'remark': '',
}

#Singer structure is a dict:
singerstructure_emum={
    'name': '',
    'search': '',
    'region': '',
    'type': '', #category
    'description': '',
    'remark': '',
    'imagefile': None
}



video_playlist = deque()
current_playing = None
#False=voice, True=music
current_channel = False
network_channel = 0
playlist_uuid = 0
videostatushasbeenset = False
channelhasbeenset = False
videostarttime = 0
videoendtime = 0
#wait for x seconds for video to start (sometime youtube is slower to start)
videowaittimeout = 10
videopopularupdated=False
videopopulartimeout = 60
randomplaytimeout = 0
statusTempText = None

maxpitchvariance = 5
audiopanstr= ''
audiopitch=0
audiovolume=0



def __post_init__():
    global videoendtime, randomplaytimeout, checkMediaTimer, statusTextTimer, statusTempTextTimer, current_channel
    videoendtime=time.time()
    randomplaytimeout=settings.config.getint('randomplay', 999999999)
    checkMediaTimer = QTimer()
    checkMediaTimer.timeout.connect(checkMediaPlayback)
    checkMediaTimer.start(100)
    statusTextTimer = QTimer()
    statusTextTimer.timeout.connect(setStatusText)
    statusTextTimer.start(200)
    statusTempTextTimer = QTimer()
    statusTempTextTimer.timeout.connect(setStatusTempText)
    statusTempTextTimer.start(100)
    current_channel=settings.config.getboolean('video.startup_channel',False)


def addVideo(video):
    global statusTempText, video_playlist, current_playing, playlist_uuid
    # print(video)
    song = video.copy()
    video_playlist.append(song)

    statusTempText = (_("Add song: ") + song['display'], 1000)

    try:
        screen.setDisplaySongText(song)
    except:
        pass
    song['playlist_uuid'] = playlist_uuid
    playlist_uuid += 1
    if len(video_playlist)>=1 and current_playing is None:
        playNextSong()


def piroritySong(video):
    global video_playlist
    try:
        video_playlist.remove(video)
        video_playlist.appendleft(video)
    except:
        pass

def deleteSong(video):
    global video_playlist
    try:
        video_playlist.remove(video)
    except:
        pass


def playNextSong():
    global video_playlist, current_playing, videostarttime, videostatushasbeenset, videopopularupdated, channelhasbeenset, network_channel, audiopitch, audiovolume
    # print(current_playing)
    # print(video_playlist)
    try:
        current_playing = video_playlist.popleft()

        if 'media_file' in current_playing.keys():
            # normal files
            library=current_playing['library']
            mediafile=str(current_playing['media_file'])
            videopath=functions.getVideoPath(library, mediafile)
        elif 'network' in current_playing :
            #network/youtube
            videopath=current_playing['url']
            if current_playing['network']=='youtube'and not functions.isValidUrl(videopath):
                videopath=r'ytdl://'+videopath
                print(videopath)

        try:
            player = settings.mpvMediaPlayer
            player.play(videopath)

            videostatushasbeenset=False
            videopopularupdated=False
            channelhasbeenset=False
            videostarttime=time.time()
            network_channel = 0
            audiopitch = 0
            audiovolume = current_playing['volume'] if 'volume' in current_playing.keys() else 0
            setChannel()

        except:
            settings.logger.printException()
            #if error, try next song
            playNextSong()


    except:
        settings.logger.printException()


def updateVideoPopular(song):
    if 'media_file' in song.keys():
        try:
            settings.dbconn.execute('update song set order_time=order_time+1 where id=?', (song['id'],))
            settings.dbconn.commit()
        except:
            pass


def checkMediaPlayback():
    global video_playlist, current_playing, videostarttime, videowaittimeout, videoendtime, videopopulartimeout, videopopularupdated
    global videostatushasbeenset, channelhasbeenset
    player = settings.mpvMediaPlayer
    timenow=time.time()
    player_time_pos=player.time_pos
    if player_time_pos is None: player_time_pos=0
    player_duration=player.duration
    if player_duration is None: player_duration=0xffffffff
    if not player.idle_active:
        if player_time_pos > 0 and not videostatushasbeenset:
            videostatushasbeenset = True
            settings.videoWindow.setStatusTempText(_("Now playing: ") + current_playing['display'], 3000)
        elif player_time_pos>videopopulartimeout and not videopopularupdated:
            videopopularupdated = True
            updateVideoPopular(current_playing)
        elif len(video_playlist)>0 and (player_time_pos > player_duration - 5):
            settings.videoWindow.setStatusTempText(_("Prepare for: ") + video_playlist[0]['display'], 3000)
    elif timenow-videostarttime > videowaittimeout:
        # have to wait for some time for the video to start, else it'll skip over
        # once finish playing, try next song
        current_playing = None
        if len(video_playlist) > 0:
            playNextSong()
        elif videostarttime>0:
            #for randomplay, this will not run
            # player.stop()
            videostarttime = 0
            videoendtime = timenow
            settings.selectorWindow.setStatusText('')
            settings.videoWindow.stopStatusTempText()
        elif timenow - videoendtime > randomplaytimeout:
            videostatushasbeenset = True
            channelhasbeenset = True
            randomPlay()

def setPlayerFilter():
    global audiopanstr, audiopitch, audiovolume
    try:
        #start with no rubberband (in MPV, for vorbis/opus, if there's rubberband the sound is not playing)
        audiopitchstr = None if audiopitch==0 else 'rubberband=pitch-scale=' + str(1 + audiopitch / 10)
        audiovolumestr = None if audiovolume==0 else 'lavfi="volume=volume=%sdB"' % audiovolume
        str1=','.join(filter(None, (audiovolumestr, audiopanstr, audiopitchstr)))
        settings.mpvMediaPlayer.command('af', 'clr', '')
        if str1: settings.mpvMediaPlayer.command('af', 'set', str1)
    except:
        settings.logger.printException()

def setPlayerChannel(channel):
    global audiopanstr
    player = settings.mpvMediaPlayer
    if channel == 'L':
        audiopanstr = 'pan="mono|c0=c0"'
    elif channel == 'R':
        audiopanstr = 'pan="mono|c0=c1"'
    elif channel == '':
        audiopanstr = ''
        player.aid = 1
    elif type(channel) == int:
        audiopanstr = ''
        try:
            tracks = player.track_list
            tracks = list(filter(lambda t: t['type']=='audio', tracks))
            if channel > len(tracks)-1: channel = 0
            player.aid = channel+1
        except:
            player.aid = 1
    setPlayerFilter()

def setChannel():
    global current_playing, current_channel, network_channel
    # print("setchannel", current_channel)

    if current_playing is None: return

    if 'network' in current_playing.keys():
        channel=['','L','R'][network_channel]
    else:
        channel = current_playing['channel']
        try:
            channel = int(channel)
        except:
            pass

        if not current_channel:
            if channel=='L':
                channel = 'R'
            elif channel=='R':
                channel = 'L'
            elif channel=='':
                pass
            elif channel==0:
                channel = 1
            elif channel>=1:
                channel = 0

    setPlayerChannel(channel)

def switchChannel():
    """Toggle voice/music"""
    global current_channel, network_channel, statusTempText
    if current_playing is not None:
        if 'network' in current_playing.keys():
            network_channel = (network_channel + 1) % 3
            if False: text='Network - '+[_('Stereo'),_('Left'),_('Right')][network_channel]
            text='Network - '+_(['Stereo','Left','Right'][network_channel])
            setChannel()
        elif 'channel' not in current_playing.keys() or current_playing['channel']=='':
            text=_("Video does not support vocal")
        else:
            current_channel = not current_channel
            text = _("Vocal off") if current_channel else _("Vocal on")
            setChannel()
        statusTempText = (text, 2000)

def setPitch():
    global audiopitch, statusTempText
    setPlayerFilter()
    text=_("Key {0:+d}").format(audiopitch) if audiopitch else _("Key reset")
    statusTempText=(text, 2000)

def setPitchUp():
    global current_playing, audiopitch
    if current_playing is not None:
        audiopitch+=1
        if audiopitch>maxpitchvariance: audiopitch=maxpitchvariance
        setPitch()

def setPitchDown():
    global current_playing, audiopitch
    if current_playing is not None:
        audiopitch-=1
        if audiopitch<-maxpitchvariance: audiopitch=-maxpitchvariance
        setPitch()

def setPitchFlat():
    global current_playing, audiopitch
    if current_playing is not None:
        audiopitch=0
        setPitch()


"""
Use different QTimer to set the status text

This fix the issue of having the another thread (eg web server) crashing the app when trying to set the text 
"""
@pyqtSlot()
def setStatusText():
    global video_playlist, current_playing

    if current_playing is None:
        text=""
    else:
        text = _("Now playing: ")+current_playing['display']
    if len(video_playlist):
        text +=" &nbsp;&nbsp;&nbsp;&nbsp; "+_("Coming up: ")+video_playlist[0]['display']
    settings.selectorWindow.setStatusText(text)

@pyqtSlot()
def setStatusTempText():
    global statusTempText
    if statusTempText is not None:
        settings.selectorWindow.setStatusTempText(*statusTempText)
        settings.videoWindow.setStatusTempText(*statusTempText)
        statusTempText=None


def randomPlay():
    global audiopitch, videopopularupdated
    try:
        rows = settings.dbconn.execute(r"select * from song where [index]!=0 order by random() limit 1")
        song=rows.fetchone()
        library=song['library']
        mediafile=str(song['media_file'])
        if library=='':
            path=mediafile
        else:
            mediafile=mediafile.lstrip(os.path.sep)
            path=os.path.join(library,mediafile)
        settings.logger.debug("Playing random file:",path)
        player = settings.mpvMediaPlayer
        player.play(path)

        # do not update popular song
        videopopularupdated=True
        audiopitch = 0
        #set voice track
        channel=song['channel']
        if channel=='L':
            setPlayerChannel('R')
        elif channel=='R':
            setPlayerChannel('L')
        elif channel is int:
            setPlayerChannel(not channel)
        else:
            setPlayerChannel('')
    except:
        settings.logger.printException()


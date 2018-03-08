"""Playlist functions

"""

from collections import deque
import os
import sys
import time
import vlc
from PyQt5.QtCore import QTimer
import settings
import screen
import youtube_dl
from pprint import pprint

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
playlist_uuid = 0
videostatushasbeenset = False
channelhasbeenset = False
videostarttime = 0
videoendtime = 0
#wait for x seconds for video to start (sometime youtube is slower to start)
videowaittimeout = 10
randomplaytimeout = 0


def __post_init__():
    global videoendtime, randomplaytimeout, timer
    videoendtime=time.time()
    randomplaytimeout=settings.config.getint('randomplay', 999999999)
    timer = QTimer()
    timer.timeout.connect(checkMediaPlayback)
    timer.start(100)


def addVideo(video):
    global video_playlist, current_playing, playlist_uuid
    # print(video)
    song = video.copy()
    video_playlist.append(song)

    settings.selectorWindow.setTempStatusText(_("Add song: ") + song['display'], 1000)
    try:
        screen.setDisplaySongText(song)
    except:
        pass
    song['playlist_uuid'] = playlist_uuid
    playlist_uuid += 1
    if len(video_playlist)>=1 and current_playing is None:
        playNextSong()

    setStatusText()

def piroritySong(video):
    global video_playlist
    try:
        video_playlist.remove(video)
        video_playlist.appendleft(video)
        setStatusText()
    except:
        pass

def deleteSong(video):
    global video_playlist
    try:
        video_playlist.remove(video)
        setStatusText()
    except:
        pass

def playNextSong():
    global video_playlist, current_playing, timer, videostarttime, videostatushasbeenset, channelhasbeenset, youtube_channel
    # print(current_playing)
    # print(video_playlist)
    try:
        current_playing = video_playlist.popleft()

        #normal files
        if 'media_file' in current_playing.keys():
            library=current_playing['library']
            mediafile=str(current_playing['media_file'])
            if library=='':
                path=mediafile
            else:
                mediafile=mediafile.lstrip(os.path.sep)
                path=os.path.join(library,mediafile)
            # print(path)
            media = settings.vlcInstance.media_new(path)
            media.parse()
        else:
            #youtube
            # print("try youtube")
            try:
                subs=settings.config.get('youtube.subtitleslangs','').split(',')
                option={'quiet': True, 'simulate': True, 'format': settings.config.get('youtube.format','best')}
                if len(subs) > 0: option.update({'writesubtitles':True, 'subtitleslangs': subs})
                ydl = youtube_dl.YoutubeDL(option)
                res = ydl.extract_info(current_playing['url'])

                # pprint(res)
                # #if the video and audio is spilt, 1st item is viideo, then look for audio
                # format_id = res['format_id'].split('+')
                # url=next(f['url'] for f in res['formats'] if f['format_id']==format_id[0])
                # media = settings.vlcInstance.media_new(url)
                # for f1 in format_id[1:]:
                #     url=next(f['url'] for f in res['formats'] if f['format_id']==f1)
                #     media.slaves_add(vlc.MediaSlaveType.audio.value, 2, url)
                # media.parse()

                media = settings.vlcInstance.media_new(res['requested_formats'][0]['url'])
                for i in range(1, len(res['requested_formats'])):
                    media.slaves_add(vlc.MediaSlaveType.audio.value, 4, res['requested_formats'][i]['url'])
                for v in res['requested_subtitles'].values():
                    media.slaves_add(vlc.MediaSlaveType.subtitle.value, 4, v['url'])
                media.parse()
            except youtube_dl.utils.DownloadError as err:
                print("Youtube error:",err)
                settings.selectorWindow.setTempStatusText(str(err), 2000)
                current_playing=None
            except:
                print("error", sys.exc_info())

        try:
            # timer.stop()
            player = settings.vlcMediaPlayer
            # player.stop()
            player.set_media(media)
            player.play()

            #have to wait a bit after it start to be able to set channel
            # time.sleep(0.1)
            # setChannel()
            videostatushasbeenset=False
            channelhasbeenset=False
            videostarttime=time.time()
            youtube_channel = 0

        except:
            print("error", sys.exc_info())
            #if error, try next song
            playNextSong()

        #if the screen on playlist, refresh it
        browserhistory=screen.browserhistory[len(screen.browserhistory) - 1]
        if browserhistory[0]==screen.playelistSearch:
            browserhistory[0](browserhistory[1],browserhistory[2])

    except:
        print("err",sys.exc_info())

    setStatusText()


def checkMediaPlayback():
    global video_playlist, current_playing, videostarttime, videowaittimeout, videoendtime
    global videostatushasbeenset, channelhasbeenset, randomtimer
    player = settings.vlcMediaPlayer
    timenow=time.time()
    if player.is_playing():
        # print(player.get_time(),player.get_length())
        if player.get_time() > 0 and not videostatushasbeenset:
            videostatushasbeenset = True
            settings.videoWindow.setStatusTempText(_("Now playing: ") + current_playing['display'], 3000)
        elif len(video_playlist)>0 and (player.get_time() > player.get_length() - 5000):
            settings.videoWindow.setStatusTempText(_("Prepare for: ") + video_playlist[0]['display'], 3000)
        # else:
        #     settings.videoWindow.setStatusTempText('')
        #wait till the video is actually played, then set the channel
        if player.get_time() > 0 and not channelhasbeenset:
            channelhasbeenset = True
            setChannel()
    elif timenow-videostarttime > videowaittimeout:
        # have to wait for some time for the video to start, else it'll skip over
        # once finish playing, try next song
        current_playing = None
        if len(video_playlist) > 0:
            playNextSong()
        elif videostarttime>0:
            #for randomplay, this will not run
            player.stop()
            videostarttime = 0
            videoendtime = timenow
            settings.selectorWindow.setStatusText('')
            settings.videoWindow.stopStatusTempText()
        elif timenow - videoendtime > randomplaytimeout:
            videostatushasbeenset = True
            channelhasbeenset = True
            randomPlay()

def setPlayerChannel(channel):
    player = settings.vlcMediaPlayer
    if channel == 'L':
        player.audio_set_channel(vlc.AudioOutputChannel.Left.value)
    elif channel == 'R':
        player.audio_set_channel(vlc.AudioOutputChannel.Right.value)
    elif channel == '':
        player.audio_set_channel(vlc.AudioOutputChannel.Stereo.value)
        player.audio_set_track(0)
    elif type(channel) == int:
        try:
            tracks = player.audio_get_track_description()
            tracks = list(filter(lambda x: x[0] >= 0, tracks))  # positive tracks only
            if channel > len(tracks): channel = 0

            player.audio_set_track(tracks[channel][0])
            player.audio_set_channel(vlc.AudioOutputChannel.Stereo.value)
        except:
            player.audio_set_track(0)
            player.audio_set_channel(vlc.AudioOutputChannel.Stereo.value)

def setChannel():
    global current_playing, current_channel, youtube_channel
    # print("setchannel", current_channel)

    if current_playing is None: return
    player = settings.vlcMediaPlayer

    if 'youtube' in current_playing.keys():
        channel=['','L','R'][youtube_channel]
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
            elif channel==0:
                channel = 1
            elif channel>=1:
                channel = 0

    setPlayerChannel(channel)

def switchChannel():
    """Toggle voice/music"""
    global current_channel, youtube_channel
    if current_playing is not None:
        if 'youtube' in current_playing.keys():
            youtube_channel = (youtube_channel+1)%3
            if False: text=[_('Stereo'),_('Left'),_('Right')][youtube_channel]
            text=_(['Stereo','Left','Right'][youtube_channel])
            setChannel()
        elif 'channel' not in current_playing.keys() or current_playing['channel']=='':
            text=_("Video does not support vocal")
        else:
            current_channel = not current_channel
            text = _("Vocal off") if current_channel else _("Vocal on")
            setChannel()
        settings.selectorWindow.setTempStatusText(text, 2000)
        settings.videoWindow.setStatusTempText(text, 2000)


def setStatusText():
    global video_playlist, current_playing

    if current_playing is None:
        text=""
    else:
        text = _("Now playing: ")+current_playing['display']
    if len(video_playlist):
        text +=" &nbsp;&nbsp;&nbsp;&nbsp; "+_("Coming up: ")+video_playlist[0]['display']
    settings.selectorWindow.setStatusText(text)

def randomPlay():
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
        print("Playing random file",path)
        media = settings.vlcInstance.media_new(path)
        media.parse()
        player = settings.vlcMediaPlayer
        player.set_media(media)
        player.play()

        #set voice track
        time.sleep(0.1)
        channel=song['channel']
        if channel=='L':
            setPlayerChannel('R')
        elif channel=='R':
            setPlayerChannel('L')
        elif channel is int:
            setPlayerChannel(not(channel))
        else:
            setPlayerChannel('')
    except:
        print("error",sys.exc_info())
        pass



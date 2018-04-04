"""All the global variables here


"""

import vlc
import configparser
import os
import sys
import traceback
import sqlite3
import gettext
import playlist


vlcInstance = None
vlcMediaPlayer = None
config = None
themeDir = None

videoWindow = None
selectorWindow = None

dbconn = None


def __init__():
    global vlcInstance, vlcMediaPlayer, config, themeDir, dbconn
    vlcInstance = vlc.Instance(["--sub-source=marq"])
    vlcMediaPlayer = vlcInstance.media_player_new()
    vlcMediaPlayer.video_set_mouse_input(False)
    vlcMediaPlayer.video_set_key_input(False)

    scriptpath=os.path.abspath(os.path.dirname(os.path.realpath(sys.argv[0])))

    config = configparser.ConfigParser()
    config.read(os.path.join(scriptpath,"config.ini"))
    config = config['DEFAULT']

    vlcMediaPlayer.video_set_aspect_ratio(config.get('video.aspect_ratio','None'))
    playlist.current_channel=config.getboolean('video.startup_channel',False)

    themeDir = os.path.join(config.get('theme.dir'), '')

    dbconn = sqlite3.connect(config['sqlitefile'])
    dbconn.row_factory = sqlite3.Row


    localedir = os.path.join(scriptpath, 'locale')
    translate = gettext.translation('messages', localedir, languages=[config['language']])
    translate.install()



class mainLogger(object):
    _out_file = sys.stdout
    _err_file = sys.stderr

    def debug(self, *args, **kwargs):
        if self._err_file is not None:
            print(*args, file=self._out_file, **kwargs)

    def warning(self, *args, **kwargs):
        if self._err_file is not None:
            print(*args, file=self._out_file, **kwargs)

    def error(self, *args, **kwargs):
        if self._err_file is not None:
            print(*args, file=self._out_file, **kwargs)

    def printException(self, *args, **kwargs):
        if self._err_file is not None:
            print(*args, file=self._out_file, **kwargs)
            traceback.print_exc()
            self._err_file.flush()

logger = mainLogger()

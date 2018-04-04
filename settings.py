"""All the global variables here


"""

import mpv
import configparser
import os
import sys
import traceback
import sqlite3
import gettext
import playlist


mpvMediaPlayer = None
config = None
themeDir = None

videoWindow = None
selectorWindow = None
ignoreInputKey=False

dbconn = None


def __init__():
    global mpvMediaPlayer, config, themeDir, dbconn

    mpvMediaPlayer = mpv.MPV(hwdec=True, log_handler=logger.warning, loglevel='warn')
    # vlcMediaPlayer = mpv.MPV(log_handler=print, loglevel='debug')

    scriptpath=os.path.abspath(os.path.dirname(os.path.realpath(sys.argv[0])))

    config = configparser.ConfigParser()
    config.read(os.path.join(scriptpath,"config.ini"))
    config = config['DEFAULT']

    mpvMediaPlayer.video_aspect = config.get('video.aspect_ratio', '-1')
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

"""All the global variables here


"""

import mpv
import configparser
import os
import sys
import traceback
import gettext

import functions

programDir = os.path.abspath(os.path.dirname(os.path.realpath(sys.argv[0])))
mpvMediaPlayer = None
config = None
keyboardshortcut = None
themeDir = ''
singerdir = ''

videoWindow = None
selectorWindow = None
ignoreInputKey=False

dbconn = None


def __init__():
    global mpvMediaPlayer, config, keyboardshortcut, themeDir, singerdir, dbconn

    mpvMediaPlayer = mpv.MPV(hwdec=True, log_handler=logger.warning, loglevel='warn', ytdl=True)

    configfile = configparser.ConfigParser()
    configfile.read(os.path.join(programDir,"config.ini"))
    config = configfile['program']
    keyboardshortcut = configfile['keyboard']

    mpvMediaPlayer.video_aspect = config.get('video.aspect_ratio', '-1')
    mpvMediaPlayer.ytdl_format=config.get('youtube.format','best')
    mpvMediaPlayer.slang = config.get('youtube.subtitleslangs', '')

    themeDir = os.path.join(config.get('theme.dir'), '')
    singerdir = os.path.join(programDir, config.get('singer.picture', ''))

    dbconn = functions.createDatabase()


    localedir = os.path.join(programDir, 'locale')
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

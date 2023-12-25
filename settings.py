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
libraries={}

videoWindow = None
selectorWindow = None
ignoreInputKey=False

dbconn = None


def __init__():
    global mpvMediaPlayer, config, keyboardshortcut, themeDir, singerdir, dbconn

    mpvMediaPlayer = mpv.MPV(hwdec=True, log_handler=logger.warning, loglevel='warn', ytdl=True, audio_file_auto='exact')

    configfile = configparser.ConfigParser()
    configfile.read(os.path.join(programDir,"config.ini"))
    config = configfile['program']
    keyboardshortcut = configfile['keyboard']

    #mpvMediaPlayer.video_aspect = config.get('video.aspect_ratio', '-1')
    mpvMediaPlayer.ytdl_format=config.get('youtube.format','')
    mpvMediaPlayer.slang = config.get('youtube.subtitleslangs', '')

    themeDir = os.path.normcase(os.path.join(programDir, config.get('theme.dir'), ''))
    singerdir = os.path.normcase(os.path.join(programDir, config.get('singer.picture', '')))

    dbconn = functions.createDatabase()
    upgradedatabase()
    loadLibraries()

    localedir = os.path.join(programDir, 'locale')
    translate = gettext.translation('messages', localedir, languages=[config['language']])
    translate.install()


def loadLibraries():
    global dbconn, libraries
    rows = dbconn.execute('select * from library')
    for r in rows:
        libraries[r['root_path']] = list(filter(None, [r['mirror1'],r['mirror2'],r['mirror3'],r['mirror4'],r['mirror5'],r['mirror6'],r['mirror7'],r['mirror8'],r['mirror9'],r['mirror10']]))


upgradedbsql = [
    # version 2021.12.25-beta
    [20211225, "ALTER TABLE song ADD COLUMN library2 TEXT NOT NULL DEFAULT ''"],
    [20211225, "ALTER TABLE song ADD COLUMN media_file2 TEXT NOT NULL DEFAULT ''"],
    [20211225, "CREATE UNIQUE INDEX idx_song_index ON song (`index`)"],
    # version 2025.12.25-beta
    # remove unique as 0 is used for new songs
    [20231225, "DROP INDEX idx_song_index"],
    [20231225, "CREATE INDEX idx_song_index ON song (`index`)"],
]

def upgradedatabase():
    global dbconn
    rows = dbconn.execute('PRAGMA user_version')
    user_version = next(rows)[0]

    for sql in upgradedbsql:
        if user_version < sql[0]:
            try:
                # print(sql[1])
                dbconn.execute(sql[1])
            except:
                next
    if user_version != sql[0]:
        dbconn.execute('PRAGMA user_version=%d'%(sql[0]))
    dbconn.commit()


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

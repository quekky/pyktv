import re
import pypinyin
import subprocess
import sqlite3
from urllib.parse import urlparse
import os
import settings


CREATE_NO_WINDOW=0x08000000


def createDatabase():
    dbconn = sqlite3.connect(os.path.join(settings.programDir, settings.config['sqlitefile']))
    dbconn.row_factory = sqlite3.Row
    return dbconn


def isValidUrl(url):
    #https://ffmpeg.org/ffmpeg-protocols.html
    return urlparse(url).scheme in ("http", "https", "ftp", "ftps", "sftp", "file",
                                    "rtmp", "rtmps", "rtmpe", "rtmpt", "rtmpts", "rtmpte",
                                    "rtp", "rtsp", "sctp", "srt", "tcp", "tls", "udp", "unix"
                                    "bluray", "dvd", "bd", "tv", "pvr", "cdda", "icecast", "mmsh",
                                    "data", "ytdl", "smb",)

def getVideoPath(library, mediafile):
    """joins library and mediafile
    If media is not found in the main library, try all the mirrors
    """
    if library == '' or isValidUrl(mediafile):
        videopath = mediafile
    else:
        mediafile = mediafile.lstrip('\\/')
        videopath = os.path.join(library, mediafile).replace('\\', os.path.sep).replace('/', os.path.sep)

    if not isValidUrl(videopath):
        if not os.path.isfile(videopath) and library in settings.libraries.keys():
            for path in settings.libraries[library]:
                tempfile=os.path.join(path, mediafile).replace('\\', os.path.sep).replace('/', os.path.sep)
                if os.path.isfile(tempfile):
                    videopath=tempfile
                    break

    return videopath


def get_initials(word):
    re_jap='[ぁ-んァ-ン]'
    re_hangul='[\u1100-\u11FF\u3130-\u318F\uA960-\uA97F\uAC00-\uD7AF\uD7B0-\uD7FF]'
    split=pypinyin.lazy_pinyin(word, errors=lambda w: [m.group() for m in re.finditer('[A-Za-z]+|[0-9]|'+re_jap+'|'+re_hangul, w)])
    return ''.join([x[0] for x in split]).upper()


def setZeroMargins(layout):
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    return layout


def to_sec(s):
    return (int(s[0:2]) * 60 * 60) + (int(s[3:5]) * 60) + float(s[6:11])


class CommandRunner():
    DUR_REGEX = re.compile(r'Duration: (\d\d:\d\d:\d\d.\d\d)')
    TIME_REGEX = re.compile(r'Parsed_ebur128_0.*\st:\s*(\d+\.\d+)')
    output=None

    def run_ffmpeg_command(self, cmd):
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=CREATE_NO_WINDOW)
        total_dur=None
        stderr=[]
        while True:
            line = p.stderr.readline().decode("utf8", errors='replace')
            if line == '' and p.poll() is not None:
                break
            stderr.append(line.strip())
            self.output = "\n".join(stderr)

            if not total_dur and CommandRunner.DUR_REGEX.search(line):
                total_dur = to_sec(self.DUR_REGEX.search(line).group(1))
                continue
            if total_dur:
                result = self.TIME_REGEX.search(line)
                if result:
                    elapsed_time = float(result.group(1))
                    yield int(elapsed_time / total_dur * 100) if elapsed_time<=total_dur else 100
        yield 100

    def run_command(self, cmd):
        p = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, creationflags=CREATE_NO_WINDOW)
        stdout, stderr = p.communicate()
        self.output=stderr.decode("utf8", errors='replace')

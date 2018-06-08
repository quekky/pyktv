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


""" Hangul functions """

LEADING_CONSONANTS = ['ㄱ', 'ㄲ', 'ㄴ', 'ㄷ', 'ㄸ', 'ㄹ', 'ㅁ', 'ㅂ', 'ㅃ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅉ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
INDEX_BY_LEADING_CONSONANT = { leading_consonant: index for index, leading_consonant in enumerate(LEADING_CONSONANTS) }

VOWELS = ['ㅏ', 'ㅐ', 'ㅑ', 'ㅒ', 'ㅓ', 'ㅔ', 'ㅕ', 'ㅖ', 'ㅗ', 'ㅘ', 'ㅙ', 'ㅚ', 'ㅛ', 'ㅜ', 'ㅝ', 'ㅞ', 'ㅟ', 'ㅠ', 'ㅡ', 'ㅢ', 'ㅣ']
INDEX_BY_VOWEL = { vowel: index for index, vowel in enumerate(VOWELS) }

TRAILING_CONSONANTS = [None, 'ㄱ', 'ㄲ', 'ㄳ', 'ㄴ', 'ㄵ', 'ㄶ', 'ㄷ', 'ㄹ', 'ㄺ', 'ㄻ', 'ㄼ', 'ㄽ', 'ㄾ', 'ㄿ', 'ㅀ', 'ㅁ', 'ㅂ', 'ㅄ', 'ㅅ', 'ㅆ', 'ㅇ', 'ㅈ', 'ㅊ', 'ㅋ', 'ㅌ', 'ㅍ', 'ㅎ']
INDEX_BY_TRAILING_CONSONANT = { trailing_consonant: index for index, trailing_consonant in enumerate(TRAILING_CONSONANTS) }

COMPLEXJOOGSUNG = {'ㄹㄱ': 'ㄺ', 'ㄹㄷ': 'ㄾ', 'ㄹㅂ': 'ㄼ', 'ㄹㅍ': 'ㄿ', 'ㄱㅅ': 'ㄳ', 'ㄴㅎ': 'ㄶ', 'ㄹㅅ': 'ㄽ', 'ㄹㅎ': 'ㅀ', 'ㅂㅅ': 'ㅄ', 'ㄴㅈ': 'ㄵ', 'ㄹㅁ': 'ㄻ'}


class Hangul():
    chosung = ""
    jungsung = ""
    jongsung = ""
    jongsung2 = ""
    step = 0
    searchlastkey = [-1, 0]



    def compose_jamo(self, cho, jung, jong=''):
        if cho in LEADING_CONSONANTS and jung in VOWELS:
            code = 0xAC00 + INDEX_BY_LEADING_CONSONANT[cho] * 588 + INDEX_BY_VOWEL[jung] * 28
            end = ''
            if jong in TRAILING_CONSONANTS:
                code += INDEX_BY_TRAILING_CONSONANT[jong]
            else:
                end = jong
            return chr(code) + end
        else:
            return cho + jung + jong


    def getHangul(self, step=-1):
        if step == -1: step = self.step
        if step == 0:
            return self.chosung
        elif step == 1:
            return self.compose_jamo(self.chosung, self.jungsung)
        elif step == 2:
            return self.compose_jamo(self.chosung, self.jungsung, self.jongsung)
        elif step == 3:
            jamojoin = self.jongsung + self.jongsung2
            if jamojoin in COMPLEXJOOGSUNG.keys():
                return self.compose_jamo(self.chosung, self.jungsung, COMPLEXJOOGSUNG[jamojoin])
            else:
                return self.compose_jamo(self.chosung, self.jungsung, self.jongsung) + self.jongsung2
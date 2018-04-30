import re
import pypinyin
import subprocess
import sqlite3
import os
import settings


CREATE_NO_WINDOW=0x08000000


def createDatabase():
    dbconn = sqlite3.connect(os.path.join(settings.programDir, settings.config['sqlitefile']))
    dbconn.row_factory = sqlite3.Row
    return dbconn

def get_initials(word):
    split=pypinyin.lazy_pinyin(word, errors=lambda w: [m.group() for m in re.finditer('[A-Za-z]+|[0-9]', w)])
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

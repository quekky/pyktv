import re
import pypinyin


def get_initials(word):
    split=pypinyin.lazy_pinyin(word, errors=lambda w: [m.group() for m in re.finditer('[A-Za-z]+|[0-9]', w)])
    return ''.join([x[0] for x in split]).upper()


def setZeroMargins(layout):
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(0)
    return layout
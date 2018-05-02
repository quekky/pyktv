#!/usr/bin/env python

"""Simple KTV software for home use

Feel free to use in your small business as well
copyleft quekky
"""

import os
import sys
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication, qApp

from layout import VideoWindow, SelectorWindow
import settings
import screen
import playlist
import webapp


if __name__ == '__main__':
    settings.__init__()
    webapp.__init__()
    app = QApplication(sys.argv)
    qApp.setOrganizationName('pyktv')
    qApp.setApplicationName('songeditor')
    qApp.setWindowIcon(QIcon(os.path.join(settings.programDir, 'themes/pyktv.ico')))
    settings.videoWindow = VideoWindow()
    settings.selectorWindow = SelectorWindow()
    screen.startHomeScreen()
    settings.videoWindow.raise_()
    playlist.__post_init__()

    ###debuging
    #screen.titleSearch()
    #screen.indexSearch()
    #screen.artistSearch1(None)
    #screen.artistSearch3({'display': '组合', 'region': '華語', 'type': '男歌手'})
    #screen.artistSearch4( {'display': '黃明志', 'region': '華語', 'type': '男歌手', 'name': '黃明志'})
    # screen.youtubeScreen1()
    # screen.youtubeScreen2({'id': 1, 'name': 'Popular Music in Singapore', 'url': 'https://www.youtube.com/playlist?list=PLsn0k7lyjYpl_uyG35AKRrj2toaJoi_gH', 'enable': 1, 'display': 'Popular Music in Singapore'})
    # screen.youtubeScreen2({'id': 2, 'name': 'Latest Music Videos','url': 'https://www.youtube.com/playlist?list=PLFgquLnL59akA2PflFpeQG9L01VFg90wS', 'enable': 1,'display': 'Latest Music Videos'})
    # playlist.addVideo({"display":"test","url":"https://www.youtube.com/watch?v=vMCqvEPBGlA","youtube":True})
    # playlist.addVideo({'channel': 'R', 'library': 'Z:\\KTV\\Videos\\流行歌曲','media_file': '\\0.其他\\羅嘉良 + 吳鎮宇 + 張可頤 + 宣萱 - 難兄難弟 [KTV].mpg', 'remark': '羅嘉良 + 吳鎮宇 + 張可頤 + 宣萱', 'display': '難兄難弟 《羅嘉良,吳鎮宇,張可頤,宣萱》  （粵,合唱）'})
    # playlist.addVideo({'channel': '1', 'library': r'Z:\KTV\Videos\流行歌曲','media_file': r'\男\黃明志\黃明志 feat  王力宏 - 漂向北方(KTV).mp4', 'display': '漂向北方 《黃明志,王力宏》  （粵,合唱）'})
    # playlist.addVideo({'url': 'pWvPXTWUexk', 'display': '王力宏 Leehom Wang《奇遇的起點 Singularity》官方 Official MV', 'youtube': True})
    # playlist.addVideo({'url': 'W5LzxmZUwhs', 'display': '68 鄭君綿 + 許艷秋 中馬票 1970', 'youtube': True})
    # playlist.addVideo({'url': 'JQGRg8XBnB4', 'display': '[MV] MOMOLAND (모모랜드) _ BBoom BBoom (뿜뿜)', 'youtube': True})
    # screen.networkSearch1()

    sys.exit(app.exec_())

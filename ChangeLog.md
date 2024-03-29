## version 2023.12.25-beta

- Fix bug with Database Indexing

## version 2021.12.25-beta

- Add option to have second audio from as a different file (Note: mpv may have a lag when switching audio from youtube)
- Add QR code link on main screen
- Fix youtube "Auto set volume"


## version 2021.08.09-beta

- Add YouTube search in webapp


## version 2021.01.14-beta

- Fix web app search unable to search for certain text


## version 2018.06.08-beta

- Rewrite the code for Hangul (Korean) search, now supports complex jamo (CVCC) (eg 훯), and remove the need for external package
- Fix cx_freeze with gevent 1.2.3
- Bugfix


## version 2018.06.01-beta

- Search using Jap and Korean
- Bugfix


## version 2018.05.30-beta

- Added video jump forward, jump backwards, pause
- Bugfix
  - Fix OnsenUI version to 2.9.2 instead of latest version (which is buggy)
  - Index search - search startswith (instead of search in any part of the string)
  - other bugfix


## version 2018.05.24-beta

- Added a small program to show what is the key pressed (to map special keys in the config.ini, eg remote controls buttons usually return special keys)
- Support for CDG files
- If alphabets (A-Z) are mapped to run functions, ignore them in the search
- Bugfix


## version 2018.05.02-beta

- Popular songs (only songs played after certain time is consider popular)
- Library supports mirror dir
- Realtime replace dir separator with the system separator
- [Song Editor] Speed up volume detection by running ffmpeg in parallel
- [Song Editor] Save/restore window position
- Bugfix

With this release, you can have players in both Windows and Linux using the same database,
with the files in shared drives. As Windows use UNC and Linux use mountpoint, you can put
1 in the root_path and the other in mirror. Also Linux does not support "\", program will
auto replace it with "/" (or whatever the system supposed to be)


## version 2018.04.29-beta

- Volume for each song (please use the new DB format)
- [Song Editor] added a few new features for song:
  - Translate title and singers between TC and SC
  - Check if media is valid
  - Find the loudness and set the volume for each song
  - (right click on the song to find the new feature)
- Bugfix


## version 2018.04.25-beta

- [Song Editor] - a new program to edit the database
- Replace xpinyin with pypinyin
- Bugfix


## version 2018.04.20-beta

- Web server support (browse on your smartphone/tablet port 5000)
- Allow change of keyboard mapping
- Common functions can now be clicked (for touch screen)
- Bugfix


## version 2018.04.17-beta

- Web server support (browse on your smartphone/tablet port 5000)
- update to youtube_dl 2018.4.16
- Bugfix


## version 2018.04.10-beta

- Browse and play from DLNA servers on local network
- Bugfix


## version 2018.04.07-beta

- Use coding to create the labels and buttons for the selector.
  Now the background image does not need to manually draw the lines/boxes/numberings for the labels
- Add shortcuts on right-click menu
- Show/hide the selector window on keyboard input
- Bugfix


## version 2018.04.04-beta

- Change from VLC to MPV (switching audio tracks do not have long delay now)
- Implement pitch control (key-up/key-down)
- update to youtube_dl 2018.4.3
- minor bugfix


## version 2018.03.09-beta

- implement randomplay on idle
- minor bugfix


## Initial release 2018.03.07 beta

- Video playback using VLC 3
- GUI using pyqt5
- YouTube features using youtube-dl 2018.3.3
- Chinese text to pinyin using xpinyin, from https://github.com/lxneng/xpinyin
  - Updated Mandarin.dat from https://github.com/fayland/perl-lingua-han/blob/master/Lingua-Han-PinYin/lib/Lingua/Han/PinYin/Mandarin.dat

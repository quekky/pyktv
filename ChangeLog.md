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

# INSTALLATION

_Installation had been tested only in Windows. Other OS might work (provided MPV can run), however I'll not be able
to test it out._

1. Edit the config.ini according to your needs
2. Find some KTV videos (due to copyright and file size, I'm not able to provide them)
3. Run songeditor.exe to modify the database. If not sure on the fields, see <a href="#database-format">below</a> for more info
4. Run the program


# DESCRIPTION

pyktv is a simple KTV program for home use. It support dual screen (and works best on dual screen), with 1 main TV 
playing the video, and another smaller screen for selecting the songs.

Current pyktv features:
* Search by song name
* Select by index number
* Select by Artist, sub-divide to region and type. It is up to you to define what is region and type (eg,
  region is country of singer, type is male/female/group/etc) 
* Select by song category
* Select by number of characters
* Youtube playlist
* DLNA support, pyktv will automatically find DLNA servers on your network
* Web server


# USAGE

## Keyboard

 key       | description
 ----------|------------------------------------------------
 F1-F4     | As seen on screen
 0-9       | As seen on screen
 F5/Pgup   | Page up
 F6/Pgdn   | Page down
 F10       | Next song
 F12       | Main menu
 Spacebar  | (Local) Switch between voice and music tracks <br> (Youtube) Switch between stereo/left/right
 Backspace | Previous page
 A-Z       | During search, you can use A-Z to search
 \-        | Key down
 \+        | Key up
 =         | Key reset


Edit config.ini to change the default settings

Mouse/touchscreen works as well


## Web server

pyktv have a very simple web server. Use your smartphone/tablet to browse to your computer port 5000.

eg, http://{computer_ip}:5000/ _(replace computer_ip with your actual computer IP address)_


# CONFIGURATION

Read config.ini on how to edit


# DATABASE FORMAT

Google for programs to edit sqlite file.

There are 3 tables in the database.

## song

 Field        | Description                                       
--------------|---------------------------------------------------
 id           | Running number                                    
 index        | index number, for selecting by index              
 title        | title of the song                                 
 search       | search (must be A-Z in caps)                      
 chars        | number of char in title                           
 singer       | artist                                            
 singer2      | for multiple artist, use singer2-10 in order      
 singer3      |                                                   
 singer4      |                                                   
 singer5      |                                                   
 singer6      |                                                   
 singer7      |                                                   
 singer8      |                                                   
 singer9      |                                                   
 singer10     |                                                   
 language     | language of song                                  
 style        | song category                                     
 channel      | which channel is music only (L, R, 0, 1)          
 library      | which library it belongs to
 volume       | Volume to increase (in decibel(dB)), put - to decrease
 media_file   | media file name within the library                
 remark       | remarks                                           

_rest of fields not used_

*note: library and media_file must be filled in*
The final file name will be library+media_file


## singer

 Field        | Description                                       
--------------|---------------------------------------------------
 id           | Running number                                    
 name         | singer name   
 search       | search (must be A-Z in caps)                      
 region       | region of singer                                  
 type         | type of singer (eg M/F/Group/etc)                 
 remark       | remarks                                           

_rest of fields not used_


## youtube

 Field        | Description                                       
--------------|---------------------------------------------------
 id           | Running number                                    
 name         | name for display                                  
 user         | user of the playlist/channel                      
 url          | youtube url                                       
 enable       | 1=enable, 0=disable                               

YouTube plugin only supports playlist (https://www.youtube.com/playlist?list=xxx), user playlist 
(https://www.youtube.com/user/xxx/playlists), and user (https://www.youtube.com/user/ziller)

I will recommend not to link to a huge list, as it takes a long time to download the list everytime it is clicked.
For some youtube users who have a big list, I'll suggust that you point to their playlists instead 
(https://www.youtube.com/user/xxx/playlists)

And of course Internet connection is required for YouTube to work.


## library

 Field        | Description
--------------|---------------------------------------------------
 id           | Running number
 root_path    | The root directory
 enabled      | 1=enable, 0=disable
 last_mirror  | for future expansion
 mirror1      | Alternate dir. Not used at the moment, for future expansion
 mirror2      |
 mirror3      |
 mirror4      |
 mirror5      |
 mirror6      |
 mirror7      |
 mirror8      |
 mirror9      |
 mirror10     |
 available    | for future expansion


# DEVELOPER

To run from sourcecode, install the python packages according to requirements.txt

$ pip install -r requirements.txt

Download MPV library from https://mpv.io/ and put it in the path (For Windows, download **mpv-1.dll**)
If there's no library for the OS you're using, you'll need to compile it from MPV source and drop the library file
in the root of the project

After downloading youtube_dl source (or from pip), edit the code https://github.com/rg3/youtube-dl/issues/15787


# FAQ

### Unable to play xxx file format

The program use MPV to play file.

Try download MPV from their site and playing the video using MPV. If it not able to play the video file, but other
players is able to play it, report the bug to MPV.

_(MPV uses ffmpeg to decode almost all videos, so it should be able to play almost any video)_

### Unable to play any Youtube video

Make sure youtube-dl.exe in the same directory as the program, MPV will require youtube-dl.exe to play the video

### Unable to play some Youtube video

Some of the Youtube videos are restricted by country. Make sure that you can play it on your browser on the same
computer. If it can be play, try playing it in MPV.

### Unable to show certain YouTube playlist

The program is using youtube-dl to download the playlist (current version 2018.4.3)
   
Try downloading youtube-dl.exe and run ```youtube-dl.exe -j --flat-playlist url``` If it is not able to download,
report bug under youtube-dl project. If the latest version is working, let me know the url so that I can update the 
library

### When I try your program after unzipping the release, videos are not playing

Due to copyright (and huge video files), I **cannot** provide you with the ktv video files. You'll need to buy the video
files/vcd and edit the database yourself. 

### Why is the release so big?

Due to the number of 3rd party libraries used, those libraries are huge!

# INSTALLATION

_Installation had been tested only in Windows. Other OS might work (provided VLC can run), however I'll not be able 
to test it out._

1. Install VLC 3.x. Make sure the libvlc is able to find your VLC installation (for Windows it should be automatic)
2. Edit the config.ini according to your needs
3. Find some KTV videos (due to copyright and file size, I'm not able to provide them)
4. Use any sqlite program to modify the database
5. Run the program


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
 library      | which library it belongs to, for future expansion 
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


# DEVELOPER

To run from sourcecode, the following python packages is required:

* PyQt5 
* python-vlc 3.x
* youtube_dl


# FAQ

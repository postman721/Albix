# Albix
Albix music player (Python+Pygame)

![albix3](https://user-images.githubusercontent.com/29865797/31854798-edaf06e2-b6a7-11e7-8bce-539a77f4d6a8.jpg)


<b>License</b>

#Albix 3.0 (PostX 0.5 revision 1.) Copyright (c) 2017 JJ Posti <techtimejourney.net>

#This program comes with ABSOLUTELY NO WARRANTY;

#for details see: http://www.gnu.org/copyleft/gpl.html.

#This is free software, and you are welcome to redistribute it under

#GPL Version 2, June 1991″)

 ___________________________

<b>Dependencies:</b>

python-qt5, python-pygame, python-mutagen

The packages below (or similar) might be needed to get installed if the above packages do not pull them as dependencies (for some odd reason):

python,python3. In almost every case, python is already installed on a desktop Linux system.

 ________________________

<b>New & Changed features in Albix 3.0</b>

– Outlook is now done via CSS. Colours are dark and easy for the eyes. and the generic outlook is gone.

– Jump to a position. New: This is now an actual slider – instead of an input box. Also, if you open Albix via terminal you can see the jump position time value printed in to terminal. Time value is not yet integrated to the Gui.

-Albix 3.0 fetches duration of an ogg file and – since 3.0 – also mp3´s duration info via python-mutagen. Duration info gets printed to the statusbar along with the playing item name. If Albix fails to fetch the duration info, or info in general, nothing may get printed to the statusbar. If info fetching fails, you might experience some trouble using position slider – or you might see partial and inaccurate info.

-Play a single song mode, which was present in the older version is now removed due to

its problematic handling of mp3 & ogg files.

-If you stop playback by pressing the stop then you must create a new playlist.

When you add files to a playlist the old entries will automatically clear out.

The dialog for adding files is now a bit more helpful than it was before.

–Albix no longer adds full path of the song to the list. Instead, something like sample.mp3 gets added. This means that you need to add files that are in the same directory (Albix needs to be able to parse the full pathway correctly behind the scenes).

-Albix 3.0 has a plenty of error handling features in it. You should not need to worry about crashing the Gui anymore. Error handling should capture all the common exceptions that might occur in a regular usage.

_________________

<b>Features that come from earlier versions</b>

– Add multiple songs to the list.

– Remove a selected song from the playlist.

– Toggle Pause/Play.

– Stop playback.

– Play the next song.

-Currently, Albix supports playing multiple songs in a row.

The playback needs to be triggered manually by pressing the play/next button.

_____________________

<b>Other instructions.</b>

If you have letters or markings that show up as squares within the file´s name then change them to something else, because otherwise the playback fails.

When adding files you can add them at any order. To choose multiple files you can, for example, hold the Control-key and click the files individually to select them. Alternatively, you can click and hold-down a mouse button and paint all the songs blue(selected) by moving your mouse.



<b>To run the program</b>

Open terminal and do: python albix.py

If you need to make the file executable: chmod +x albix.py

_____________________________________
Original post is at:
https://www.techtimejourney.net/albix-3-0-arrives/

## Albix Player 

Albix is a clean, keyboard-friendly media player written in Python with a modern PyQt UI.
It plays your local audio/video files, streams internet radio, saves/loads playlists, and (optionally) fetches song lyrics in a dockable pane.

<img width="1259" height="724" alt="Image" src="https://github.com/user-attachments/assets/e0d71bb8-cb68-458c-9b70-c79746e1fe61" />

### Features

<b> PyQt6 and PyQt5 compatible (auto-fallback). </b>

- Local media: MP3, OGG, FLAC, WAV, MP4, AVI, MKV, MOV, WMV (OS codecs permitting).

- Internet radio: double-click a station, or add your own (name + URL).

- Playlist management: add, remove, reorder by dragging, save to/load from JSON.

- Playback controls: Play/Pause, Stop, Next/Prev, Seek slider, Volume, Mute.

- Drag & drop files into the playlist.

- Lyrics toggle button (optional module) with per-track fetching.


<img width="1261" height="722" alt="Image" src="https://github.com/user-attachments/assets/6f2e9abe-4c8b-43ff-a2ae-141644fff0de" />
- Radio stations + “Add custom station”. More stations added.

- Video playback via QVideoWidget.

- New UI: Compact dark theme, hoverable buttons, fullscreen video.

- Next/Previous track, Shuffle & Repeat (auto-advance to next track).

- Mute + volume slider.

##### Playlist saving:
- Save/Load playlist (JSON. Remember to save with filepath, for example: test.json ).


##### Shuffle/Repeat:

- Shuffle picks a random next track.

- Repeat replays the current track when it ends.

Otherwise Albix automatically plays the next item in the list.

<img width="1258" height="734" alt="Image" src="https://github.com/user-attachments/assets/aaa1ac69-6ab4-44a7-8d8d-d30d71b97711" />
Lyrics (optional): toggle a dockable lyrics pane. Tries sidecar file → tags/filename → online (lyrics.ovh).


### Install (Debian/Ubuntu) – PyQt6 (recommended)

Qt6 Multimedia on Debian uses its own FFmpeg backend; GStreamer is not required for Albix on PyQT6.

		sudo apt-get update
		sudo apt-get install \
		python3-pyqt6 \
		python3-pyqt6.qtmultimedia \
		libqt6multimedia6 \
		libqt6multimediawidgets6 \
		ffmpeg \
		libavcodec-extra \
		python3-requests \
		python3-mutagen		

###### Wayland support for Qt6 (if you run Wayland)
		sudo apt-get install qt6-wayland
  
###### Optional packages;  
		python3-mutagen: #improves artist/title detection from tags.
		ffmpeg: #Having it installed does not hurt.
  
  
### PyQt5 alternative (if you prefer Qt5)

		sudo apt-get install \
		python3-pyqt5 \
		python3-pyqt5.qtmultimedia \
		libqt5multimedia5-plugins \
		python3-requests

###### Qt5 often benefits from system GStreamer codecs:

		sudo apt-get install \
		gstreamer1.0-plugins-base \
		gstreamer1.0-plugins-good \
		gstreamer1.0-plugins-bad \
		gstreamer1.0-plugins-ugly \
		gstreamer1.0-libav

- The <b> Optional packages </b> section might be useful here as well, depending on Python QT5 version.

### Run

		chmod +x albix.py albix_lyrics.py
		python3 albix.py



### Usage

- Add files: Click Add (or drag & drop files onto the playlist).

- Play: Select an item and press Play (double-click also plays).

- Stop / Next / Prev: Use the respective buttons.

- Seek: Drag the playback slider.

- Volume / Mute: Under the slider.

- Shuffle / Repeat: Toggle buttons in the control row.

- Radio: Open the Radio Stations tab, double-click a station, or create one.

- Lyrics: Press Lyrics to show/hide the pane.


### Keyboard shortcuts

- P — Play/Pause  -> When focus is on the playlist.

- F11 — Full screen (Esc to exit).

- Ctrl+L — Toggle lyrics (when the module is present).


### Known issues

- Wayland: Qt may log “Wayland does not support QWindow::requestActivate()” when trying to raise windows; Albix avoids forcing activation, but the message may still appear.

- Codecs: If a file won’t play, ensure ffmpeg/libavcodec-extra (Qt6) or GStreamer plugins (Qt5) are installed.

- Lyrics API: Online fetching uses a public endpoint (lyrics.ovh). Availability is not guaranteed; sidecar files are the most reliable.

- Small theming issues on dialogs.

- If you want to permanently add a new radio station, it needs to be added to the list on albix.py code.

### License

##### License: GPL v2
##### Author: JJ Posti <techtimejourney.net> 2025

# Albix Player 5.0

Albix Player is a sleek and user-friendly media player built with Python and PyQt5.
![Image](https://github.com/user-attachments/assets/789639ea-f0e0-4463-bd0d-bda271deb813)

New features (besides the original functionality):
 - Next/Previous track buttons
 - Shuffle & Repeat toggle
 - Mute button
 - Save & Load playlist (JSON-based)
 - Add custom radio station
 - Drag & drop support for adding files

### Features

- **Add Songs:** Easily add multiple songs to your playlist.
- **Play/Pause:** Control playback with intuitive play and pause buttons.
- **Stop Playback:** Completely stop the current song.
- **Remove Songs:** Remove selected songs from your playlist.
- **Playback Slider:** Seek through songs using the playback slider.
- **Volume Control:** Adjust the playback volume to your preference.
- **Playlist Management:** Efficiently manage your list of songs.
- **Error Handling:** Gracefully handles playback errors and missing files.
- **Responsive UI:** Interactive buttons with hover effects for enhanced user experience.
- **Video Playback**: Play local video files.
- **Radio Stations**: Stream live radio stations directly from the application.
![radio](https://github.com/user-attachments/assets/34b5aa4a-0288-4f7a-8a69-9f649ba454e1)


### Installation - with all media packages
```bash
sudo apt-get update
sudo apt-get install \
  python3-pyqt5 \
  python3-pyqt5.qtmultimedia \
  libqt5multimedia5-plugins \
  gstreamer1.0-plugins-base \
  gstreamer1.0-plugins-good \
  gstreamer1.0-plugins-bad \
  gstreamer1.0-plugins-ugly \
  gstreamer1.0-libav

```

### Run Albix Player

Navigate to the project directory and execute the player script.

python3 albix.py

### Usage

    Launch the Application: Run the Albix Player script to open the application window.
    Add Songs: Click on the "Add Song" button to select and add music files to your playlist.
    Play/Pause: Use the "Play" button to start playback. The button toggles to "Pause" when playing.
    Stop Playback: Click the "Stop" button to halt playback completely.
    Remove Songs: Select one or more songs from the playlist and click "Remove" to delete them.
    Seek Through Songs: Drag the playback slider to jump to a specific part of the song.
    Adjust Volume: Use the volume slider to increase or decrease the playback volume.
    Double-Click to Play: Double-click any song in the playlist to start playing it immediately.
    F11: Toggle full screen.
    Keyboard keypress p: Toggle play/pause.


## License

Albix Player 5.0 is released under the GNU General Public License v2. This program comes with ABSOLUTELY NO WARRANTY.

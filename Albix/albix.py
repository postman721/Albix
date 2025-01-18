#!/usr/bin/env python3

"""
Albix Player 4.5
----------------
A media player built with PyQt5 that supports both audio and video playback,
as well as streaming radio stations.

This program comes with ABSOLUTELY NO WARRANTY; 
for details see: http://www.gnu.org/copyleft/gpl.html.

This is free software, and you are welcome to redistribute it under 
GPL Version 2, June 1991.

Author: JJ Posti <techtimejourney.net>
"""

import sys
import os
from os.path import basename, splitext
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QUrl, QTimer, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QListWidget, QFileDialog, QSlider, QAbstractItemView, QMessageBox, QLabel, QTabWidget
)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import QPropertyAnimation


class AnimatedButton(QPushButton):
    """
    A QPushButton subclass that handles animated hover effects.
    Provides a default and hover style, as well as opacity animations.
    """
    def __init__(self, *args, **kwargs):
        super(AnimatedButton, self).__init__(*args, **kwargs)

        self.default_style = """
            QPushButton {
                color: #333333; 
                background-color: #ffffff; 
                border: 2px solid #cccccc; 
                border-radius: 8px;
                padding: 10px;
                min-width: 80px;
                font-weight: bold;
            }
        """

        self.hover_style = """
            QPushButton {
                color: #ffffff; 
                background-color: #4CAF50; 
                border: 2px solid #4CAF50; 
                border-radius: 8px;
                padding: 10px;
                min-width: 80px;
                font-weight: bold;
            }
        """

        self.setStyleSheet(self.default_style)

        # Initialize the opacity animation
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)

    def enterEvent(self, event: QtCore.QEvent) -> None:
        """
        Triggered when the mouse enters the button area.
        Changes style and starts opacity animation.
        """
        self.setStyleSheet(self.hover_style)
        self.animation.stop()
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.95)
        self.animation.start()
        super(AnimatedButton, self).enterEvent(event)

    def leaveEvent(self, event: QtCore.QEvent) -> None:
        """
        Triggered when the mouse leaves the button area.
        Resets style and stops opacity animation.
        """
        self.setStyleSheet(self.default_style)
        self.animation.stop()
        self.animation.setStartValue(0.95)
        self.animation.setEndValue(1.0)
        self.animation.start()
        super(AnimatedButton, self).leaveEvent(event)


class MainWindow(QMainWindow):
    """
    Main window class for Albix Player.

    Handles:
    - Loading and playing local audio & video files.
    - Streaming radio from predefined stations.
    - Managing the current playlist and media player.
    - Displaying video content in a QVideoWidget.
    """

    SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mkv", ".mov", ".wmv"}
    SUPPORTED_AUDIO_EXTENSIONS = {".mp3", ".ogg", ".flac", ".wav"}

    def __init__(self):
        super(MainWindow, self).__init__()

        # =========== Window Setup ===========
        self.setWindowTitle("Albix Player")
        self.setGeometry(100, 100, 900, 700)  # Increase width for additional UI elements
        self.setStyleSheet("""
            QMainWindow {
                color: #333333; 
                background-color: #f5f5f5; 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 12px;
            }
            QPushButton {
                color: #333333; 
                background-color: #ffffff; 
                border: 2px solid #cccccc; 
                border-radius: 8px;
                padding: 10px;
                min-width: 80px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: #ffffff; 
                background-color: #4CAF50; 
                border: 2px solid #4CAF50;
            }
            QListWidget {
                color: #333333; 
                background-color: #ffffff; 
                border: 2px solid #cccccc; 
                border-radius: 8px;
                selection-background-color: #4CAF50;
                selection-color: #ffffff;
            }
            QListWidget::item:selected {
                background-color: #4CAF50;
                color: #ffffff;
            }
            QSlider::groove:horizontal {
                border: 1px solid #cccccc;
                height: 8px;
                background: #e0e0e0;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #4CAF50;
                border: 1px solid #4CAF50;
                width: 14px;
                margin: -3px 0;
                border-radius: 7px;
            }
            QLabel {
                color: #333333;
                font-size: 10px;
            }
            QSlider::sub-page:horizontal {
                background: #4CAF50;
                border: 1px solid #4CAF50;
                border-radius: 4px;
            }
            QSlider::add-page:horizontal {
                background: #e0e0e0;
                border: 1px solid #e0e0e0;
                border-radius: 4px;
            }
        """)

        # =========== QMediaPlayer Setup ===========
        self.player = QMediaPlayer()
        self.player.stateChanged.connect(self.update_play_button)
        self.player.positionChanged.connect(self.update_slider)
        self.player.durationChanged.connect(self.set_duration)
        self.player.mediaStatusChanged.connect(self.handle_media_status)
        self.player.error.connect(self.handle_error)

        # Track current media type: 'audio' or 'video'
        self.current_media_type = 'audio'

        # =========== Playlist & Indices ===========
        # Each item in playlist will be a dict: {"path": str, "type": "audio" or "video"}
        self.playlist = []
        self.current_song_index = -1
        self.current_radio = None  # Currently playing radio station

        # =========== Radio Stations ===========
        self.radio_stations = {
            "Triple J (Australia)": "http://live-radio01.mediahubaustralia.com/2TJW/mp3/",
            "Radio Paradise (USA)": "http://stream.radioparadise.com/mp3-192",
            "FIP (France)": "http://icecast.radiofrance.fr/fip-midfi.mp3",
            "SomaFM: Indie Pop Rocks (USA)": "https://ice2.somafm.com/indiepop-128-mp3",
            "Radio Nova (France)": "http://novazz.ice.infomaniak.ch/novazz-128.mp3",
            "181.fm The Rock! (USA)": "http://listen.181fm.com/181-rock_128k.mp3",
            "Big R Radio: Top 40 Hits (USA)": "http://bigrradio.cdnstream1.com/5104_128",
            "NRJ Hits (France)": "http://cdn.nrjaudio.fm/audio1/fr/30001/mp3_128.mp3",
        }

        # =========== UI Setup ===========
        self.setup_ui()

    def setup_ui(self):
        """
        Initialize and arrange the main UI components.
        """
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # ---------- Video Widget ----------
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumSize(640, 360)
        self.video_widget.hide()  # Hide by default (will show when playing video)
        main_layout.addWidget(self.video_widget)

        # Connect player to the video widget
        self.player.setVideoOutput(self.video_widget)

        # ---------- Tabs: Local Files & Radio ----------
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)
        self.tab_widget.setTabShape(QTabWidget.Rounded)
        self.tab_widget.setStyleSheet("""
            QTabBar::tab {
                background: #ffffff;
                border: 1px solid #cccccc;
                padding: 10px;
                min-width: 100px;
            }
            QTabBar::tab:selected {
                background: #4CAF50;
                color: #ffffff;
            }
        """)

        self.music_tab = QWidget()
        self.radio_tab = QWidget()

        self.tab_widget.addTab(self.music_tab, "Local Files")
        self.tab_widget.addTab(self.radio_tab, "Radio Stations")

        self.setup_music_tab()
        self.setup_radio_tab()

        main_layout.addWidget(self.tab_widget)

        # ---------- Playback Slider & Time Labels ----------
        slider_layout = QHBoxLayout()
        slider_layout.setAlignment(Qt.AlignVCenter)

        self.current_time_label = QLabel("00:00")
        slider_layout.addWidget(self.current_time_label)

        self.playback_slider = QSlider(Qt.Horizontal)
        self.playback_slider.setRange(0, 0)
        self.playback_slider.sliderMoved.connect(self.seek_position)
        self.playback_slider.setEnabled(False)
        slider_layout.addWidget(self.playback_slider)

        self.total_time_label = QLabel("00:00")
        slider_layout.addWidget(self.total_time_label)

        main_layout.addLayout(slider_layout)

        # ---------- Volume Control ----------
        volume_layout = QHBoxLayout()
        volume_layout.setAlignment(Qt.AlignRight)

        self.volume_label = QLabel("Volume:")
        volume_layout.addWidget(self.volume_label)

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)  # Default volume
        self.volume_slider.setFixedWidth(150)
        self.volume_slider.valueChanged.connect(self.change_volume)
        volume_layout.addWidget(self.volume_slider)

        main_layout.addLayout(volume_layout)

        # ---------- Status Bar ----------
        self.status_bar = QtWidgets.QStatusBar()
        self.setStatusBar(self.status_bar)

    def setup_music_tab(self):
        """
        Create the layout and controls for the 'Local Files' tab.
        """
        music_layout = QVBoxLayout(self.music_tab)

        # ----------- Control Buttons -----------
        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)

        # Add Song/Video
        self.add_button = AnimatedButton("Add Song/Video")
        # Safely set icons if they exist, otherwise ignore
        if os.path.exists("add.png"):
            self.add_button.setIcon(QIcon("add.png"))
        self.add_button.setIconSize(QtCore.QSize(24, 24))
        self.add_button.clicked.connect(self.add_songs)
        control_layout.addWidget(self.add_button)

        # Play/Pause
        self.play_button = AnimatedButton("Play")
        if os.path.exists("play.png"):
            self.play_button.setIcon(QIcon("play.png"))
        self.play_button.setIconSize(QtCore.QSize(24, 24))
        self.play_button.clicked.connect(self.play_pause_song)
        self.play_button.setEnabled(False)
        control_layout.addWidget(self.play_button)

        # Stop
        self.stop_button = AnimatedButton("Stop")
        if os.path.exists("stop.png"):
            self.stop_button.setIcon(QIcon("stop.png"))
        self.stop_button.setIconSize(QtCore.QSize(24, 24))
        self.stop_button.clicked.connect(self.stop_song)
        self.stop_button.setEnabled(False)
        control_layout.addWidget(self.stop_button)

        # Remove
        self.remove_button = AnimatedButton("Remove")
        if os.path.exists("remove.png"):
            self.remove_button.setIcon(QIcon("remove.png"))
        self.remove_button.setIconSize(QtCore.QSize(24, 24))
        self.remove_button.clicked.connect(self.remove_songs)
        self.remove_button.setEnabled(False)
        control_layout.addWidget(self.remove_button)

        music_layout.addLayout(control_layout)

        # ----------- Playlist (ListWidget) -----------
        self.playlist_widget = QListWidget()
        self.playlist_widget.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.playlist_widget.itemDoubleClicked.connect(self.play_selected_song)
        self.playlist_widget.setStyleSheet("""
            QListWidget::item {
                padding: 10px;
                font-size: 12px;
            }
        """)
        music_layout.addWidget(self.playlist_widget)

    def setup_radio_tab(self):
        """
        Create the layout and controls for the 'Radio Stations' tab.
        """
        radio_layout = QVBoxLayout(self.radio_tab)

        self.radio_list_widget = QListWidget()
        self.radio_list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.radio_list_widget.itemDoubleClicked.connect(self.play_radio_station)
        self.radio_list_widget.setStyleSheet("""
            QListWidget::item {
                padding: 10px;
                font-size: 12px;
            }
        """)

        # Populate radio stations
        for station in self.radio_stations.keys():
            self.radio_list_widget.addItem(station)

        radio_layout.addWidget(self.radio_list_widget)

 # ---------- Toggle Full screen----------


    def keyPressEvent(self, event):
        """
        Handles key press events for the main window.
        Toggle fullscreen mode with F11 or Escape key.
        """
        if event.key() == Qt.Key_F11:
            if self.isFullScreen():
                self.showNormal()  # Exit fullscreen
                self.playlist_widget.show()
                self.play_button.show()
                self.stop_button.show()
                self.add_button.show()
                self.remove_button.show()
                self.tab_widget.show()
            else:
                self.showFullScreen()  # Enter fullscreen
                self.playlist_widget.hide()
                self.play_button.hide()
                self.stop_button.hide()
                self.add_button.hide()
                self.tab_widget.hide()
                self.remove_button.hide()
        elif event.key() == Qt.Key_Escape and self.isFullScreen():
            self.showNormal()  # Exit fullscreen when Escape is pressed
            self.playlist_widget.show()
            self.play_button.show()
            self.stop_button.show()
            self.add_button.show()
            self.remove_button.show()
            self.tab_widget.show()
        elif event.key() == Qt.Key_P:
            self.play_pause_song()			
            

    def add_songs(self):
        """
        Opens a file dialog to select media files and classify them 
        as 'video' or 'audio' based on the file extension.
        """
        options = QFileDialog.Options()
        # Use native dialogs if desired; currently set to not use them
        options |= QFileDialog.DontUseNativeDialog

        files, _ = QFileDialog.getOpenFileNames(
            self, 
            "Add Media Files", 
            "", 
            "Media Files (*.mp3 *.ogg *.flac *.wav *.mp4 *.avi *.mkv *.mov *.wmv);;All Files (*)", 
            options=options
        )

        if not files:
            return  # User canceled or no files selected

        for file_path in files:
            # Check if path already in the playlist
            if any(item["path"] == file_path for item in self.playlist):
                continue  # Skip duplicates

            extension = splitext(file_path)[1].lower()
            if extension in self.SUPPORTED_VIDEO_EXTENSIONS:
                media_type = "video"
            elif extension in self.SUPPORTED_AUDIO_EXTENSIONS:
                media_type = "audio"
            else:
                # For unrecognized extensions, skip or handle differently
                QMessageBox.warning(
                    self, 
                    "Unsupported Format", 
                    f"Skipping unsupported file format:\n{basename(file_path)}"
                )
                continue

            if not os.path.exists(file_path):
                QMessageBox.warning(
                    self, "File Not Found", 
                    f"The file '{basename(file_path)}' does not exist."
                )
                continue

            self.playlist.append({"path": file_path, "type": media_type})
            self.playlist_widget.addItem(basename(file_path))

        # Enable control buttons if playlist is not empty
        if self.playlist:
            self.play_button.setEnabled(True)
            self.remove_button.setEnabled(True)

    def remove_songs(self):
        """
        Removes selected items from the playlist. Stops playback if
        a currently playing item is removed.
        """
        selected_items = self.playlist_widget.selectedItems()
        if not selected_items:
            return

        for item in selected_items:
            index = self.playlist_widget.row(item)
            # Safeguard for index range
            if 0 <= index < len(self.playlist):
                self.playlist.pop(index)
                self.playlist_widget.takeItem(index)
                if index == self.current_song_index:
                    self.stop_song()

        # Adjust current_song_index if necessary
        if self.current_song_index >= len(self.playlist):
            self.current_song_index = len(self.playlist) - 1

        # Disable buttons if playlist is empty
        if not self.playlist:
            self.play_button.setEnabled(False)
            self.remove_button.setEnabled(False)

    def play_selected_song(self):
        """
        Handles the double-click event on the playlist to play the selected item.
        """
        self.current_song_index = self.playlist_widget.currentRow()
        self.current_radio = None  # Ensure radio is not playing
        self.play_song()

    def play_pause_song(self):
        """
        Toggles between play and pause states depending on current player state.
        If no track is selected but the playlist is non-empty, it plays the first track.
        """
        state = self.player.state()
        if state == QMediaPlayer.PlayingState:
            self.player.pause()
        elif state == QMediaPlayer.PausedState:
            self.player.play()  # Resume playback
        elif state == QMediaPlayer.StoppedState:
            if self.current_song_index == -1 and self.playlist:
                # No track selected, start from first
                self.current_song_index = 0
                self.playlist_widget.setCurrentRow(self.current_song_index)
            elif self.current_radio is not None:
                # If a radio station was selected, play it
                self.play_radio_station_by_name(self.current_radio)
            self.play_song()

    def play_song(self):
        """
        Plays the currently selected local media from the playlist if valid. 
        Shows or hides the video widget depending on media type.
        """
        if not (0 <= self.current_song_index < len(self.playlist)):
            return

        media_info = self.playlist[self.current_song_index]
        file_path = media_info["path"]
        media_type = media_info["type"]
        self.current_media_type = media_type

        if not os.path.exists(file_path):
            QMessageBox.warning(
                self, "File Not Found", 
                f"The file '{basename(file_path)}' was not found."
            )
            return

        # Show video widget if video; hide if audio
        if media_type == "video":
            self.video_widget.show()
        else:
            self.video_widget.hide()

        url = QUrl.fromLocalFile(file_path)
        content = QMediaContent(url)

        current_media = ""
        if self.player.media():
            current_media = self.player.media().canonicalUrl().toLocalFile()

        # Only set media if it's different from what's currently loaded
        if current_media != file_path:
            self.player.setMedia(content)

        self.player.play()
        self.playback_slider.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.status_bar.showMessage(f"Playing: {basename(file_path)}")

    def play_radio_station(self, item):
        """
        Called when a radio station is double-clicked in the list widget.
        """
        station_name = item.text()
        self.current_radio = station_name
        self.current_song_index = -1  # Stop any local track
        self.play_radio_station_by_name(station_name)

    def play_radio_station_by_name(self, station_name: str):
        """
        Play the specified radio station by name. If station not found, show warning.
        """
        if station_name not in self.radio_stations:
            QMessageBox.warning(
                self, "Station Not Found", 
                f"The radio station '{station_name}' was not found."
            )
            return

        stream_url = self.radio_stations[station_name]
        url = QUrl(stream_url)
        content = QMediaContent(url)

        # Hide the video widget for radio (generally no video)
        self.video_widget.hide()

        self.player.setMedia(content)
        self.player.play()
        self.playback_slider.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.status_bar.showMessage(f"Streaming Radio: {station_name}")

    def stop_song(self):
        """
        Stops playback, resets UI controls, and hides the video widget if it was shown.
        """
        self.player.stop()
        self.playback_slider.setValue(0)
        self.playback_slider.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.play_button.setText("Play")
        self.current_time_label.setText("00:00")
        self.status_bar.showMessage("Playback stopped.")
        self.current_radio = None
        self.video_widget.hide()

    def update_play_button(self, state: QMediaPlayer.State):
        """
        Updates the Play/Pause button text based on the media player's state.
        """
        if state == QMediaPlayer.PlayingState:
            self.play_button.setText("Pause")
        elif state == QMediaPlayer.PausedState:
            self.play_button.setText("Play")
        elif state == QMediaPlayer.StoppedState:
            self.play_button.setText("Play")

    def update_slider(self, position: int):
        """
        Synchronizes the playback slider and current time label with the player's position.
        """
        self.playback_slider.blockSignals(True)
        self.playback_slider.setValue(position)
        self.playback_slider.blockSignals(False)
        current_time = self.millis_to_time(position)
        self.current_time_label.setText(current_time)

    def set_duration(self, duration: int):
        """
        Called when the media's duration changes. Updates slider range and total time label.
        """
        self.playback_slider.setRange(0, duration)
        total_time = self.millis_to_time(duration)
        self.total_time_label.setText(total_time)

    def seek_position(self, position: int):
        """
        Seek the media to the specified position (in milliseconds).
        """
        self.player.setPosition(position)
        current_time = self.millis_to_time(position)
        self.current_time_label.setText(current_time)
        self.status_bar.showMessage(f"Seeked to: {current_time}")

    def change_volume(self, value: int):
        """
        Updates the media player's volume and the status bar.
        """
        self.player.setVolume(value)
        self.status_bar.showMessage(f"Volume: {value}%")

    def handle_media_status(self, status: QMediaPlayer.MediaStatus):
        """
        Responds to changes in the media player's status.
        If we reach the end of a local file, we move to the next item in the playlist.
        """
        if status == QMediaPlayer.EndOfMedia:
            self.next_song()

    def handle_error(self):
        """
        Called when QMediaPlayer encounters an error. Displays a message box and stops playback.
        """
        error = self.player.errorString()
        if error:
            QMessageBox.critical(
                self, "Playback Error", 
                f"An error occurred during playback:\n\n{error}"
            )
            self.stop_song()

    def next_song(self):
        """
        Advances to the next song in the playlist, or stops if at the end.
        """
        if (self.current_song_index + 1) < len(self.playlist):
            self.current_song_index += 1
            self.playlist_widget.setCurrentRow(self.current_song_index)
            self.play_song()
        else:
            self.status_bar.showMessage("End of playlist.")
            self.stop_song()

    @staticmethod
    def millis_to_time(millis: int) -> str:
        """
        Convert a time in milliseconds to a string in MM:SS format.
        """
        seconds_total = millis // 1000
        minutes = seconds_total // 60
        seconds = seconds_total % 60
        return f"{minutes:02}:{seconds:02}"


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

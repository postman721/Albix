#!/usr/bin/env python3

"""
Albix Player 5.0
------------------------------------------------
A media player built with PyQt5 that supports both audio and video playback,
as well as streaming radio stations.

New features (besides the original functionality):
 - Next/Previous track buttons
 - Shuffle & Repeat toggle
 - Mute button
 - Save & Load playlist (JSON-based)
 - Add custom radio station
 - Drag & drop support for adding files

This program comes with ABSOLUTELY NO WARRANTY; 
for details see: http://www.gnu.org/copyleft/gpl.html.

This is free software, and you are welcome to redistribute it under 
GPL Version 2, June 1991.

Author: JJ Posti <techtimejourney.net>
"""

import sys
import os
import json
import random
from os.path import basename, splitext
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import (
    Qt, QUrl, QTimer, QEasingCurve, pyqtProperty, QPropertyAnimation
)
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QFileDialog, QSlider, QAbstractItemView, QMessageBox, QLabel,
    QTabWidget, QLineEdit, QStatusBar, QMenuBar
)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget


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
    Main window class for Albix Player

    Includes:
    - Local audio & video playback
    - Streaming radio with a predefined list + custom entries
    - Next/Previous track, Shuffle & Repeat
    - Save & Load playlist (JSON)
    - Drag & drop support for media files
    - Mute button
    """

    SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mkv", ".mov", ".wmv"}
    SUPPORTED_AUDIO_EXTENSIONS = {".mp3", ".ogg", ".flac", ".wav"}

    def __init__(self):
        super(MainWindow, self).__init__()

        # =========== Window Setup ===========
        self.setWindowTitle("Albix Player")
        self.setGeometry(100, 100, 1000, 700)
        self.setAcceptDrops(True)  # Enable drag & drop onto the window

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
        # Each item in playlist is a dict: {"path": str, "type": "audio" or "video"}
        self.playlist = []
        self.current_song_index = -1
        self.current_radio = None  # Currently playing radio station

        # Shuffle & repeat states
        self.shuffle_mode = False
        self.repeat_mode = False  # Repeat the *current* song

        # =========== Radio Stations ===========
        self.radio_stations = {
            "Triple J (Australia)": "https://live-radio01.mediahubaustralia.com/2TJW/mp3/",
            "Radio Paradise (USA)": "https://stream.radioparadise.com/mp3-192",
            "FIP (France)": "https://icecast.radiofrance.fr/fip-midfi.mp3",
            "SomaFM: Indie Pop Rocks (USA)": "https://ice2.somafm.com/indiepop-128-mp3",
            "Radio Nova (France)": "https://novazz.ice.infomaniak.ch/novazz-128.mp3",
            "181.fm The Rock! (USA)": "https://listen.181fm.com/181-rock_128k.mp3",
            "Big R Radio: Top 40 Hits (USA)": "https://bigrradio.cdnstream1.com/5104_128",
            "NRJ Hits (France)": "http://cdn.nrjaudio.fm/audio1/fr/30001/mp3_128.mp3",
        }

        # =========== UI Setup ===========
        self.setup_ui()

    # ---------------- DRAG & DROP SUPPORT --------------------
    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        """
        Accept drag events that contain file URLs.
        """
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        """
        Handle file drops onto the window.
        """
        if event.mimeData().hasUrls():
            paths = [url.toLocalFile() for url in event.mimeData().urls()]
            self.process_dropped_files(paths)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    def process_dropped_files(self, files):
        """
        Adds dropped files to the playlist if supported.
        """
        for file_path in files:
            extension = splitext(file_path)[1].lower()
            if extension in self.SUPPORTED_VIDEO_EXTENSIONS:
                media_type = "video"
            elif extension in self.SUPPORTED_AUDIO_EXTENSIONS:
                media_type = "audio"
            else:
                continue  # Skip unsupported

            if not os.path.exists(file_path):
                continue

            # Avoid duplicates
            if any(item["path"] == file_path for item in self.playlist):
                continue

            self.playlist.append({"path": file_path, "type": media_type})
            self.playlist_widget.addItem(basename(file_path))

        # Enable control buttons if playlist is not empty
        if self.playlist:
            self.play_button.setEnabled(True)
            self.remove_button.setEnabled(True)
            self.prev_button.setEnabled(True)
            self.next_button.setEnabled(True)
            self.shuffle_button.setEnabled(True)
            self.repeat_button.setEnabled(True)

    # ---------------------------------------------------------

    def setup_ui(self):
        """
        Initialize and arrange the main UI components.
        """
        # Apply a simple light theme (no toggle):
        self.apply_light_theme()

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
        # Minimal tab style
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

        # ---------- Volume + Mute Button ----------
        volume_layout = QHBoxLayout()
        volume_layout.setAlignment(Qt.AlignRight)

        self.mute_button = AnimatedButton("Mute")
        self.mute_button.clicked.connect(self.toggle_mute)
        self.mute_button.setCheckable(True)
        volume_layout.addWidget(self.mute_button)

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
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # ---------- Menu Bar (Optional) ----------
        menubar = self.menuBar()

        file_menu = menubar.addMenu("File")
        save_action = QtWidgets.QAction("Save Playlist", self)
        save_action.triggered.connect(self.save_playlist)
        file_menu.addAction(save_action)

        load_action = QtWidgets.QAction("Load Playlist", self)
        load_action.triggered.connect(self.load_playlist)
        file_menu.addAction(load_action)

        exit_action = QtWidgets.QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def apply_light_theme(self):
        """
        Sets a simple light theme for the entire window (no toggle).
        """
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
            QMenuBar {
                background-color: #ffffff;
            }
            QMenuBar::item:selected {
                background-color: #4CAF50;
                color: #ffffff;
            }
        """)

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
        self.add_button.setIconSize(QtCore.QSize(24, 24))
        self.add_button.clicked.connect(self.add_songs)
        control_layout.addWidget(self.add_button)

        # Play/Pause
        self.play_button = AnimatedButton("Play")
        self.play_button.setIconSize(QtCore.QSize(24, 24))
        self.play_button.clicked.connect(self.play_pause_song)
        self.play_button.setEnabled(False)
        control_layout.addWidget(self.play_button)

        # Stop
        self.stop_button = AnimatedButton("Stop")
        self.stop_button.setIconSize(QtCore.QSize(24, 24))
        self.stop_button.clicked.connect(self.stop_song)
        self.stop_button.setEnabled(False)
        control_layout.addWidget(self.stop_button)

        # Previous
        self.prev_button = AnimatedButton("Prev")
        self.prev_button.setIconSize(QtCore.QSize(24, 24))
        self.prev_button.clicked.connect(self.prev_song)
        self.prev_button.setEnabled(False)
        control_layout.addWidget(self.prev_button)

        # Next
        self.next_button = AnimatedButton("Next")
        self.next_button.setIconSize(QtCore.QSize(24, 24))
        self.next_button.clicked.connect(self.next_song)
        self.next_button.setEnabled(False)
        control_layout.addWidget(self.next_button)

        # Remove
        self.remove_button = AnimatedButton("Remove")
        self.remove_button.setIconSize(QtCore.QSize(24, 24))
        self.remove_button.clicked.connect(self.remove_songs)
        self.remove_button.setEnabled(False)
        control_layout.addWidget(self.remove_button)

        # Shuffle
        self.shuffle_button = AnimatedButton("Shuffle OFF")
        self.shuffle_button.setCheckable(True)
        self.shuffle_button.clicked.connect(self.toggle_shuffle)
        self.shuffle_button.setEnabled(False)
        control_layout.addWidget(self.shuffle_button)

        # Repeat
        self.repeat_button = AnimatedButton("Repeat OFF")
        self.repeat_button.setCheckable(True)
        self.repeat_button.clicked.connect(self.toggle_repeat)
        self.repeat_button.setEnabled(False)
        control_layout.addWidget(self.repeat_button)

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
        Create the layout and controls for the 'Radio Stations' tab,
        including a way to add custom stations.
        """
        radio_layout = QVBoxLayout(self.radio_tab)

        # Existing radio list
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

        # Add custom station controls
        custom_station_layout = QHBoxLayout()
        self.custom_station_name = QLineEdit()
        self.custom_station_name.setPlaceholderText("Station Name")
        self.custom_station_url = QLineEdit()
        self.custom_station_url.setPlaceholderText("Stream URL")
        add_station_button = AnimatedButton("Add Station")
        add_station_button.clicked.connect(self.add_custom_station)

        custom_station_layout.addWidget(self.custom_station_name)
        custom_station_layout.addWidget(self.custom_station_url)
        custom_station_layout.addWidget(add_station_button)

        radio_layout.addLayout(custom_station_layout)

    # ---------- Fullscreen Toggle ----------
    def keyPressEvent(self, event):
        """
        Handles key press events for the main window.
        Toggle fullscreen mode with F11 or Escape key.
        Also toggles Play/Pause with 'P'.
        """
        if event.key() == Qt.Key_F11:
            if self.isFullScreen():
                self.showNormal()  # Exit fullscreen
                self.show_normal_ui_elements()
            else:
                self.showFullScreen()  # Enter fullscreen
                self.hide_ui_elements()
        elif event.key() == Qt.Key_Escape and self.isFullScreen():
            self.showNormal()  # Exit fullscreen when Escape is pressed
            self.show_normal_ui_elements()
        elif event.key() == Qt.Key_P:
            self.play_pause_song()
        else:
            super(MainWindow, self).keyPressEvent(event)

    def hide_ui_elements(self):
        """
        Hide UI elements when entering fullscreen.
        """
        self.playlist_widget.hide()
        self.play_button.hide()
        self.stop_button.hide()
        self.add_button.hide()
        self.prev_button.hide()
        self.next_button.hide()
        self.remove_button.hide()
        self.shuffle_button.hide()
        self.repeat_button.hide()
        self.tab_widget.hide()

    def show_normal_ui_elements(self):
        """
        Show UI elements when exiting fullscreen.
        """
        self.playlist_widget.show()
        self.play_button.show()
        self.stop_button.show()
        self.add_button.show()
        self.prev_button.show()
        self.next_button.show()
        self.remove_button.show()
        self.shuffle_button.show()
        self.repeat_button.show()
        self.tab_widget.show()

    # ------------------- Custom Station ---------------------
    def add_custom_station(self):
        """
        Add a custom station to the radio list and internal dictionary.
        """
        name = self.custom_station_name.text().strip()
        url = self.custom_station_url.text().strip()
        if not name or not url:
            QMessageBox.warning(self, "Invalid Input", "Station name and URL cannot be empty.")
            return

        # Add to dictionary and list widget
        self.radio_stations[name] = url
        self.radio_list_widget.addItem(name)

        # Clear text fields
        self.custom_station_name.clear()
        self.custom_station_url.clear()

    # ------------------- Playlist Management ----------------
    def add_songs(self):
        """
        Opens a file dialog to select media files and classify them 
        as 'video' or 'audio' based on the file extension.
        """
        options = QFileDialog.Options()
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
            self.prev_button.setEnabled(True)
            self.next_button.setEnabled(True)
            self.shuffle_button.setEnabled(True)
            self.repeat_button.setEnabled(True)

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
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
            self.shuffle_button.setEnabled(False)
            self.repeat_button.setEnabled(False)

    def play_selected_song(self):
        """
        Handles the double-click event on the playlist to play the selected item.
        """
        self.current_song_index = self.playlist_widget.currentRow()
        self.current_radio = None  # Ensure radio is not playing
        self.play_song()

    # ------------------- Playback Controls -------------------
    def play_pause_song(self):
        """
        Toggles between play and pause states depending on current player state.
        If no track is selected but the playlist is non-empty, it plays the first track.
        If a radio station is active, it will resume or start that station.
        """
        state = self.player.state()
        if state == QMediaPlayer.PlayingState:
            self.player.pause()
        elif state == QMediaPlayer.PausedState:
            self.player.play()  # Resume playback
        elif state == QMediaPlayer.StoppedState:
            if self.current_song_index == -1 and self.playlist:
                self.current_song_index = 0
                self.playlist_widget.setCurrentRow(self.current_song_index)
            elif self.current_radio is not None:
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

        # Hide the video widget for radio
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

    # ---------- Next/Previous/Shuffle/Repeat -----------
    def next_song(self):
        """
        Advances to the next song in the playlist, or stops if at the end.
        If shuffle is on, choose a random track. If radio is playing, stop radio first.
        """
        if not self.playlist:
            return

        self.current_radio = None
        if self.shuffle_mode:
            self.current_song_index = random.randint(0, len(self.playlist) - 1)
        else:
            if (self.current_song_index + 1) < len(self.playlist):
                self.current_song_index += 1
            else:
                self.status_bar.showMessage("End of playlist.")
                self.stop_song()
                return

        self.playlist_widget.setCurrentRow(self.current_song_index)
        self.play_song()

    def prev_song(self):
        """
        Moves to the previous song in the playlist.
        If radio is playing, just stop radio.
        """
        if not self.playlist:
            return

        self.current_radio = None
        if self.shuffle_mode:
            self.current_song_index = random.randint(0, len(self.playlist) - 1)
        else:
            if (self.current_song_index - 1) >= 0:
                self.current_song_index -= 1
            else:
                self.status_bar.showMessage("Start of playlist.")
                self.current_song_index = 0

        self.playlist_widget.setCurrentRow(self.current_song_index)
        self.play_song()

    def toggle_shuffle(self):
        """
        Toggles shuffle mode on/off.
        """
        self.shuffle_mode = not self.shuffle_mode
        if self.shuffle_mode:
            self.shuffle_button.setText("Shuffle ON")
            self.status_bar.showMessage("Shuffle Mode: ON")
        else:
            self.shuffle_button.setText("Shuffle OFF")
            self.status_bar.showMessage("Shuffle Mode: OFF")

    def toggle_repeat(self):
        """
        Toggles repeat mode on/off (repeat the current track).
        """
        self.repeat_mode = not self.repeat_mode
        if self.repeat_mode:
            self.repeat_button.setText("Repeat ON")
            self.status_bar.showMessage("Repeat Mode: ON (Current Track)")
        else:
            self.repeat_button.setText("Repeat OFF")
            self.status_bar.showMessage("Repeat Mode: OFF")

    # ---------- Volume / Mute -----------
    def change_volume(self, value: int):
        """
        Updates the media player's volume and the status bar.
        """
        self.player.setVolume(value)
        self.status_bar.showMessage(f"Volume: {value}%")

    def toggle_mute(self):
        """
        Mutes or unmutes the player.
        """
        if self.mute_button.isChecked():
            self.player.setMuted(True)
            self.status_bar.showMessage("Muted")
        else:
            self.player.setMuted(False)
            volume = self.volume_slider.value()
            self.status_bar.showMessage(f"Volume: {volume}%")

    # ---------- Slider / Time Update -----------
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

    # ---------- Media Status / Error -----------
    def handle_media_status(self, status: QMediaPlayer.MediaStatus):
        """
        Responds to changes in the media player's status.
        If we reach the end of a local file, we move to the next item in the playlist,
        or repeat if `repeat_mode` is active.
        """
        if status == QMediaPlayer.EndOfMedia:
            if self.current_radio is not None:
                pass  # Radio: do nothing special
            else:
                if self.repeat_mode:
                    self.player.setPosition(0)
                    self.player.play()
                else:
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

    # ---------- Save & Load Playlist -----------
    def save_playlist(self):
        """
        Save the current playlist to a JSON file.
        """
        if not self.playlist:
            QMessageBox.information(self, "Empty Playlist", "There is no playlist to save.")
            return

        file_name, _ = QFileDialog.getSaveFileName(self, "Save Playlist", "", "JSON Files (*.json)")
        if file_name:
            # Write to JSON
            try:
                with open(file_name, 'w', encoding='utf-8') as f:
                    json.dump(self.playlist, f, indent=4)
                QMessageBox.information(self, "Playlist Saved", f"Playlist saved to {file_name}")
            except Exception as e:
                QMessageBox.critical(self, "Error Saving Playlist", str(e))

    def load_playlist(self):
        """
        Load a playlist from a JSON file.
        """
        file_name, _ = QFileDialog.getOpenFileName(self, "Load Playlist", "", "JSON Files (*.json)")
        if file_name:
            try:
                with open(file_name, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Validate data format is a list of dict with 'path' and 'type'
                    if isinstance(data, list) and all('path' in d and 'type' in d for d in data):
                        self.playlist = data
                        self.playlist_widget.clear()
                        for item in self.playlist:
                            self.playlist_widget.addItem(basename(item['path']))

                        # Enable control buttons if playlist is not empty
                        if self.playlist:
                            self.play_button.setEnabled(True)
                            self.remove_button.setEnabled(True)
                            self.prev_button.setEnabled(True)
                            self.next_button.setEnabled(True)
                            self.shuffle_button.setEnabled(True)
                            self.repeat_button.setEnabled(True)

                        QMessageBox.information(self, "Playlist Loaded", f"Playlist loaded from {file_name}")
                    else:
                        QMessageBox.warning(self, "Invalid File", "The selected JSON does not contain a valid playlist.")
            except Exception as e:
                QMessageBox.critical(self, "Error Loading Playlist", str(e))

    # ---------- Helper -----------
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

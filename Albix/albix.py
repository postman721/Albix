# Albix Player 4.0 Version
# This program comes with ABSOLUTELY NO WARRANTY; for details see: http://www.gnu.org/copyleft/gpl.html.
# This is free software, and you are welcome to redistribute it under GPL Version 2, June 1991

#!/usr/bin/env python3

import sys
import os
from os.path import basename
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QUrl, QTimer, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QListWidget, QFileDialog, QSlider, QAbstractItemView, QMessageBox, QLabel, QGroupBox, QTabWidget
)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtCore import QPropertyAnimation


class AnimatedButton(QPushButton):
    """
    A QPushButton subclass that handles animated hover effects.
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
        self.animation = QPropertyAnimation(self, b"windowOpacity")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)

    def enterEvent(self, event):
        # Change style on hover
        self.setStyleSheet(self.hover_style)
        # Start opacity animation
        self.animation.stop()
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.95)
        self.animation.start()
        super(AnimatedButton, self).enterEvent(event)

    def leaveEvent(self, event):
        # Revert style when not hovered
        self.setStyleSheet(self.default_style)
        # Revert opacity animation
        self.animation.stop()
        self.animation.setStartValue(0.95)
        self.animation.setEndValue(1.0)
        self.animation.start()
        super(AnimatedButton, self).leaveEvent(event)


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.setWindowTitle("Albix Player")
        self.setGeometry(100, 100, 900, 700)  # Increased width for additional UI elements
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

        # Initialize QMediaPlayer
        self.player = QMediaPlayer()
        self.player.stateChanged.connect(self.update_play_button)
        self.player.positionChanged.connect(self.update_slider)
        self.player.durationChanged.connect(self.set_duration)
        self.player.mediaStatusChanged.connect(self.handle_media_status)
        self.player.error.connect(self.handle_error)

        # Initialize playlist and current song index
        self.playlist = []  # List to store full paths of songs
        self.current_song_index = -1  # Currently playing song index
        self.current_radio = None  # Currently playing radio station

        # Define Finnish radio stations
        self.radio_stations = {
            "Triple J (Australia)": "http://live-radio01.mediahubaustralia.com/2TJW/mp3/",
            # Australian station focusing on new and alternative music.

            "Radio Paradise (USA)": "http://stream.radioparadise.com/mp3-192",
            # Eclectic mix of rock, world music, and more.

            "FIP (France)": "http://icecast.radiofrance.fr/fip-midfi.mp3",
            # A wide range of genres, including rock, jazz, and world music.

            "SomaFM: Indie Pop Rocks (USA)": "https://ice2.somafm.com/indiepop-128-mp3",
            # Indie pop and alternative rock from SomaFM.

            "Radio Nova (France)": "http://novazz.ice.infomaniak.ch/novazz-128.mp3",
            # Modern rock, indie, and alternative music.

            "181.fm The Rock! (USA)": "http://listen.181fm.com/181-rock_128k.mp3",
            # A mix of modern and classic rock.

            "Big R Radio: Top 40 Hits (USA)": "http://bigrradio.cdnstream1.com/5104_128",
            # Top 40 and pop hits.

            "NRJ Hits (France)": "http://cdn.nrjaudio.fm/audio1/fr/30001/mp3_128.mp3",
            # Popular music and international hits.

        }



        # Set up UI components
        self.setup_ui()

    def setup_ui(self):
        # Central widget and main layout
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Tab widget to switch between Local Music and Radio Stations
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

        # Create tabs
        self.music_tab = QWidget()
        self.radio_tab = QWidget()
        self.tab_widget.addTab(self.music_tab, "Local Music")
        self.tab_widget.addTab(self.radio_tab, "Radio Stations")

        # Setup Music Tab
        self.setup_music_tab()

        # Setup Radio Tab
        self.setup_radio_tab()

        main_layout.addWidget(self.tab_widget)

        # Horizontal layout for playback slider and time labels
        slider_layout = QHBoxLayout()
        slider_layout.setAlignment(Qt.AlignVCenter)

        # Current Time Label
        self.current_time_label = QLabel("00:00")
        slider_layout.addWidget(self.current_time_label)

        # Playback Slider
        self.playback_slider = QSlider(Qt.Horizontal)
        self.playback_slider.setRange(0, 0)
        self.playback_slider.sliderMoved.connect(self.seek_position)
        self.playback_slider.setEnabled(False)  # Disabled until a song or radio is playing
        slider_layout.addWidget(self.playback_slider)

        # Total Time Label
        self.total_time_label = QLabel("00:00")
        slider_layout.addWidget(self.total_time_label)

        main_layout.addLayout(slider_layout)

        # Horizontal layout for volume control
        volume_layout = QHBoxLayout()
        volume_layout.setAlignment(Qt.AlignRight)

        # Volume Label
        self.volume_label = QLabel("Volume:")
        volume_layout.addWidget(self.volume_label)

        # Volume Slider
        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)  # Default volume
        self.volume_slider.setFixedWidth(150)
        self.volume_slider.valueChanged.connect(self.change_volume)
        volume_layout.addWidget(self.volume_slider)

        main_layout.addLayout(volume_layout)

        # Status Bar
        self.status_bar = QtWidgets.QStatusBar()
        self.setStatusBar(self.status_bar)

    def setup_music_tab(self):
        # Layout for Music Tab
        music_layout = QVBoxLayout(self.music_tab)

        # Horizontal layout for control buttons
        control_layout = QHBoxLayout()
        control_layout.setSpacing(10)

        # Add Song Button
        self.add_button = AnimatedButton("Add Song")
        self.add_button.setIcon(QIcon("add.png"))  # Ensure 'add.png' is in the same directory
        self.add_button.setIconSize(QtCore.QSize(24, 24))
        self.add_button.clicked.connect(self.add_songs)
        control_layout.addWidget(self.add_button)

        # Play/Pause Button
        self.play_button = AnimatedButton("Play")
        self.play_button.setIcon(QIcon("play.png"))  # Ensure 'play.png' is in the same directory
        self.play_button.setIconSize(QtCore.QSize(24, 24))
        self.play_button.clicked.connect(self.play_pause_song)
        self.play_button.setEnabled(False)  # Disabled until a song is added
        control_layout.addWidget(self.play_button)

        # Stop Button
        self.stop_button = AnimatedButton("Stop")
        self.stop_button.setIcon(QIcon("stop.png"))  # Ensure 'stop.png' is in the same directory
        self.stop_button.setIconSize(QtCore.QSize(24, 24))
        self.stop_button.clicked.connect(self.stop_song)
        self.stop_button.setEnabled(False)  # Disabled until a song is playing
        control_layout.addWidget(self.stop_button)

        # Remove Song Button
        self.remove_button = AnimatedButton("Remove")
        self.remove_button.setIcon(QIcon("remove.png"))  # Ensure 'remove.png' is in the same directory
        self.remove_button.setIconSize(QtCore.QSize(24, 24))
        self.remove_button.clicked.connect(self.remove_songs)
        self.remove_button.setEnabled(False)  # Disabled until a song is added
        control_layout.addWidget(self.remove_button)

        music_layout.addLayout(control_layout)

        # Playlist (ListWidget)
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
        # Layout for Radio Tab
        radio_layout = QVBoxLayout(self.radio_tab)

        # Radio Stations List
        self.radio_list_widget = QListWidget()
        self.radio_list_widget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.radio_list_widget.itemDoubleClicked.connect(self.play_radio_station)
        self.radio_list_widget.setStyleSheet("""
            QListWidget::item {
                padding: 10px;
                font-size: 12px;
            }
        """)

        # Populate Radio Stations
        for station in self.radio_stations.keys():
            self.radio_list_widget.addItem(station)

        radio_layout.addWidget(self.radio_list_widget)

    def add_songs(self):
        # Open file dialog to select music files
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        files, _ = QFileDialog.getOpenFileNames(
            self, 
            "Add Music Files", 
            "", 
            "Audio Files (*.mp3 *.ogg *.flac *.wav);;All Files (*)", 
            options=options
        )
        if files:
            for file in files:
                if file not in self.playlist:
                    self.playlist.append(file)
                    self.playlist_widget.addItem(basename(file))
            # Enable control buttons
            self.play_button.setEnabled(True)
            self.remove_button.setEnabled(True)

    def remove_songs(self):
        # Remove selected songs from playlist and ListWidget
        selected_items = self.playlist_widget.selectedItems()
        if not selected_items:
            return
        for item in selected_items:
            index = self.playlist_widget.row(item)
            del self.playlist[index]
            self.playlist_widget.takeItem(index)
            # If the removed song is currently playing, stop playback
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
        # Play the double-clicked song
        self.current_song_index = self.playlist_widget.currentRow()
        self.current_radio = None  # Ensure radio is not playing
        self.play_song()

    def play_pause_song(self):
        if self.player.state() == QMediaPlayer.PlayingState:
            self.player.pause()
        elif self.player.state() == QMediaPlayer.PausedState:
            self.player.play()  # Resume playback without resetting
        elif self.player.state() == QMediaPlayer.StoppedState:
            if self.current_song_index == -1 and self.playlist:
                # If no song is selected, play the first song
                self.current_song_index = 0
                self.playlist_widget.setCurrentRow(self.current_song_index)
            elif self.current_radio is not None:
                # If a radio station is selected, play it
                self.play_radio_station_by_name(self.current_radio)
            self.play_song()

    def play_song(self):
        if 0 <= self.current_song_index < len(self.playlist):
            song_path = self.playlist[self.current_song_index]
            if not os.path.exists(song_path):
                QMessageBox.warning(self, "File Not Found", f"The file '{basename(song_path)}' was not found.")
                return
            url = QUrl.fromLocalFile(song_path)
            content = QMediaContent(url)
            
            # Check if the current media is different before setting it
            current_media = self.player.media().canonicalUrl().toLocalFile() if self.player.media() else ""
            if current_media != song_path:
                self.player.setMedia(content)
            
            self.player.play()
            self.playback_slider.setEnabled(True)
            self.stop_button.setEnabled(True)
            self.status_bar.showMessage(f'Playing: {basename(song_path)}')

    def play_radio_station(self, item):
        # Play the selected radio station
        station_name = item.text()
        self.current_radio = station_name
        self.current_song_index = -1  # Ensure songs are not playing
        self.play_radio_station_by_name(station_name)

    def play_radio_station_by_name(self, station_name):
        if station_name in self.radio_stations:
            stream_url = self.radio_stations[station_name]
            url = QUrl(stream_url)
            content = QMediaContent(url)
            
            self.player.setMedia(content)
            self.player.play()
            self.playback_slider.setEnabled(True)
            self.stop_button.setEnabled(True)
            self.status_bar.showMessage(f'Streaming Radio: {station_name}')
        else:
            QMessageBox.warning(self, "Station Not Found", f"The radio station '{station_name}' was not found.")

    def stop_song(self):
        self.player.stop()
        self.playback_slider.setValue(0)
        self.playback_slider.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.play_button.setText("Play")
        self.current_time_label.setText("00:00")
        self.status_bar.showMessage('Playback stopped.')
        self.current_radio = None  # Stop any radio playback

    def update_play_button(self, state):
        if state == QMediaPlayer.PlayingState:
            self.play_button.setText("Pause")
        elif state == QMediaPlayer.PausedState:
            self.play_button.setText("Play")
        elif state == QMediaPlayer.StoppedState:
            self.play_button.setText("Play")

    def update_slider(self, position):
        # Update the playback slider and current time label
        self.playback_slider.blockSignals(True)
        self.playback_slider.setValue(position)
        self.playback_slider.blockSignals(False)
        current_time = self.millis_to_time(position)
        self.current_time_label.setText(current_time)

    def set_duration(self, duration):
        # Set the maximum value of the slider based on song duration
        self.playback_slider.setRange(0, duration)
        total_time = self.millis_to_time(duration)
        self.total_time_label.setText(total_time)

    def seek_position(self, position):
        # Seek to the specified position in the song or radio
        self.player.setPosition(position)
        current_time = self.millis_to_time(position)
        self.current_time_label.setText(current_time)
        self.status_bar.showMessage(f'Seeked to: {current_time}')

    def change_volume(self, value):
        # Change the playback volume
        self.player.setVolume(value)
        self.status_bar.showMessage(f'Volume: {value}%')

    def handle_media_status(self, status):
        if status == QMediaPlayer.EndOfMedia:
            self.next_song()

    def handle_error(self):
        error = self.player.errorString()
        if error:
            QMessageBox.critical(self, "Playback Error", f"An error occurred during playback.\n\nError: {error}")
            self.stop_song()

    def next_song(self):
        # Play the next song in the playlist
        if self.current_song_index + 1 < len(self.playlist):
            self.current_song_index += 1
            self.playlist_widget.setCurrentRow(self.current_song_index)
            self.play_song()
        else:
            self.status_bar.showMessage("End of playlist.")
            self.stop_song()

    def millis_to_time(self, millis):
        # Convert milliseconds to a MM:SS format
        seconds = millis // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02}:{seconds:02}"


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

#!/usr/bin/env python3
"""
Albix Player 6.0  (PyQt6 / PyQt5 compatible)
------------------------------------------------
Lyrics: integrated via external albix_lyrics module (show/hide only; no save/overlay UI).

License: GPL v2
Author: JJ Posti <techtimejourney.net>
"""

import sys
sys.dont_write_bytecode = True
import os
import json
import random
from os.path import basename, splitext

# ----- REQUIRE lyrics module next to this script or in PYTHONPATH -----
import albix_lyrics

# ---------------- PyQt6 first, fallback to PyQt5 ----------------
USING_QT6 = False
try:
    from PyQt6 import QtCore, QtGui, QtWidgets
    from PyQt6.QtCore import Qt, QUrl, QSize
    from PyQt6.QtGui import QIcon, QAction, QKeySequence
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
        QListWidget, QFileDialog, QSlider, QAbstractItemView, QMessageBox, QLabel,
        QTabWidget, QLineEdit, QStatusBar, QMenuBar
    )
    from PyQt6.QtMultimedia import QMediaPlayer, QAudioOutput
    from PyQt6.QtMultimediaWidgets import QVideoWidget
    USING_QT6 = True
    print("Using PyQt6")
except Exception as e:
    print("PyQt6 import failed, falling back to PyQt5:", e)
    from PyQt5 import QtCore, QtGui, QtWidgets
    from PyQt5.QtCore import Qt, QUrl, QSize
    from PyQt5.QtGui import QIcon, QKeySequence
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
        QListWidget, QFileDialog, QSlider, QAbstractItemView, QMessageBox, QLabel,
        QTabWidget, QLineEdit, QStatusBar, QMenuBar, QAction
    )
    from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
    from PyQt5.QtMultimediaWidgets import QVideoWidget
    USING_QT6 = False
    print("Using PyQt5")

# ---------------- Cross-version helpers ----------------
def align_center():
    return Qt.AlignmentFlag.AlignCenter if USING_QT6 else Qt.AlignCenter

def key(name: str):
    return getattr(Qt.Key, name) if USING_QT6 else getattr(Qt, name)

def file_dialog_options(use_native: bool = False):
    if USING_QT6:
        opt = QtWidgets.QFileDialog.Option(0)
        if not use_native:
            opt |= QtWidgets.QFileDialog.Option.DontUseNativeDialog
        return opt
    else:
        opt = QFileDialog.Options()
        if not use_native:
            opt |= QFileDialog.DontUseNativeDialog
        return opt

def _is_wayland() -> bool:
    try:
        plat = QtWidgets.QApplication.platformName()
    except Exception:
        plat = ""
    return (os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland") or ("wayland" in plat.lower())

def _safe_bring_to_front(w):
    """Show/raise without Wayland warnings."""
    if not w:
        return
    try:
        w.show()
        if not _is_wayland():
            if hasattr(w, "raise_"):
                w.raise_()
            if hasattr(w, "activateWindow"):
                w.activateWindow()
    except Exception:
        pass

# ---------------- Animated button (simple hover) ----------------
class AnimatedButton(QtWidgets.QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._default = """
            QPushButton {
                color: #e5e9ec;
                background-color: #2e3a41;
                border: 1px solid #3b474e;
                border-radius: 10px;
                padding: 10px 14px;
                min-width: 88px;
                font-weight: 600;
            }
        """
        self._hover = """
            QPushButton {
                color: #ffffff;
                background-color: #3b474e;
                border: 1px solid #4d5960;
                border-radius: 10px;
                padding: 10px 14px;
                min-width: 88px;
                font-weight: 600;
            }
        """
        self.setStyleSheet(self._default)

    def enterEvent(self, e):
        self.setStyleSheet(self._hover)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self.setStyleSheet(self._default)
        super().leaveEvent(e)

# ---------------- Main Window ----------------
class MainWindow(QMainWindow):
    SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mkv", ".mov", ".wmv"}
    SUPPORTED_AUDIO_EXTENSIONS = {".mp3", ".ogg", ".flac", ".wav"}

    def __init__(self):
        super().__init__()

        # Window
        self.setWindowTitle("Albix Player")
        self.setGeometry(100, 100, 1000, 700)
        self.setAcceptDrops(True)

        # Playlist & state
        self.playlist = []
        self.current_song_index = -1
        self.current_radio = None
        self.shuffle_mode = False
        self.repeat_mode = False
        self.current_media_type = 'audio'
        self._lyrics_visible = False

        # Track-end watchdog
        self._duration_ms = 0
        self._end_guard = False

        # Radio stations
        self.radio_stations = {
            "Triple J (Australia)": "https://live-radio01.mediahubaustralia.com/2TJW/mp3/",
            "Radio Paradise (USA)": "https://stream.radioparadise.com/mp3-192",
            "FIP (France)": "https://icecast.radiofrance.fr/fip-midfi.mp3",
            "SomaFM: Indie Pop Rocks (USA)": "https://ice2.somafm.com/indiepop-128-mp3",
            "Radio Nova (France)": "https://novazz.ice.infomaniak.ch/novazz-128.mp3",
            "181.fm The Rock! (USA)": "https://listen.181fm.com/181-rock_128k.mp3",
            "Big R Radio: Top 40 Hits (USA)": "https://bigrradio.cdnstream1.com/5104_128",
            "Yle Radio Suomi(FI)":"https://icecast.live.yle.fi/radio/YleRS/icecast.audio",
            "YleX(FI)":"https://icecast.live.yle.fi/radio/YleX/icecast.audio",
            "Yle Vega(FI)":"https://icecast.live.yle.fi/radio/YleVega/icecast.audio",
            "Yle Klassinen(FI)":"https://icecast.live.yle.fi/radio/YleKlassinen/icecast.audio",
            "Järviradio(FI)":"https://jarviradio.radiotaajuus.fi:9000/jr",
        }

        # Multimedia setup
        if USING_QT6:
            self.player = QMediaPlayer(self)
            self.audio_out = QAudioOutput(self)
            self.player.setAudioOutput(self.audio_out)
            self.player.playbackStateChanged.connect(self._on_playback_state_changed)
            self.player.positionChanged.connect(self.update_slider)
            self.player.durationChanged.connect(self.set_duration)
            self.player.mediaStatusChanged.connect(self.handle_media_status)
            self.player.errorOccurred.connect(self.handle_error)
        else:
            self.player = QMediaPlayer(self)
            self.player.stateChanged.connect(self._on_state_changed)
            self.player.positionChanged.connect(self.update_slider)
            self.player.durationChanged.connect(self.set_duration)
            self.player.mediaStatusChanged.connect(self.handle_media_status)
            self.player.error.connect(self.handle_error)

        # UI
        self._apply_dark_theme()
        self._build_ui()

        # ---- Lyrics integration (show/hide only) ----
        try:
            self.lyrics = albix_lyrics.AlbixLyrics(self, video_widget=self.video_widget)
        except Exception as e:
            self.lyrics = None
            QMessageBox.warning(self, "Lyrics",
                                f"Failed to initialize Albix Lyrics module:\n{e}")

        # Initialize volume to slider value
        self.change_volume(self.volume_slider.value())

    # ---------------- Drag & Drop ----------------
    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        if event.mimeData().hasUrls():
            paths = [url.toLocalFile() for url in event.mimeData().urls()]
            self._process_dropped_files(paths)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    def _process_dropped_files(self, files):
        for file_path in files:
            ext = splitext(file_path)[1].lower()
            if ext in self.SUPPORTED_VIDEO_EXTENSIONS:
                mtype = "video"
            elif ext in self.SUPPORTED_AUDIO_EXTENSIONS:
                mtype = "audio"
            else:
                continue
            if not os.path.exists(file_path):
                continue
            if any(it["path"] == file_path for it in self.playlist):
                continue
            self.playlist.append({"path": file_path, "type": mtype})
            self.playlist_widget.addItem(basename(file_path))
        self._update_controls_enabled()

    # ---------------- UI build ----------------
    def _build_ui(self):
        central = QWidget(self)
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Video widget
        self.video_widget = QVideoWidget(self)
        self.video_widget.setObjectName("video_widget")
        self.video_widget.setMinimumSize(640, 360)
        self.video_widget.hide()
        main_layout.addWidget(self.video_widget)

        # Connect player to video widget
        self.player.setVideoOutput(self.video_widget)

        # Tabs
        self.tab_widget = QTabWidget(self)
        self.tab_widget.setTabPosition(QTabWidget.TabPosition.North if USING_QT6 else QTabWidget.North)
        self.tab_widget.setTabShape(QTabWidget.TabShape.Rounded if USING_QT6 else QTabWidget.Rounded)
        self.tab_widget.setStyleSheet("""
            QTabBar::tab {
                background: #1a262d;
                color: #b9c2c8;
                border: 1px solid #26333a;
                padding: 8px 16px;
                margin-right: 6px;
                border-top-left-radius: 10px;
                border-top-right-radius: 10px;
                min-width: 110px;
            }
            QTabBar::tab:selected {
                background: #212c34;
                color: #e5e9ec;
                border-color: #3b474e;
            }
            QTabBar::tab:hover:!selected {
                background: #1f2b32;
            }
        """)

        self.music_tab = QWidget(self)
        self.radio_tab = QWidget(self)

        self.tab_widget.addTab(self.music_tab, "Local Files")
        self.tab_widget.addTab(self.radio_tab, "Radio Stations")

        self._setup_music_tab()
        self._setup_radio_tab()

        main_layout.addWidget(self.tab_widget)

        # Slider + time
        s_layout = QHBoxLayout()
        s_layout.setAlignment(align_center())

        self.current_time_label = QLabel("00:00")
        s_layout.addWidget(self.current_time_label)

        self.playback_slider = QSlider(Qt.Orientation.Horizontal if USING_QT6 else Qt.Horizontal)
        self.playback_slider.setRange(0, 0)
        self.playback_slider.sliderMoved.connect(self.seek_position)
        self.playback_slider.setEnabled(False)
        s_layout.addWidget(self.playback_slider)

        self.total_time_label = QLabel("00:00")
        s_layout.addWidget(self.total_time_label)

        main_layout.addLayout(s_layout)

        # Volume + mute
        v_layout = QHBoxLayout()
        v_layout.setAlignment(align_center())

        self.mute_button = AnimatedButton("Mute")
        self.mute_button.setCheckable(True)
        self.mute_button.clicked.connect(self.toggle_mute)
        v_layout.addWidget(self.mute_button)

        self.volume_label = QLabel("Volume:")
        v_layout.addWidget(self.volume_label)

        self.volume_slider = QSlider(Qt.Orientation.Horizontal if USING_QT6 else Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setFixedWidth(150)
        self.volume_slider.valueChanged.connect(self.change_volume)
        v_layout.addWidget(self.volume_slider)

        main_layout.addLayout(v_layout)

        # Status bar
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

        # File menu (kept), NO View menu
        menubar = self.menuBar()
        file_menu = menubar.addMenu("File")

        save_action = QAction("Save Playlist", self)
        save_action.triggered.connect(self.save_playlist)
        file_menu.addAction(save_action)

        load_action = QAction("Load Playlist", self)
        load_action.triggered.connect(self.load_playlist)
        file_menu.addAction(load_action)

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        self._update_controls_enabled()

    def _setup_music_tab(self):
        layout = QVBoxLayout(self.music_tab)

        # Row 1: transport
        row1 = QHBoxLayout()
        row1.setSpacing(10)

        self.prev_button = AnimatedButton("Prev")
        self.prev_button.setObjectName("prev_button")
        self.prev_button.clicked.connect(self.prev_song)
        self.prev_button.setEnabled(False)
        row1.addWidget(self.prev_button)

        self.play_button = AnimatedButton("Play")
        self.play_button.setObjectName("play_button")
        self.play_button.clicked.connect(self.play_pause_song)
        self.play_button.setEnabled(False)
        row1.addWidget(self.play_button)

        self.next_button = AnimatedButton("Next")
        self.next_button.setObjectName("next_button")
        self.next_button.clicked.connect(self.next_song)
        self.next_button.setEnabled(False)
        row1.addWidget(self.next_button)

        self.stop_button = AnimatedButton("Stop")
        self.stop_button.clicked.connect(self.stop_song)
        self.stop_button.setEnabled(False)
        row1.addWidget(self.stop_button)

        layout.addLayout(row1)

        # Row 2: library & modes
        row2 = QHBoxLayout()
        row2.setSpacing(10)

        self.add_button = AnimatedButton("Add")
        self.add_button.clicked.connect(self.add_songs)
        row2.addWidget(self.add_button)

        self.remove_button = AnimatedButton("Remove")
        self.remove_button.clicked.connect(self.remove_songs)
        self.remove_button.setEnabled(False)
        row2.addWidget(self.remove_button)

        self.shuffle_button = AnimatedButton("Shuffle OFF")
        self.shuffle_button.setCheckable(True)
        self.shuffle_button.clicked.connect(self.toggle_shuffle)
        self.shuffle_button.setEnabled(False)
        row2.addWidget(self.shuffle_button)

        self.repeat_button = AnimatedButton("Repeat OFF")
        self.repeat_button.setCheckable(True)
        self.repeat_button.clicked.connect(self.toggle_repeat)
        self.repeat_button.setEnabled(False)
        row2.addWidget(self.repeat_button)

        self.lyrics_button = AnimatedButton("Lyrics")
        self.lyrics_button.setCheckable(True)
        self.lyrics_button.clicked.connect(self.toggle_lyrics)
        row2.addWidget(self.lyrics_button)

        layout.addLayout(row2)

        # Playlist
        self.playlist_widget = QListWidget(self.music_tab)
        sel_mode = QAbstractItemView.SelectionMode.ExtendedSelection if USING_QT6 else QAbstractItemView.ExtendedSelection
        self.playlist_widget.setSelectionMode(sel_mode)
        self.playlist_widget.itemDoubleClicked.connect(self.play_selected_song)
        self.playlist_widget.setStyleSheet("""
            QListWidget::item {
                padding: 10px;
                font-size: 12px;
            }
        """)
        layout.addWidget(self.playlist_widget)

    def _setup_radio_tab(self):
        layout = QVBoxLayout(self.radio_tab)

        self.radio_list_widget = QListWidget(self.radio_tab)
        sel_mode = QAbstractItemView.SelectionMode.SingleSelection if USING_QT6 else QAbstractItemView.SingleSelection
        self.radio_list_widget.setSelectionMode(sel_mode)
        self.radio_list_widget.itemDoubleClicked.connect(self.play_radio_station)
        self.radio_list_widget.setStyleSheet("""
            QListWidget::item {
                padding: 10px;
                font-size: 12px;
            }
        """)
        for station in self.radio_stations.keys():
            self.radio_list_widget.addItem(station)
        layout.addWidget(self.radio_list_widget)

        # Custom station row
        row = QHBoxLayout()
        self.custom_station_name = QLineEdit(self.radio_tab)
        self.custom_station_name.setPlaceholderText("Station Name")
        self.custom_station_url = QLineEdit(self.radio_tab)
        self.custom_station_url.setPlaceholderText("Stream URL")
        add_station = AnimatedButton("Add Station")
        add_station.clicked.connect(self.add_custom_station)

        row.addWidget(self.custom_station_name)
        row.addWidget(self.custom_station_url)
        row.addWidget(add_station)
        layout.addLayout(row)

    # ---------------- Theme ----------------
    def _apply_dark_theme(self):
        self.setStyleSheet("""
            QMainWindow {
                color: #e5e9ec;
                background-color: #111e25;
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                font-size: 12px;
            }
            QPushButton {
                color: #e5e9ec;
                background-color: #2e3a41;
                border: 1px solid #3b474e;
                border-radius: 10px;
                padding: 10px 14px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #3b474e; border-color: #4d5960; }
            QPushButton:pressed { background-color: #212c34; border-color: #4d5960; }
            QPushButton:disabled { color: #7d8a92; background-color: #1a262d; border-color: #26333a; }
            QPushButton:focus { outline: none; border: 1px solid #7f8c94; }

            QListWidget {
                color: #e5e9ec; background-color: #212c34;
                border: 1px solid #3b474e; border-radius: 10px; padding: 6px;
                selection-background-color: #3b474e; selection-color: #ffffff;
            }
            QListWidget::item { padding: 10px; border-radius: 8px; }
            QListWidget::item:hover:!selected { background: #1a262d; }
            QListWidget::item:selected { background: #3b474e; color: #ffffff; }

            QLabel { color: #b9c2c8; font-size: 11px; }

            QSlider::groove:horizontal { border: 1px solid #26333a; height: 8px; background: #1a262d; border-radius: 4px; margin: 0 2px; }
            QSlider::sub-page:horizontal { background: #4d5960; border: 1px solid #3b474e; border-radius: 4px; }
            QSlider::add-page:horizontal { background: #171f25; border: 1px solid #26333a; border-radius: 4px; }
            QSlider::handle:horizontal { background: #2e3a41; border: 1px solid #4d5960; width: 16px; margin: -5px 0; border-radius: 8px; }
            QSlider::handle:horizontal:hover { border-color: #7f8c94; }

            QLineEdit { background: #1a262d; color: #e5e9ec; border: 1px solid #3b474e; border-radius: 10px; padding: 8px 10px;
                        selection-background-color: #3b474e; selection-color: #ffffff; }
            QLineEdit:focus { border: 1px solid #7f8c94; background: #1d2a31; }

            QMenuBar { background-color: #111e25; color: #e5e9ec; border-bottom: 1px solid #26333a; }
            QMenuBar::item { padding: 6px 10px; background: transparent; border-radius: 6px; }
            QMenuBar::item:selected { background-color: #1a262d; }

            QMenu { background: #1a262d; color: #e5e9ec; border: 1px solid #26333a; padding: 6px; border-radius: 10px; }
            QMenu::item { padding: 6px 10px; border-radius: 6px; }
            QMenu::item:selected { background: #2e3a41; }

            QTabWidget::pane { border: 1px solid #26333a; border-radius: 10px; background: #171f25; padding: 6px; }

            QVideoWidget, QWidget#video_widget { background-color: #000000; border: 1px solid #26333a; border-radius: 10px; }

            QStatusBar { background: #111e25; color: #8fa0a9; border-top: 1px solid #26333a; }

            QScrollBar:vertical { background: transparent; width: 12px; margin: 4px 0; }
            QScrollBar::handle:vertical { background: #2e3a41; min-height: 28px; border-radius: 6px; }
            QScrollBar::handle:vertical:hover { background: #3b474e; }
            QScrollBar:horizontal { background: transparent; height: 12px; margin: 0 4px; }
            QScrollBar::handle:horizontal { background: #2e3a41; min-width: 28px; border-radius: 6px; }
            QScrollBar::handle:horizontal:hover { background: #3b474e; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

            QToolTip { color: #e5e9ec; background: #1a262d; border: 1px solid #3b474e; border-radius: 8px; padding: 6px 8px; }
        """)

    # ---------------- Menu actions ----------------
    def save_playlist(self):
        if not self.playlist:
            QMessageBox.information(self, "Empty Playlist", "There is no playlist to save.")
            return
        opts = file_dialog_options(False)
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Playlist", "", "JSON Files (*.json)", options=opts)
        if file_name:
            try:
                with open(file_name, 'w', encoding='utf-8') as f:
                    json.dump(self.playlist, f, indent=4)
                QMessageBox.information(self, "Playlist Saved", f"Playlist saved to {file_name}")
            except Exception as e:
                QMessageBox.critical(self, "Error Saving Playlist", str(e))

    def load_playlist(self):
        opts = file_dialog_options(False)
        file_name, _ = QFileDialog.getOpenFileName(self, "Load Playlist", "", "JSON Files (*.*)", options=opts)
        if file_name:
            try:
                with open(file_name, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if isinstance(data, list) and all('path' in d and 'type' in d for d in data):
                    self.playlist = data
                    self.playlist_widget.clear()
                    for item in self.playlist:
                        self.playlist_widget.addItem(basename(item['path']))
                    self._update_controls_enabled()
                    QMessageBox.information(self, "Playlist Loaded", f"Playlist loaded from {file_name}")
                else:
                    QMessageBox.warning(self, "Invalid File", "The selected JSON does not contain a valid playlist.")
            except Exception as e:
                QMessageBox.critical(self, "Error Loading Playlist", str(e))

    # ---------------- Music tab actions ----------------
    def add_songs(self):
        opts = file_dialog_options(False)
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Add Media Files",
            "",
            "Media Files (*.mp3 *.ogg *.flac *.wav *.mp4 *.avi *.mkv *.mov *.wmv);;All Files (*)",
            options=opts
        )
        if not files:
            return
        for file_path in files:
            if any(it["path"] == file_path for it in self.playlist):
                continue
            ext = splitext(file_path)[1].lower()
            if ext in self.SUPPORTED_VIDEO_EXTENSIONS:
                mtype = "video"
            elif ext in self.SUPPORTED_AUDIO_EXTENSIONS:
                mtype = "audio"
            else:
                QMessageBox.warning(self, "Unsupported Format", f"Skipping:\n{basename(file_path)}")
                continue
            if not os.path.exists(file_path):
                QMessageBox.warning(self, "File Not Found", f"The file does not exist:\n{basename(file_path)}")
                continue
            self.playlist.append({"path": file_path, "type": mtype})
            self.playlist_widget.addItem(basename(file_path))
        self._update_controls_enabled()

    def remove_songs(self):
        selected = self.playlist_widget.selectedItems()
        if not selected:
            return
        for item in selected:
            idx = self.playlist_widget.row(item)
            if 0 <= idx < len(self.playlist):
                self.playlist.pop(idx)
                self.playlist_widget.takeItem(idx)
                if idx == self.current_song_index:
                    self.stop_song()
        if self.current_song_index >= len(self.playlist):
            self.current_song_index = len(self.playlist) - 1
        self._update_controls_enabled()

    def play_selected_song(self):
        self.current_song_index = self.playlist_widget.currentRow()
        self.current_radio = None
        self.play_song()

    # ---------------- Playback control ----------------
    def play_pause_song(self):
        if USING_QT6:
            from PyQt6.QtMultimedia import QMediaPlayer as QMP
            state = self.player.playbackState()
            if state == QMP.PlaybackState.PlayingState:
                self.player.pause()
            elif state == QMP.PlaybackState.PausedState:
                self.player.play()
            else:
                if self.current_song_index == -1 and self.playlist:
                    self.current_song_index = 0
                    self.playlist_widget.setCurrentRow(self.current_song_index)
                elif self.current_radio is not None:
                    self.play_radio_station_by_name(self.current_radio)
                self.play_song()
        else:
            state = self.player.state()
            if state == QMediaPlayer.State.PlayingState:
                self.player.pause()
            elif state == QMediaPlayer.State.PausedState:
                self.player.play()
            else:
                if self.current_song_index == -1 and self.playlist:
                    self.current_song_index = 0
                    self.playlist_widget.setCurrentRow(self.current_song_index)
                elif self.current_radio is not None:
                    self.play_radio_station_by_name(self.current_radio)
                self.play_song()

    def play_song(self):
        if not (0 <= self.current_song_index < len(self.playlist)):
            return
        media_info = self.playlist[self.current_song_index]
        file_path = media_info["path"]
        mtype = media_info["type"]
        self.current_media_type = mtype

        if not os.path.exists(file_path):
            QMessageBox.warning(self, "File Not Found", f"The file was not found:\n{basename(file_path)}")
            return

        if mtype == "video":
            self.video_widget.show()
        else:
            self.video_widget.hide()

        if USING_QT6:
            self.player.setSource(QUrl.fromLocalFile(file_path))
        else:
            self.player.setMedia(QMediaContent(QUrl.fromLocalFile(file_path)))

        # reset end-guard for a new track
        self._end_guard = False

        self.player.play()
        self.playback_slider.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.status_bar.showMessage(f"Playing: {basename(file_path)}")

        # Inform lyrics module of current media
        self._lyrics_call("set_media", file_path)

    def play_radio_station(self, item):
        station_name = item.text()
        self.current_radio = station_name
        self.current_song_index = -1
        self.play_radio_station_by_name(station_name)

    def play_radio_station_by_name(self, station_name: str):
        if station_name not in self.radio_stations:
            QMessageBox.warning(self, "Station Not Found", f"No such station:\n{station_name}")
            return
        stream_url = self.radio_stations[station_name]
        self.video_widget.hide()
        if USING_QT6:
            self.player.setSource(QUrl(stream_url))
        else:
            self.player.setMedia(QMediaContent(QUrl(stream_url)))
        self.player.play()
        self.playback_slider.setEnabled(True)
        self.stop_button.setEnabled(True)
        self.status_bar.showMessage(f"Streaming Radio: {station_name}")
        self._lyrics_call("clear")

    def stop_song(self):
        self.player.stop()
        self.playback_slider.setValue(0)
        self.playback_slider.setEnabled(False)
        self.stop_button.setEnabled(False)
        self._set_play_button_text("Play")
        self.current_time_label.setText("00:00")
        self.status_bar.showMessage("Playback stopped.")
        self.current_radio = None
        self.video_widget.hide()
        self._lyrics_call("clear")
        # prevent watchdog from firing after manual stop
        self._end_guard = True

    def next_song(self):
        if not self.playlist:
            return
        self.current_radio = None
        if self.shuffle_mode and len(self.playlist) > 1:
            choices = list(range(len(self.playlist)))
            if 0 <= self.current_song_index < len(self.playlist):
                choices.pop(self.current_song_index)
            self.current_song_index = random.choice(choices)
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
        if not self.playlist:
            return
        self.current_radio = None
        if self.shuffle_mode and len(self.playlist) > 1:
            choices = list(range(len(self.playlist)))
            if 0 <= self.current_song_index < len(self.playlist):
                choices.pop(self.current_song_index)
            self.current_song_index = random.choice(choices)
        else:
            if (self.current_song_index - 1) >= 0:
                self.current_song_index -= 1
            else:
                self.status_bar.showMessage("Start of playlist.")
                self.current_song_index = 0
        self.playlist_widget.setCurrentRow(self.current_song_index)
        self.play_song()

    def toggle_shuffle(self):
        self.shuffle_mode = not self.shuffle_mode
        self.shuffle_button.setText("Shuffle ON" if self.shuffle_mode else "Shuffle OFF")
        self.status_bar.showMessage(f"Shuffle Mode: {'ON' if self.shuffle_mode else 'OFF'}")

    def toggle_repeat(self):
        self.repeat_mode = not self.repeat_mode
        self.repeat_button.setText("Repeat ON" if self.repeat_mode else "Repeat OFF")
        self.status_bar.showMessage(f"Repeat Mode: {'ON (Current Track)' if self.repeat_mode else 'OFF'}")

    # ---------------- Volume / Mute ----------------
    def change_volume(self, value: int):
        if USING_QT6:
            self.audio_out.setVolume(max(0.0, min(1.0, value / 100.0)))
        else:
            self.player.setVolume(value)
        self.status_bar.showMessage(f"Volume: {value}%")

    def toggle_mute(self):
        if USING_QT6:
            self.audio_out.setMuted(self.mute_button.isChecked())
        else:
            self.player.setMuted(self.mute_button.isChecked())
        self.status_bar.showMessage("Muted" if self.mute_button.isChecked() else f"Volume: {self.volume_slider.value()}%")

    # ---------------- Slider / time ----------------
    def update_slider(self, position_ms: int):
        self.playback_slider.blockSignals(True)
        self.playback_slider.setValue(position_ms)
        self.playback_slider.blockSignals(False)
        self.current_time_label.setText(self._millis_to_time(position_ms))
        self._lyrics_call("update_position", int(position_ms))

        # Watchdog: if we're within 1s of the end and not advanced yet, advance once.
        if self.current_radio is None and self._duration_ms > 0:
            if position_ms >= max(0, self._duration_ms - 1000) and not self._end_guard:
                self._end_guard = True
                QtCore.QTimer.singleShot(50, self._advance_after_end)

    def set_duration(self, duration_ms: int):
        self._duration_ms = max(0, int(duration_ms))
        self.playback_slider.setRange(0, self._duration_ms)
        self.total_time_label.setText(self._millis_to_time(self._duration_ms))
        self._end_guard = False

    def seek_position(self, position_ms: int):
        self.player.setPosition(position_ms)
        self.current_time_label.setText(self._millis_to_time(position_ms))
        self.status_bar.showMessage(f"Seeked to: {self._millis_to_time(position_ms)}")
        self._lyrics_call("update_position", int(position_ms))

    # ---------------- Media status / errors ----------------
    def handle_media_status(self, status):
        name = getattr(status, 'name', str(status))
        if 'EndOfMedia' in name:
            self._advance_after_end()
        if 'LoadedMedia' in name or 'BufferedMedia' in name:
            self._end_guard = False

    def _advance_after_end(self):
        if self.current_radio is not None:
            return
        if self.repeat_mode:
            self.player.setPosition(0)
            self.player.play()
            self._end_guard = False
        else:
            self.next_song()

    def handle_error(self, *args):
        err = ""
        try:
            err = self.player.errorString()
        except Exception:
            err = "Playback error."
        if err:
            QMessageBox.critical(self, "Playback Error", f"An error occurred:\n\n{err}")
            self.stop_song()

    # ---------------- Key handling ----------------
    def keyPressEvent(self, event):
        if event.key() == key('Key_F11'):
            if self.isFullScreen():
                self.showNormal()
                self._show_normal_ui()
            else:
                self.showFullScreen()
                self._hide_ui_for_fullscreen()
        elif event.key() == key('Key_Escape') and self.isFullScreen():
            self.showNormal()
            self._show_normal_ui()
        elif event.key() == key('Key_P'):
            self.play_pause_song()
        elif event.key() == key('Key_L') and (event.modifiers() & (Qt.KeyboardModifier.ControlModifier if USING_QT6 else Qt.ControlModifier)):
            self.toggle_lyrics()
        else:
            super().keyPressEvent(event)

    def _hide_ui_for_fullscreen(self):
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
        self.lyrics_button.hide()

    def _show_normal_ui(self):
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
        self.lyrics_button.show()

    # ---------------- Helpers ----------------
    def _update_controls_enabled(self):
        enabled = bool(self.playlist)
        for w in (self.play_button, self.remove_button, self.prev_button,
                  self.next_button, self.shuffle_button, self.repeat_button):
            w.setEnabled(enabled)

    def _set_play_button_text(self, txt: str):
        self.play_button.setText(txt)

    def _millis_to_time(self, millis: int) -> str:
        s = max(0, millis // 1000)
        m = s // 60
        s = s % 60
        return f"{m:02}:{s:02}"

    # ---------------- Lyrics control (toggle via button) ----------------
    def toggle_lyrics(self):
        if not getattr(self, "lyrics", None):
            return
        try:
            visible_now = bool(self.lyrics.isVisible())
        except Exception:
            visible_now = bool(getattr(self, "_lyrics_visible", False))
        if visible_now:
            self.hide_lyrics()
        else:
            self.show_lyrics()

    def show_lyrics(self):
        if not getattr(self, "lyrics", None):
            return
        try:
            self.lyrics.show_panel()
            self._lyrics_visible = True
            if hasattr(self, "lyrics_button"):
                self.lyrics_button.setChecked(True)
                self.lyrics_button.setText("Hide Lyrics")
            # ensure enough width for the dock
            if self.width() < 1200:
                self.resize(1200, self.height())
            _safe_bring_to_front(self)
        except Exception:
            pass

    def hide_lyrics(self):
        if not getattr(self, "lyrics", None):
            return
        try:
            self.lyrics.hide_panel()
            self._lyrics_visible = False
            if hasattr(self, "lyrics_button"):
                self.lyrics_button.setChecked(False)
                self.lyrics_button.setText("Lyrics")
        except Exception:
            pass

    def _lyrics_call(self, name: str, *args):
        """Call an optional lyrics API; ignore errors."""
        if not getattr(self, "lyrics", None):
            return
        fn = getattr(self.lyrics, name, None)
        if callable(fn):
            try:
                fn(*args)
            except Exception as e:
                print(f"lyrics.{name} error:", e)

    # ---------------- Custom stations ----------------
    def add_custom_station(self):
        name = self.custom_station_name.text().strip()
        url = self.custom_station_url.text().strip()
        if not name or not url:
            QMessageBox.warning(self, "Invalid Input", "Station name and URL cannot be empty.")
            return
        self.radio_stations[name] = url
        self.radio_list_widget.addItem(name)
        self.custom_station_name.clear()
        self.custom_station_url.clear()

    # ---------------- State change adapters ----------------
    def _on_playback_state_changed(self, state):
        from PyQt6.QtMultimedia import QMediaPlayer as QMP
        self._set_play_button_text("Pause" if state == QMP.PlaybackState.PlayingState else "Play")
        self._lyrics_call("set_playing", state == QMP.PlaybackState.PlayingState)

    def _on_state_changed(self, state):
        self._set_play_button_text("Pause" if state == QMediaPlayer.State.PlayingState else "Play")
        self._lyrics_call("set_playing", state == QMediaPlayer.State.PlayingState)

# ---------------- Main ----------------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec() if USING_QT6 else app.exec_())

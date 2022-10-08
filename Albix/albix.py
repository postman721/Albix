#Albix 3.5 Copyright (c) 2017 JJ Posti <techtimejourney.net> 
#This program comes with ABSOLUTELY NO WARRANTY;  #for details see: http://www.gnu.org/copyleft/gpl.html. 
#This is free software, and you are welcome to redistribute it under  #GPL Version 2, June 1991")
#!/usr/bin/env python3

#Pygame from pip enables mp3 support. We are using that instead of default Debian package.

#Dependencies: sudo apt install python3-pyqt5 python3-mutagen && sudo apt install python3-pip && pip3 install pygame

from PyQt5 import QtCore, QtGui, QtWidgets 
from PyQt5.QtCore import *  
from PyQt5.QtGui import *  
from PyQt5.QtWidgets import *
import subprocess, os, sys, pygame
from os.path import basename
from mutagen.mp3 import MP3
import mutagen
import datetime
import time
try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s
try:
    _encoding = QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QApplication.translate(context, text, disambig)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName(_fromUtf8("MainWindow"))
        MainWindow.setStyleSheet("color:#ffffff; background-color:#474747; border: 2px solid #353535; border-radius: 3px;font-size: 12px;")
        MainWindow.resize(700, 350)
        MainWindow.setLayoutDirection(QtCore.Qt.LeftToRight)
        MainWindow.setToolButtonStyle(QtCore.Qt.ToolButtonIconOnly)
        MainWindow.setTabShape(QTabWidget.Triangular)
        MainWindow.setUnifiedTitleAndToolBarOnMac(False)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(_fromUtf8("centralwidget"))
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(_fromUtf8("verticalLayout"))
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(_fromUtf8("horizontalLayout"))
#Playlist
        self.playlist=[]
        
#Seconds navigator        
        self.horizontalSlider = QSlider(self.centralwidget)
        self.horizontalSlider.setOrientation(QtCore.Qt.Horizontal)
        self.horizontalSlider.setObjectName(_fromUtf8("horizontalSlider"))
        self.horizontalSlider.setTickPosition(QSlider.TicksBelow)
        self.horizontalSlider.setTickInterval(1)
        self.horizontalSlider.setRange(0, 100)
        self.horizontalSlider.setToolTip('Jump to position')        
        self.horizontalSlider.setFixedSize(250, 30)
        self.horizontalSlider.valueChanged[int].connect(self.position)        
                
#Add song        
        self.Add = QPushButton(self.centralwidget)
        self.Add.setText(_fromUtf8("Add song"))
        self.Add.setStyleSheet("QPushButton{color:#ffffff; background-color:#353535; border: 2px solid #353535; border-radius: 3px;font-size: 12px;}"
        "QPushButton:hover{background-color:#1b486a;}")  
        icon = QIcon()
        icon.addPixmap(QPixmap(_fromUtf8("add.png")), QIcon.Normal, QIcon.Off)
        self.Add.setIcon(icon)
        self.Add.setIconSize(QtCore.QSize(32, 32))
        self.Add.setObjectName(_fromUtf8("Add"))
        self.horizontalLayout.addWidget(self.Add)
        self.Add.clicked.connect(self.dialog)
#Play song        
        self.Play = QPushButton(self.centralwidget)
        self.Play.setText(_fromUtf8("Play"))
        self.Play.setStyleSheet("QPushButton{color:#ffffff; background-color:#353535; border: 2px solid #353535; border-radius: 3px;font-size: 12px;}"
        "QPushButton:hover{background-color:#1b486a;}")  
        icon1 = QIcon()
        icon1.addPixmap(QPixmap(_fromUtf8("play.png")), QIcon.Normal, QIcon.Off)
        self.Play.setIcon(icon1)
        self.Play.setIconSize(QtCore.QSize(32, 32))
        self.Play.setObjectName(_fromUtf8("Play"))
        self.horizontalLayout.addWidget(self.Play)
        self.Play.clicked.connect(self.play)
        self.Play.clicked.connect(self.play_button)
        self.Play.setEnabled(False)
        self.Play.clicked.connect(self.getme)        
#Remove Playlist items       
        self.Remove = QPushButton(self.centralwidget)
        self.Remove.setText(_fromUtf8("Remove"))
        self.Remove.setStyleSheet("QPushButton{color:#ffffff; background-color:#353535; border: 2px solid #353535; border-radius: 3px;font-size: 12px;}"
        "QPushButton:hover{background-color:#1b486a;}")  
        icon2 = QIcon()
        icon2.addPixmap(QPixmap(_fromUtf8("remove.png")), QIcon.Normal, QIcon.Off)
        self.Remove.setIcon(icon2)
        self.Remove.setIconSize(QtCore.QSize(32, 32))
        self.Remove.setObjectName(_fromUtf8("Remove item from playlist"))
        self.horizontalLayout.addWidget(self.Remove)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.Remove.clicked.connect(self.deleting)
        self.Remove.setEnabled(False)        
#Song Listing        
        self.listWidget = QListWidget(self.centralwidget)
        self.listWidget.setObjectName(_fromUtf8("listwidget"))
        self.listWidget.setStyleSheet("QListWidget{color:#ffffff; background-color:#1b1b1b; border: 2px solid #353535; border-radius: 3px;font-size: 12px;}"
        "QPushButton:hover{background-color:#1b486a;}")  
        self.verticalLayout.addWidget(self.listWidget)
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(_fromUtf8("horizontalLayout_2")) 
        self.listWidget.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
       
#Pause Song        
        self.Pause = QPushButton(self.centralwidget)
        self.Pause.setText(_fromUtf8("Toggle Pause"))
        self.Pause.setStyleSheet("QPushButton{color:#ffffff; background-color:#353535; border: 2px solid #353535; border-radius: 3px;font-size: 12px;}"
        "QPushButton:hover{background-color:#1b486a;}")  
        icon3 = QIcon()
        icon3.addPixmap(QPixmap(_fromUtf8("pause.png")), QIcon.Normal, QIcon.Off)
        self.Pause.setIcon(icon3)
        self.Pause.setIconSize(QtCore.QSize(32, 32))
        self.Pause.setObjectName(_fromUtf8("Pause"))
        self.Pause.clicked.connect(self.paused)
        self.Pause.clicked.connect(self.getme)
        self.horizontalLayout_2.addWidget(self.Pause)
                                      
#Stop Song        
        self.Stop = QPushButton(self.centralwidget)
        self.Stop.setText(_fromUtf8("Stop"))
        self.Stop.setStyleSheet("QPushButton{color:#ffffff; background-color:#353535; border: 2px solid #353535; border-radius: 3px;font-size: 12px;}"
        "QPushButton:hover{background-color:#1b486a;}")  
        icon6 = QIcon()
        icon6.addPixmap(QPixmap(_fromUtf8("stop.png")), QIcon.Normal, QIcon.Off)
        self.Stop.setIcon(icon6)
        self.Stop.setIconSize(QtCore.QSize(32, 32))
        self.Stop.setObjectName(_fromUtf8("Stop"))
        self.horizontalLayout_2.addWidget(self.Stop)
        self.verticalLayout.addLayout(self.horizontalLayout_2)
        self.Stop.clicked.connect(self.stop)
        self.Stop.setEnabled(True)        
#Placeholder variables
        self.Pause.setEnabled(True)
        self.Paused = False
        self.Stopped=False
        MainWindow.setCentralWidget(self.centralwidget)
#Statusbar        
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(_fromUtf8("statusbar"))
        self.statusbar.addPermanentWidget(self.horizontalSlider)
        MainWindow.setStatusBar(self.statusbar)
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

#Double-click list item - play it.
        self.listWidget.itemDoubleClicked.connect(self.play)
        self.listWidget.itemDoubleClicked.connect(self.getme)
        self.listWidget.itemDoubleClicked.connect(self.play_button)        

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(_translate("MainWindow", "Albix Player 3.5", None))
        self.Add.setToolTip(_translate("MainWindow", "Add to playlist", None))
        self.Play.setToolTip(_translate("MainWindow", "Play/Next song", None))
        self.Remove.setToolTip(_translate("MainWindow", "Remove item from playlist", None))
        self.Pause.setToolTip(_translate("MainWindow", "Pause playback", None))
        self.Stop.setToolTip(_translate("MainWindow", "Stop playback", None))
#Add files to playlist  
    def dialog(self):
        self.listWidget.clear()
        self.playlist.clear()
        self.stop()
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        path, _ = QFileDialog.getOpenFileNames(None,"Choose music files. Use files that are within the same directory.", "","All Files (*);;Mp3 Files (*.mp3) ;;Ogg Files (*.ogg)", options=options)
        if path:
            for x in path:
                dirs=os.path.dirname(x)
                os.chdir(os.path.dirname(x))
                print (dirs)
                bases=(os.path.basename(x))
                self.playlist.append(bases)
            self.listWidget.addItems(self.playlist)
            self.pathway=self.playlist
            self.numbers=len(self.playlist)
            print (self.numbers)
            self.Remove.setEnabled(True)
            self.Play.setEnabled(True)
            pygame.mixer.init()
            return self.pathway  

#Delete Files from playlist
    def deleting(self):
        for item in self.listWidget.selectedItems():
            self.listWidget.takeItem(self.listWidget.row(item))
        self.Play.setEnabled(True)   
#Play song(s)
    def play(self,item): 
        self.statusbar.showMessage('')
        xlist= len(self.pathway)        
        basic=(self.listWidget.currentRow())
        index = basic 
        pygame.mixer.init()
        pygame.mixer.music.load(self.playlist[index])
        song=(self.playlist[index])
        ax=os.path.basename(song)
        self.songs=song
        self.single=ax
        self.Stop.setEnabled(True)
        self.Pause.setEnabled(True)
               
        a = pygame.mixer.Sound(song)
        self.x=a.get_length()
        self.ls=int(self.x)
        self.marking=str(self.x)
        self.seconds_here=self.marking[0:3]
        pygame.mixer.music.play()
    
        return self.songs, self.single, self.ls, self.seconds_here
        
#Play button checks                
    def play_button(self):
        self.numbersx= len(self.pathway)
        if self.numbersx >= 1:
           self.Play.setEnabled(True)
           self.getme()
        elif self.numbersx == 0:
            try:
                self.Play.setEnabled(False)
                self.getme()
            except Exception as e:
                print ("Error.No next item.")
#Pause / Unpause
    def paused(self,widget):
        if self.Paused:
            try:
                pygame.mixer.music.unpause()
                self.Stop.setEnabled(True)
                self.Paused = False
            except Exception as e:
                print ("Nothing to pause.")
        else:
            try:
                pygame.mixer.music.pause()
                self.Stop.setEnabled(False)
                self.Paused = True
            except Exception as e:
                print ("Error while pausing.")
#Stop song
    def stop(self):
        if self.Stopped:
            try:
                self.statusbar.showMessage('')
            except Exception as e:
                print ("Error. Nothing to stop.")
        else:
            try:
                self.Stop.setEnabled(True)
                pygame.mixer.music.stop()
                pygame.mixer.quit()
                self.Play.setEnabled(True)
                self.Pause.setEnabled(False)
                self.statusbar.showMessage('Playlist stopped.' )        
            except Exception as e:
                print ("Error. Nothing to stop.")
                
#Jump to position    
    def position(self, value):
        x=self.horizontalSlider.value()
        try:
            if self.songs.endswith('.mp3'):			
                pros= self.song.info.length/100
                time=(x * pros)
                dur=str(datetime.timedelta(seconds=time))
                print(dur)
                pygame.mixer.music.play(0, time)            
        except Exception as e:
             print("Error. Not an mp3. Mutagen will not get duration.")
#Duration         
    def getme(self):
        try:
            if self.songs.endswith('.mp3'):			
                self.song = MP3(self.songs) 
                self.seconds= int(self.song.info.length)
                self.total=str(datetime.timedelta(seconds=self.seconds))
                print (self.total)
                self.statusbar.showMessage('Playing: ' + self.single + '  ' + self.total)
                self.horizontalSlider.setEnabled(True) 
            else:
                self.statusbar.showMessage('Playing: ' + self.single + '   ' + '(Slider enabled for mp3).')
                self.horizontalSlider.setEnabled(False)                 							        
        except Exception as e:
            print("Error. Mutagen will not get duration.")
						                                
if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    MainWindow = QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

#!/usr/bin/python
# -*- coding: utf-8 -*-

import subprocess, sys
from PyQt4 import QtGui, QtCore


PROGRAM_NAME = "getLyrics editor"

class infoLabel(QtGui.QLabel):

    def __init__(self, *args):
        super(infoLabel, self).__init__(*args)
        self.setOpenExternalLinks(False)
        self.linkActivated.connect(self.googleSearch)

        
    def googleSearch(self, url):
        url = unicode(url.toUtf8(), sys.getfilesystemencoding())
        subprocess.Popen(["kioclient", "exec", url], stdout = open('/dev/null', 'w'), stderr = subprocess.STDOUT)


class lyricsEditor(QtGui.QWidget):

    textChanged = False

    def __init__(self, lyrics, info):
        super(lyricsEditor, self).__init__()


        self.initUI(lyrics, info)


    def initUI(self, lyrics = "", info = ""):
        self.hlButtons = QtGui.QHBoxLayout()
        self.hlButtons.addStretch()

        if info != "":
            url = " ".join(info.split())
            url = "http://www.google.com/search?q=%s&ie=UTF-8&oe=UTF-8" % info.replace('"', "%22").replace("'", "%27").replace("&", "%26").replace("?", "%3F")
            info = "<a href=\'%s\'>%s</a>" % (url, info)
            self.lblInfo = infoLabel(info, self)
            self.lblInfo.setTextInteractionFlags(QtCore.Qt.TextBrowserInteraction)
        
        self.btnSave = QtGui.QPushButton("&Save", self)
        self.btnSave.setEnabled(False)
        self.btnSave.clicked.connect(self.saveFile)
        self.btnSave.resize(self.btnSave.sizeHint())
        self.hlButtons.addWidget(self.btnSave)

        self.btnQuit = QtGui.QPushButton('&Quit', self)
        self.btnQuit.clicked.connect(self.close)
        self.btnQuit.resize(self.btnQuit.sizeHint())
        self.btnQuit.setAutoDefault(True)
        self.hlButtons.addWidget(self.btnQuit)

        self.tdText = QtGui.QTextEdit(self)
        self.tdText.setAcceptRichText(False)
        self.tdText.setPlainText(lyrics)
        self.tdText.textChanged.connect(self.textChangedSlot)
        
        self.mainLayout = QtGui.QVBoxLayout(self)
        self.setLayout(self.mainLayout)
        if info != "":
            self.mainLayout.addWidget(self.lblInfo)
            
        self.mainLayout.addWidget(self.tdText)
        self.mainLayout.addLayout(self.hlButtons)

        #self.sizeHint = QtCore.QSize(500, 600)
        self.resize(500, 600)
        #self.setGeometry(300, 300, 250, 150)
        
        self.setWindowTitle(PROGRAM_NAME)
        self.show()


    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()


    def textChangedSlot(self):
        self.textChanged = True
        self.btnSave.setEnabled(True)

        
    def closeEvent(self, event):
        if self.textChanged:
            reply = QtGui.QMessageBox.question(self, PROGRAM_NAME + ' - Message',
                "Your are about to loose all your changes.\n\nAre you sure to quit?", QtGui.QMessageBox.Yes |
                QtGui.QMessageBox.No, QtGui.QMessageBox.No)

            if reply == QtGui.QMessageBox.Yes:
                event.accept()
            else:
                event.ignore()

        else:
            event.accept()

            
    def saveFile(self, event):
        print self.tdText.toPlainText().toUtf8()
        self.textChanged = False
        self.close()
            

def main():
    lyrics = info = ""
    try:
        lyrics = unicode(sys.argv[1].strip(), sys.getfilesystemencoding())

    except:
        pass

    try:
        info = unicode(sys.argv[2].strip(), sys.getfilesystemencoding())

    except:
        pass

    app = QtGui.QApplication(sys.argv)

    ex = lyricsEditor(lyrics, info)
    sys.exit(app.exec_())


if __name__ == '__main__':
    main() 

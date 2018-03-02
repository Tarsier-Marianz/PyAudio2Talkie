import sys
import os
import re
import binascii
import time
from threading import Thread
from PyQt5.QtCore import QFile, QFileInfo, QSettings, Qt, QTextStream, QTimer, QThread, pyqtSignal
from PyQt5.QtWidgets import QMainWindow, QTextEdit, QAction, QApplication, QMessageBox, QFileDialog
from PyQt5.QtGui import QIcon, QFont
import webbrowser
try:
    import configparser
except:
    from six.moves import configparser

from shutil import copyfile


class ConvertAudio(QThread):
    sec_signal = pyqtSignal(str)
    def __init__(self, parent=None, audio_file ='', wav_file=''):
        super(ConvertAudio, self).__init__(parent)
        self.current_time = 0
        self.audio_file = audio_file
        self.wav_file = wav_file
    
    def __del__(self):
        self.wait()

    def run(self):
        #this is a special fxn that's called with the start() fxn       
        if os.path.isfile(self.audio_file):
            f = open(self.audio_file, "rb")
            # start of code variable declaration based from audio filename
            code = "const uint8_t sp" + self.wav_file[:-4]+"[] PROGMEM ={"
            try:
                byte = f.read(1)
                while byte != "":
                    # Do stuff with byte.
                    byte = f.read(1)
                    if self.is_version3:
                        #print ("%s0x%s," % ( code,(binascii.hexlify(byte)).decode("ascii").upper()))
                        code = ("%s0x%s," % (
                            code, (binascii.hexlify(byte)).decode("ascii").upper()))
                    else:
                        #print ("%s0x%s," % (code,(binascii.hexlify(byte))))
                        code = ("%s0x%s," % (code, (binascii.hexlify(byte))))
                    time.sleep(1)
                    self.sec_signal.emit(code) #display code to text area
            except Exception as ex:
                self.sec_signal.emit(str(ex)) #display code to text area
                print(ex)
            finally:
                f.close()
                code = code[:-4]
                code = code + "};"
                print(code)                
                self.sec_signal.emit(code) #display code to text area
                print
                print("voice.say(sp"+self.wav_file[:-4]+");")
        pass

class PyTalkieWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.copiedtext = ""
        self.init_vars()
        self.init_config()
        self.init_vars()
        self.init_ui()
        # self.initUI()

    def init_config(self):
        self.config_menus = configparser.ConfigParser()
        self.config_tools = configparser.ConfigParser()
        self.dir_name = os.path.dirname(os.path.realpath(__file__))
        self.menu_file = os.path.join(self.dir_name, "configs/menus.ini")
        self.tool_file = os.path.join(self.dir_name, "configs/toolbars.ini")

    def init_vars(self):
        self.is_loading = False
        self.is_version3 = False
        self.lastOpenedFolder = "C:\\"
        self.new_wavFilename = ''
        self.wavFile = ''
        if (sys.version_info > (3, 0)):
            # Python 3 code in this block
            self.is_version3 = True

    def init_ui(self):
        self.textEdit = QTextEdit()
        self.setCentralWidget(self.textEdit)
        self.textEdit.setText(" ")
        self.font = QFont()
        self.font.setFamily("Courier New")
        self.textEdit.setFont(self.font)

        self.menus = {}
        self.config_menus.read(self.menu_file)
        menubar = self.menuBar()
        for section in self.config_menus.sections():
            topMenu = menubar.addMenu(section)           
            for option in self.config_menus.options(section):
                menuLabel = self.config_menus.get(section, option)
                self.menus[option] = QAction(QIcon('images/%s.png' % option), menuLabel, self)
                # self.menus[option].setShortcut('Ctrl+Q')
                self.menus[option].setStatusTip(menuLabel)
                self.menus[option].triggered.connect(
                    lambda checked, tag=option: self.do_clickEvent(checked, tag))
                topMenu.addAction(self.menus[option])

        self.toolbars = {}
        self.config_tools.read(self.tool_file)
        for section in self.config_tools.sections():
            topToolbar = self.addToolBar(section)
            for option in self.config_tools.options(section):
                toolLabel = self.config_tools.get(section, option)
                self.toolbars[option] = QAction(QIcon('images/%s.png' % option), toolLabel, self)
                # self.menus[option].setShortcut('Ctrl+Q')
                self.toolbars[option].setStatusTip(toolLabel)
                self.toolbars[option].triggered.connect(
                    lambda checked, tag=option: self.do_clickEvent(checked, tag))
                topToolbar.addAction(self.toolbars[option])

        self.statusBar()
        self.setGeometry(100, 100, 500, 400)
        self.setWindowTitle('PyAudio-Talkie Synthesis')
        self.setWindowIcon(QIcon('images/convert.png'))
        self.show()

        self.statusBar().showMessage(os.path.join(self.dir_name, "alert.wav"))
        pass

    def get_audioName(self, filename):
        trim_name = re.sub(' +', ' ', filename)
        return trim_name.replace(' ', '_').upper()

    def do_clickEvent(self, checked, tag):
        if self.is_loading == True:
            return
        if tag == 'open':
            self.openo()
            pass
        elif tag == 'convert':
            self.start_convert()
            pass
        elif tag == 'save':
            pass
        elif tag=='about':
            self.about()
            pass
        elif tag=='qt':
            QApplication.instance().aboutQt()
            pass
        else:
            print(tag)            
        pass

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Message',
                                     "Are you sure to quit without Saving?", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.statusBar().showMessage('Quiting...')
            event.accept()
        else:
            event.ignore()
            self.save()
            event.accept()

    def start_convert(self):
        # change the cursor
        QApplication.setOverrideCursor(Qt.WaitCursor)
        self.is_loading = True
        self._converter = ConvertAudio(audio_file=self.new_wavFilename,wav_file=self.wavFile)
        self._converter.sec_signal.connect(self.textEdit.setText)
        self._converter.start()

    def convert_completed(self):
        if self.thread.is_alive():
            self.statusBar().showMessage("Converting %s" % self.new_wavFilename)
        else:
            QApplication.restoreOverrideCursor()
            self.is_loading = False
            self.statusBar().showMessage('Ready...')

    def openo(self):
        self.statusBar().showMessage('Open Audio (WAV) files')
        fname = QFileDialog.getOpenFileName(
            self, 'Open WAV File', self.lastOpenedFolder, "WAV files (*.wav)")
        self.statusBar().showMessage('Open WAV File')
        if fname[0]:
            folder, filename = os.path.split(fname[0])
            self.lastOpenedFolder = folder
            self.new_wavFilename = os.path.join(
                os.getcwd(), 'sounds', filename)
            self.wavFile = self.get_audioName(filename)
            self.statusBar().showMessage(self.new_wavFilename)
            copyfile(fname[0], self.new_wavFilename)

    def save(self):
        self.statusBar().showMessage('Add extension to file name')
        fname = QFileDialog.getSaveFileName(self, 'Save File')
        data = self.textEdit.toPlainText()

        file = open(fname[0], 'w')
        file.write(data)
        file.close()

    def copy(self):
        cursor = self.textEdit.textCursor()
        textSelected = cursor.selectedText()
        self.copiedtext = textSelected

    def about(self):
        QMessageBox.about(self, "PyAudio-Talkie Synthesis",
                "<b>PyAudio-Talkie Synthesis</b><br>"
                "Version: <b>1.0</b><br><br>"
                "Copyright  © <b> Tarsier 2018</b><br><br>"
                "GUI based ( of <b>ArduinoTalkieSpeech-Py</b>) that convert audio <br>"
                "file (WAV) to <b>Talkie</b> (speech synthesis for arduino) <br>"
                "compatible data.")


if __name__ == '__main__':

    app = QApplication(sys.argv)
    ex = PyTalkieWindow()
    sys.exit(app.exec_())

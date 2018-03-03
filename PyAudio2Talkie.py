import sys
import os
import re
import binascii
import time
from threading import Thread
# QFile, QFileInfo, QSettings, Qt, QTextStream, QTimer, QThread, pyqtSignal
from PyQt5.QtCore import *
# QMainWindow, QTextEdit, QAction, QApplication, QMessageBox, QFileDialog
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *  # QIcon, QFont
import webbrowser
try:
    import configparser
except:
    from six.moves import configparser

from shutil import copyfile


class ConvertAudio(QThread):
    sec_signal = pyqtSignal(str)

    def __init__(self, parent=None, audio_file='', wav_file=''):
        super(ConvertAudio, self).__init__(parent)
        self.current_time = 0
        self.audio_file = audio_file
        self.wav_file = wav_file[:-4]

        self.is_version3 = False
        if (sys.version_info > (3, 0)):
            # Python 3 code in this block
            self.is_version3 = True

    def __del__(self):
        self.wait()

    def run(self):
        # this is a special fxn that's called with the start() fxn
        if os.path.isfile(self.audio_file):
            # start of code variable declaration based from audio filename
            start_code = "const uint8_t sp" + self.wav_file+"[] PROGMEM = {\n"
            end_code = "\n};"
            self.code_list = []
            cl_index = 0
            code = ''
            try:
                # display code to text area
                self.sec_signal.emit(str(start_code))
                index = 0
                with open(self.audio_file, "rb") as f:
                    while True:
                        byte = f.read(1)
                        if not byte:
                            break
                        if self.is_version3:
                            #print ("%s0x%s," % ( code,(binascii.hexlify(byte)).decode("ascii").upper()))
                            code = ("%s0x%s," % (
                                code, (binascii.hexlify(byte)).decode("ascii").upper()))
                        else:
                            #print ("%s0x%s," % (code,(binascii.hexlify(byte))))
                            code = ("%s0x%s," %
                                    (code, (binascii.hexlify(byte))))
                        if index > 0 and (index % 100 == 0):
                            code = code + "\r\n"
                    time.sleep(1)
                    self.sec_signal.emit(code)  # display code to text area

            except Exception as ex:
                self.sec_signal.emit(str(ex))  # display code to text area
                print(ex)
            finally:
                f.close()
                code = code[:-1]
                final_code = start_code + code + end_code

                print(final_code)
                self.sec_signal.emit(final_code)  # display code to text area
                print
                print("voice.say(sp"+self.wav_file+");")
        pass


class OptionDialog(QDialog):
    NumGridRows = 3
    NumButtons = 4

    def __init__(self):
        super(OptionDialog, self).__init__()

        self.config_global = configparser.ConfigParser()      
        self.dir_name = os.path.dirname(os.path.realpath(__file__))
        self.opts_preview = os.path.join(self.dir_name, "configs","preview")
        self.global_file = os.path.join(self.dir_name, "configs/global.ini")
        self.config_global.read(self.global_file)

        self.output= self.config_global.get('global', 'output')
        self.theme  = self.config_global.get('global', 'theme')
        
        self.createThemesGroupBox()
        self.createFormGroupBox()
        self.createGridGroupBox()


        buttonBox = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel)

        buttonBox.accepted.connect(self.accept)
        buttonBox.rejected.connect(self.reject)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.horizontalGroupBox)
        mainLayout.addWidget(self.formGroupBox)
        mainLayout.addWidget(self.gridGroupBox)
        mainLayout.addWidget(buttonBox)
        self.setLayout(mainLayout)

        #self.changeStyle('Windows')
        self.setWindowTitle("Options")
        self.setWindowIcon(QIcon('images/convert.png'))
        self.selectionchange(self.output)


    def createThemesGroupBox(self):
        self.horizontalGroupBox = QGroupBox("Themes")
        layout = QHBoxLayout()

        self.originalPalette = QApplication.palette()
        print (self.originalPalette)

        styleComboBox = QComboBox()
        styleComboBox.addItems(QStyleFactory.keys())
        styleComboBox.activated[str].connect(self.changeStyle)

        styleLabel = QLabel("&Style:")
        styleLabel.setBuddy(styleComboBox)
        
        layout.addWidget(styleLabel)
        layout.addWidget(styleComboBox)

        self.horizontalGroupBox.setLayout(layout)

    def createGridGroupBox(self):
        self.gridGroupBox = QGroupBox("Ouput Preview")
        layout = QGridLayout()

        
        self.smallEditor = QTextEdit()
        self.smallEditor.setPlainText("Tarsier Preview")
        self.smallEditor.setReadOnly(True)

        layout.addWidget(self.smallEditor, 0, 2, 4, 1)

        #layout.setColumnStretch(1, 10)
        #layout.setColumnStretch(2, 20)
        self.gridGroupBox.setLayout(layout)

    def createFormGroupBox(self):
        self.formGroupBox = QGroupBox("Output")
        layout = QFormLayout()
        self.cb = QComboBox()
        self.cb.addItem("Arduino Syntax -Full")
        self.cb.addItem("Arduino Syntax -Declaration")
        self.cb.addItem("Plain Bytes")
        self.cb.currentIndexChanged.connect(self.selectionchange)
        layout.addRow(QLabel("Formatting: "), self.cb)
        self.formGroupBox.setLayout(layout)

    def selectionchange(self,i):
        self.output =str(i)
        self.opts_file = os.path.join(self.opts_preview, ("%s.txt" %i))
        if os.path.isfile(self.opts_file):
            f = open(self.opts_file, 'r')
            with f:
                data = f.read()
                self.smallEditor.setText(data)
        self.save_config()
        

    def changeStyle(self, styleName):
        self.theme = styleName
        print (self.theme)
        self.save_config()
        QApplication.setStyle(QStyleFactory.create(self.theme))
        QApplication.setPalette(self.originalPalette)
        
    def save_config(self):        
        self.config_global.set('global', 'theme', self.theme)
        self.config_global.set('global', 'output', self.output)
        # Writing our configuration file
        with open(self.global_file, 'w') as configfile:
            self.config_global.write(configfile)
        pass
        
class PyTalkieWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.copiedtext = ""
        self.init_vars()
        self.init_config()
        self.init_vars()
        self.init_ui()

    def init_config(self):
        self.config_opts = configparser.ConfigParser()
        self.config_global = configparser.ConfigParser()
        self.config_menus = configparser.ConfigParser()
        self.config_tools = configparser.ConfigParser()
        self.dir_name = os.path.dirname(os.path.realpath(__file__))
        self.opts_file = os.path.join(self.dir_name, "configs/options.ini")
        self.menu_file = os.path.join(self.dir_name, "configs/menus.ini")
        self.tool_file = os.path.join(self.dir_name, "configs/toolbars.ini")
        self.global_file = os.path.join(self.dir_name, "configs/global.ini")

    def save_config(self):
        self.config_global.set('global', 'width', str(
            self.frameGeometry().width()))
        self.config_global.set('global', 'height', str(
            self.frameGeometry().height()))
        self.config_global.set('global', 'init_dir', self.lastOpenedFolder)
        self.config_global.set('global', 'wav_file', self.new_wavFilename)
        #self.config_global.set('global', 'geometry', str(self.screenGeometry()))
        # Writing our configuration file
        with open(self.global_file, 'w') as configfile:
            self.config_global.write(configfile)
        pass

    def init_vars(self):
        self.is_loading = False
        self.lastOpenedFolder = "C:\\"
        self.new_wavFilename = ''
        self.wavFile = ''
        self.geometry = ''
        self.theme = ''

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
                self.menus[option] = QAction(
                    QIcon('images/%s.png' % option), menuLabel, self)
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
                self.toolbars[option] = QAction(
                    QIcon('images/%s.png' % option), toolLabel, self)
                # self.menus[option].setShortcut('Ctrl+Q')
                self.toolbars[option].setStatusTip(toolLabel)
                self.toolbars[option].triggered.connect(
                    lambda checked, tag=option: self.do_clickEvent(checked, tag))
                topToolbar.addAction(self.toolbars[option])

        self.config_global.read(self.global_file)
        self.lastOpenedFolder = self.config_global.get('global', 'init_dir')
        self.new_wavFilename = self.config_global.get('global', 'wav_file')
        self.width = self.config_global.get('global', 'width')
        self.height = self.config_global.get('global', 'height')
        self.geometry = self.config_global.get('global', 'geometry')
        self.theme = self.config_global.get('global', 'theme')

        self.statusBar()
        self.setGeometry(200, 200, int(self.width), int(self.height))
        self.setWindowTitle('PyAudio-Talkie Synthesis')
        self.setWindowIcon(QIcon('images/convert.png'))
        QApplication.setStyle(QStyleFactory.create(self.theme))
        self.show()

        pass

    def get_audioName(self, filename):
        trim_name = re.sub(' +', ' ', filename)
        trim_name = trim_name.replace(' ', '_')
        return trim_name.replace('-', '').upper()

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
        elif tag == 'option':
            self.option_dialog()
            pass
        elif tag == 'about':
            self.about()
            pass
        elif tag == 'qt':
            QApplication.instance().aboutQt()
            pass
        else:
            print(tag)
        pass

    def closeEvent(self, event):
        self.save_config()
        reply = QMessageBox.question(self, 'Exit',
                                     "Are you sure to quit without Saving?", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.statusBar().showMessage('Quiting...')
            event.accept()
        else:
            event.ignore()
            #self.save()
            event.accept()

    def start_convert(self):
        if os.path.isfile(self.new_wavFilename):
            # change the cursor
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.is_loading = True
            self._converter = ConvertAudio(
                audio_file=self.new_wavFilename, wav_file=self.wavFile)
            self._converter.sec_signal.connect(self.textEdit.setText)
            self._converter.start()
            self._converter.wait()
            QApplication.restoreOverrideCursor()
            self.is_loading = False

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

        if os.path.isfile(fname[0]):
            file = open(fname[0], 'w')
            file.write(data)
            file.close()

    def copy(self):
        cursor = self.textEdit.textCursor()
        textSelected = cursor.selectedText()
        self.copiedtext = textSelected

    def option_dialog(self):
        opt_dialog = OptionDialog()
        opt_dialog.setWindowModality(Qt.ApplicationModal)
        opt_dialog.exec_()

    def changeTitle(self, state):
        if state == Qt.Checked:
            pass
        pass

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
    '''
    #Dark Fusion Theme
    app.setStyle('Fusion')
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(53,53,53))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(15,15,15))
    palette.setColor(QPalette.AlternateBase, QColor(53,53,53))
    palette.setColor(QPalette.ToolTipBase, Qt.white)
    palette.setColor(QPalette.ToolTipText, Qt.white)
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(53,53,53))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
         
    palette.setColor(QPalette.Highlight, QColor(142,45,197).lighter())
    palette.setColor(QPalette.HighlightedText, Qt.black)
    app.setPalette(palette)
    '''
    pywin = PyTalkieWindow()
    sys.exit(app.exec_())

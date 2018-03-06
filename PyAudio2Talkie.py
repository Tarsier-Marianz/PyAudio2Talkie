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
from PyQt5 import QtPrintSupport
import webbrowser
try:
    import configparser
except:
    from six.moves import configparser

from shutil import copyfile


class ConvertAudio(QThread):
    sec_signal = pyqtSignal(str)

    def __init__(self, parent=None, audio_file='', wav_file='', syntax='0'):
        super(ConvertAudio, self).__init__(parent)
        self.current_time = 0
        self.syntax = syntax
        self.audio_file = audio_file
        self.wav_file = wav_file[:-4]

        self.is_version3 = False
        if (sys.version_info > (3, 0)):
            # Python 3 code in this block
            self.is_version3 = True

    def __del__(self):
        self.wait()

    def get_output(self, code):
        if self.syntax =='0':
            return "#include <Talkie.h>\n\nTalkie voice;\n\nconst uint8_t sp%s[] PROGMEM = {\n%s\n};\n\nsetup(){\n    voice.say(sp%s);\n}\nvoid(){\n}\n" % ( self.wav_file,code, self.wav_file)
        elif self.syntax=='1':
            return "const uint8_t sp%s[] PROGMEM = {\n%s\n};" % (self.wav_file,code)
        else:
            return code

    def run(self):
        # this is a special fxn that's called with the start() fxn
        if os.path.isfile(self.audio_file):
            # start of code variable declaration based from audio filename           
            code = ''
            try:
                # display code to text area
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
                    time.sleep(1)
                    self.sec_signal.emit(code)  # display code to text area

            except Exception as ex:
                self.sec_signal.emit(str(ex))  # display code to text area
                print(ex)
            finally:
                f.close()
                code = code[:-1]
                final_code = self.get_output( code )

                #print(final_code)
                self.sec_signal.emit(final_code)  # display code to text area               
        pass

class Highlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super(Highlighter, self).__init__(parent)

        keywordFormat = QTextCharFormat()
        keywordFormat.setForeground(Qt.darkBlue)
        keywordFormat.setFontWeight(QFont.Bold)

        keywordPatterns = ["\\bchar\\b", "\\bclass\\b", "\\bconst\\b",
                "\\bdouble\\b", "\\benum\\b", "\\bexplicit\\b", "\\bfriend\\b",
                "\\binline\\b", "\\bint\\b", "\\blong\\b", "\\bnamespace\\b",
                "\\boperator\\b", "\\bprivate\\b", "\\bprotected\\b",
                "\\bpublic\\b", "\\bshort\\b", "\\bsignals\\b", "\\bsigned\\b",
                "\\bslots\\b", "\\bstatic\\b", "\\bstruct\\b",
                "\\btemplate\\b", "\\btypedef\\b", "\\btypename\\b",
                "\\bunion\\b", "\\bunsigned\\b", "\\bvirtual\\b", "\\bvoid\\b",
                "\\bvolatile\\b", "\\bPROGMEM\\b"]

        self.highlightingRules = [(QRegExp(pattern), keywordFormat)
                for pattern in keywordPatterns]

        classFormat = QTextCharFormat()
        classFormat.setFontWeight(QFont.Bold)
        classFormat.setForeground(Qt.darkMagenta)
        self.highlightingRules.append((QRegExp("\\bQ[A-Za-z]+\\b"),
                classFormat))

        singleLineCommentFormat = QTextCharFormat()
        singleLineCommentFormat.setForeground(Qt.red)
        self.highlightingRules.append((QRegExp("//[^\n]*"),
                singleLineCommentFormat))

        self.multiLineCommentFormat = QTextCharFormat()
        self.multiLineCommentFormat.setForeground(Qt.red)

        quotationFormat = QTextCharFormat()
        quotationFormat.setForeground(Qt.darkGreen)
        self.highlightingRules.append((QRegExp("\".*\""), quotationFormat))

        datatypeFormat = QTextCharFormat()
        datatypeFormat.setForeground(Qt.darkGreen)
        self.highlightingRules.append((QRegExp("uint8_t"), datatypeFormat))

        talkieFormat = QTextCharFormat()
        talkieFormat.setForeground(Qt.darkRed)
        self.highlightingRules.append((QRegExp("Talkie"), talkieFormat))

        functionFormat = QTextCharFormat()
        functionFormat.setFontItalic(True)
        functionFormat.setForeground(Qt.blue)
        self.highlightingRules.append((QRegExp("\\b[A-Za-z0-9_]+(?=\\()"),
                functionFormat))

        self.commentStartExpression = QRegExp("/\\*")
        self.commentEndExpression = QRegExp("\\*/")

    def highlightBlock(self, text):
        for pattern, format in self.highlightingRules:
            expression = QRegExp(pattern)
            index = expression.indexIn(text)
            while index >= 0:
                length = expression.matchedLength()
                self.setFormat(index, length, format)
                index = expression.indexIn(text, index + length)

        self.setCurrentBlockState(0)

        startIndex = 0
        if self.previousBlockState() != 1:
            startIndex = self.commentStartExpression.indexIn(text)

        while startIndex >= 0:
            endIndex = self.commentEndExpression.indexIn(text, startIndex)

            if endIndex == -1:
                self.setCurrentBlockState(1)
                commentLength = len(text) - startIndex
            else:
                commentLength = endIndex - startIndex + self.commentEndExpression.matchedLength()

            self.setFormat(startIndex, commentLength,
                    self.multiLineCommentFormat)
            startIndex = self.commentStartExpression.indexIn(text,
                    startIndex + commentLength)

class OptionDialog(QDialog):
    NumGridRows = 3
    NumButtons = 4

    def __init__(self, parent=None):
        super(OptionDialog, self).__init__(parent)

        self.config_global = configparser.ConfigParser()      
        self.dir_name = os.path.dirname(os.path.realpath(__file__))
        self.opts_preview = os.path.join(self.dir_name, "configs","preview")
        self.global_file = os.path.join(self.dir_name, "configs/global.ini")
        self.config_global.read(self.global_file)

        self.output= self.config_global.get('global', 'output')
        self.theme  = self.config_global.get('global', 'theme')
        
        self.createThemesGroupBox()
        self.createGridGroupBox()
        self.createFormGroupBox()


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
        self.horizontalGroupBox.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed)#disabled auto stretching
        layout = QHBoxLayout()
        self.originalPalette = QApplication.palette()

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

        font = QFont()
        font.setFamily('Courier')
        font.setFixedPitch(True)
        font.setPointSize(8)

        self.smallEditor = QTextEdit()
        self.smallEditor.setPlainText("Tarsier Preview")
        self.smallEditor.setReadOnly(True)
        self.smallEditor.setFont(font)
        self.highlighter = Highlighter(self.smallEditor.document())

        layout.addWidget(self.smallEditor, 0, 2, 4, 1)

        #layout.setColumnStretch(1, 10)
        #layout.setColumnStretch(2, 20)
        self.gridGroupBox.setLayout(layout)

    def createFormGroupBox(self):
        self.formGroupBox = QGroupBox("Output")
        self.formGroupBox.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed) #disabled auto stretching
        layout = QFormLayout()
        self.cb = QComboBox()
        self.cb.addItem("Arduino Syntax -Full")
        self.cb.addItem("Arduino Syntax -Declaration")
        self.cb.addItem("Plain Bytes")
        self.cb.currentIndexChanged.connect(self.selectionchange)
        self.cb.setCurrentIndex(int(self.output))
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
        self.init_editor()
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
        self.config_global.set('global', 'wav_source', self.new_wavFilename)
        self.config_global.set('global', 'wav_file', self.source_wavFilename)
        #self.config_global.set('global', 'geometry', str(self.screenGeometry()))
        # Writing our configuration file
        with open(self.global_file, 'w') as configfile:
            self.config_global.write(configfile)
        pass
    
    def reinit_configs(self):
        self.config_global.read(self.global_file)
        self.lastOpenedFolder = self.config_global.get('global', 'init_dir')
        self.source_wavFilename = self.config_global.get('global', 'wav_source')
        self.new_wavFilename = self.config_global.get('global', 'wav_file')
        self.width = self.config_global.get('global', 'width')
        self.height = self.config_global.get('global', 'height')
        self.geometry = self.config_global.get('global', 'geometry')
        self.theme = self.config_global.get('global', 'theme')
        self.syntax = self.config_global.get('global', 'output')

        self.open_file(self.source_wavFilename)

    def init_vars(self):
        self.is_loading = False
        self.lastOpenedFolder = "C:\\"
        self.source_wavFilename = ''
        self.new_wavFilename = ''
        self.wavFile = ''
        self.geometry = ''
        self.theme = ''
        self.syntax = ''

    def init_editor(self):
        font = QFont()
        font.setFamily('Courier')
        font.setFixedPitch(True)
        font.setPointSize(8)

        self.textEdit = QTextEdit()
        self.setCentralWidget(self.textEdit)
        self.textEdit.setFont(font)
        self.highlighter = Highlighter(self.textEdit.document())

    def init_ui(self):    
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

        self.reinit_configs()

        self.statusBar()
        self.setGeometry(200, 200, int(self.width), int(self.height))
        self.setWindowTitle('PyAudio-Talkie Synthesis')
        self.setWindowIcon(QIcon('images/convert.png'))
        QApplication.setStyle(QStyleFactory.create(self.theme))

        self.set_details(self.new_wavFilename)
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
            self.save()
            pass
        elif tag == 'option':
            self.option_dialog()
            pass
        elif tag=='copy':
            self.copy()
            pass
        elif tag == 'about':
            self.about()
            pass
        elif tag == 'print':
            self.print()
            pass
        elif tag == 'preview':
            self.print_preview()
            pass
        elif tag == 'exit':
            self.close()
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
                                     "Are you sure to quit?", QMessageBox.Yes |
                                     QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.statusBar().showMessage('Quiting...')
            event.accept()
        else:
            event.ignore()
            #self.save()
            #event.accept()

    def start_convert(self):
        if os.path.isfile(self.new_wavFilename):
            # change the cursor
            QApplication.setOverrideCursor(Qt.WaitCursor)
            self.is_loading = True
            self._converter = ConvertAudio(
                audio_file=self.new_wavFilename, wav_file=self.wavFile, syntax=self.syntax)
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
            self, 'Open Audio File', self.lastOpenedFolder, "WAV files (*.wav);;All files (*.*)")
        
        if fname[0]:
            self.open_file(fname[0])
            
    def open_file(self, fullfilename):
        if fullfilename:
            folder, filename = os.path.split(fullfilename)
            self.lastOpenedFolder = folder
            self.new_wavFilename = os.path.join(
                os.getcwd(), 'sounds', filename)
            self.wavFile = self.get_audioName(filename)
            self.statusBar().showMessage(self.new_wavFilename)
            try:
                copyfile(fullfilename, self.new_wavFilename)
            except:
                pass
            self.set_details(fullfilename)
           
    def set_details(self, full_filename):
        if os.path.isfile(full_filename):
            folder, filename = os.path.split(full_filename)
            file_details = "[Source Details]\n Size: %s\n Filename: %s\n New Filename: %s\n Directory: %s\n Full Path: %s\n" % (os.path.getsize(full_filename),filename, self.wavFile, folder,full_filename)
            file_details += "\nClick Convert to generate Talkie speech compatible data for Arduino...\n\nNote: the bigger file size of audio file, the longer it takes to execute conversion"
            self.textEdit.setText(file_details)

    def save(self):
        data = self.textEdit.toPlainText()
        if data.strip():
            self.statusBar().showMessage('Add extension to file name')
            fname = QFileDialog.getSaveFileName(self, 'Save File', self.lastOpenedFolder,"All Files (*);;Text Files (*.txt);;Arduino Sketch (*.ino)")
            if fname and os.path.isfile(fname[0]):
                try:
                    file = open(fname[0], 'w')
                    file.write(data)
                    file.close()
                except:
                    pass

    def copy(self):
        self.copiedtext = self.textEdit.toPlainText()
        clipboard = QApplication.clipboard()
        clipboard.setText(self.copiedtext , mode=clipboard.Clipboard)
        event = QEvent(QEvent.Clipboard)
        QApplication.sendEvent(clipboard, event)

    def option_dialog(self):
        opt_dialog = OptionDialog(self)
        opt_dialog.setWindowModality(Qt.ApplicationModal)
        opt_dialog.resize(500,500)
        opt_dialog.exec_()
        self.reinit_configs()

    def print(self):
        try:
            dialog = QtPrintSupport.QPrintDialog()
            if dialog.exec_() == QtWidgets.QDialog.Accepted:
                self.textEdit.document().print_(dialog.printer())
        except:
            pass

    def print_preview(self):
        try:
            dialog = QtPrintSupport.QPrintPreviewDialog()
            dialog.setWindowIcon(QIcon('images/convert.png'))
            dialog.paintRequested.connect(self.textEdit.print_)
            dialog.exec_()
        except:
            pass

    def about(self):
        QMessageBox.about(self, "PyAudio-Talkie Synthesis",
                          "<b>PyAudio-Talkie Synthesis</b><br>"
                          "Version: <b>1.0.5801.98001</b><br><br>"
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

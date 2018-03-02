import sys
import os
import re
import binascii
from PyQt5.QtWidgets import QMainWindow, QTextEdit, QAction, QApplication,QMessageBox,QFileDialog
from PyQt5.QtGui import QIcon
import webbrowser
try:
    import configparser
except:
    from six.moves import configparser

from shutil import copyfile

class Example(QMainWindow):
    
    def __init__(self):
        super().__init__()
        self.copiedtext=""
        self.init_vars()
        self.init_config()
        self.init_vars()
        self.init_ui()
        #self.initUI()

    def init_config(self):
        self.config_menus = configparser.ConfigParser()
        self.config_tools = configparser.ConfigParser()
        self.dir_name = os.path.dirname(os.path.realpath(__file__))
        self.menu_file = os.path.join(self.dir_name, "configs/menus.ini")
        self.tool_file = os.path.join(self.dir_name, "configs/toolbars.ini")

    def init_vars(self):
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

        self.menus = {}
        self.config_menus.read(self.menu_file)
        menubar = self.menuBar()
        for section in self.config_menus.sections():
            topMenu = menubar.addMenu(section)
            topToolbar = self.addToolBar(section)
            for option in self.config_menus.options(section):
                menuLabel = self.config_menus.get(section, option)
                self.menus[option] = QAction(QIcon('images/%s.png' % option), menuLabel, self)
                self.menus[option].setShortcut('Ctrl+Q')
                self.menus[option].setStatusTip(option)
                self.menus[option].triggered.connect(lambda checked, tag=option:self.do_clickEvent(checked,tag))                
                topMenu.addAction(self.menus[option])
                topToolbar.addAction(self.menus[option])
                
        self.statusBar()      
        self.setGeometry(100,100,400,400)
        self.setWindowTitle('PyAudio-Talkie Synthesis')    
        self.setWindowIcon(QIcon('images/convert.png')) 
        self.show()
        pass

    def get_audioName(self, filename):
        trim_name = re.sub(' +',' ',filename)
        return trim_name.replace(' ', '_').upper()

    def do_clickEvent(self, checked, tag):
        if tag=='open':
            self.openo()
            pass
        elif tag=='convert':
            self.convert()
            pass
        elif tag=='save':
            pass
        else:
            print (tag)
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
            
    def openo(self):
        self.statusBar().showMessage('Open Audio (WAV) files')
        fname = QFileDialog.getOpenFileName(self, 'Open WAV File', self.lastOpenedFolder,"WAV files (*.wav)")
        self.statusBar().showMessage('Open WAV File')
        if fname[0]:
            folder, filename = os.path.split(fname[0])
            self.lastOpenedFolder  =  folder
            self.new_wavFilename = os.path.join(os.getcwd(), 'sounds',filename)
            self.wavFile = self.get_audioName(filename)
            self.statusBar().showMessage(self.new_wavFilename)
            copyfile(fname[0],self.new_wavFilename)

    def convert(self):
        if os.path.isfile(self.new_wavFilename):
            f = open(self.new_wavFilename, "rb")
            # start of code variable declaration based from audio filename
            code ="const uint8_t sp"+ self.wavFile[:-4]+"[] PROGMEM ={"
            try:
                byte = f.read(1)
                while byte != "":
                    # Do stuff with byte.
                    byte = f.read(1)
                    if self.is_version3:
                        #print ("%s0x%s," % ( code,(binascii.hexlify(byte)).decode("ascii").upper()))
                        code = ("%s0x%s," % ( code,(binascii.hexlify(byte)).decode("ascii").upper()))
                    else:
                        #print ("%s0x%s," % (code,(binascii.hexlify(byte))))
                        code = ("%s0x%s," % (code,(binascii.hexlify(byte))))
                    self.textEdit.setText(code)
            except Exception as ex:
                print (ex)
            finally:
                f.close()
                code = code[:-4]
                code = code +"};"
                print (code)
                self.textEdit.setText(code)
                print
                print("voice.say(sp"+self.wavFile[:-4]+");")
        pass

    def save(self):
        self.statusBar().showMessage('Add extension to file name')
        fname =QFileDialog.getSaveFileName(self, 'Save File')
        data=self.textEdit.toPlainText()
        
        file=open(fname[0],'w')
        file.write(data)
        file.close()
    
    def copy(self):
        cursor=self.textEdit.textCursor()
        textSelected = cursor.selectedText()
        self.copiedtext=textSelected
    
    
    def about(self):
        url ="https://en.wikipedia.org/wiki/Text_editor"
        self.statusBar().showMessage('Loading url...')
        webbrowser.open(url)
        
        
if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    ex = Example()
    sys.exit(app.exec_())

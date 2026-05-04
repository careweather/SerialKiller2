from SK_common import * 
from datetime import datetime 
import os

from PyQt6 import QtWidgets, QtCore
from GUI_SK_TEXT_POPUP import Ui_Text_Viewer

class SK_Text_Popup(QtWidgets.QMainWindow, Ui_Text_Viewer):
    file_path = None 
    file_extension = None 
    file_dir = None 
    last_modified = None 
    saved = True 
    def __init__(self, text:str = None, file:str = None, style_path:str = None):
        super().__init__()
        
        self.setupUi(self)
        self.textEdit.setTabStopDistance(40)
        
        
        self.actionSave.triggered.connect(self.save_file)
        self.actionSave_As.triggered.connect(self.save_file_as)
        #self.textEdit.setReadOnly(True)
        
        self.label_info.hide() 
        self.menuBar().hide()
        
        #self.textEdit.setTextInteractionFlags(QtCore.Qt.TextInteractionFlag.TextSelectableByKeyboard | QtCore.Qt.TextInteractionFlag.TextSelectableByMouse)
        
        if style_path is not None: 
            with open(style_path, "r") as f: 
                style_text = f.read()
                vprint(f"style_text: {style_text}")
                self.textEdit.document().setDefaultStyleSheet(style_text)
        
        


        if text is not None: 
            self.textEdit.setText(text)
            self.setWindowTitle("Text Viewer")
        elif file is not None: 
            self.file_path = file 
            self.file_extension = os.path.splitext(file)[1]
            self.file_dir = os.path.dirname(file)
            self.last_modified = datetime.fromtimestamp(os.path.getmtime(file))
            self.setWindowTitle(file)
            if not os.path.exists(file): 
                eprint(f"File {file} does not exist", color="red")
                self.label_info.setText(f"File {file} does not exist")
                return 
            
            with open(file, "r") as f:
                if self.file_extension == ".md":
                    #self.textEdit.setViewportMargins(20,0,20,0)
                    #self.textEdit.setContentsMargins(20,20,20,20)
                    self.textEdit.document().setMarkdown(f.read())
                    #h = self.textEdit.toHtml()
                    #print("----------------------------")
                    #print(h)
                    #print("----------------------------")
                    #self.textEdit.document().setHtml(h)
                    #self.textEdit.setMarkdown(f.read())
                elif self.file_extension == ".html":
                    #self.textEdit.setViewportMargins(20,0,20,0)
                    #self.textEdit.setContentsMargins(20,20,20,20)
                    self.textEdit.document().setHtml(f.read())
                elif self.file_extension.endswith((".png", ".svg")):
                    self.textEdit.setMarkdown(f"![image]({file})")
                else: 
                    self.textEdit.setText(f.read())
                    self.label_info.show()
                    self.menuBar().show() 
                    self.update_label_info()
                    self.setStyleSheet("font: Ubuntu Mono;font-size: 10pt;")
                    ## made text editable 
                    self.textEdit.setReadOnly(False)
                    self.textEdit.setLineWrapMode(QtWidgets.QTextEdit.LineWrapMode.NoWrap)
                    self.textEdit.textChanged.connect(self.text_edited)



    def text_edited(self):
        if self.saved == True:
            self.saved = False 
            self.update_label_info() 
        


    def update_label_info(self):
        if not self.file_path:
            return 
        last_modified = self.last_modified.strftime('%Y-%m-%d %I:%M:%S %p')
        self.label_info.setText(f"Last Modified:\t{last_modified}\nSaved:\t\t{self.saved}")
        if self.saved == True:
            self.label_info.setStyleSheet(f"color: {color_to_style_sheet(COLOR_LIGHT_GREEN)};")
        else:
            self.label_info.setStyleSheet("color: red;")

    def save_file(self):
        self.save_file_as(self.file_path)

    def save_file_as(self, filename:str = None):
        #dprint(f"[TEXT POPUP] save file as: {filename}")
        if not self.file_path:
            return 
        if not filename: 
            filename = get_save_file_popup(self, file_path = self.file_dir, extensions="*" + self.file_extension)
            if not filename: 
                return  
            
        dprint(f"[TEXT POPUP] save file as: {filename}")
        
        ## If the file is the original file, check if the original file has been modified
        if filename == self.file_path:
            if self.last_modified != datetime.fromtimestamp(os.path.getmtime(self.file_path)):
                dprint(f"[TEXT POPUP] original file has been modified", color = 'red')
                # Open a dialog to ask if the user wants to overwrite the file
                overwrite_dialog = QtWidgets.QMessageBox()
                overwrite_dialog.setIcon(QtWidgets.QMessageBox.Icon.Warning)
                overwrite_dialog.setWindowTitle("File Modified")
                overwrite_dialog.setText(f"The original file {self.file_path} has been modified. Do you want to save the changes?")
                overwrite_dialog.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
                overwrite_dialog.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
                overwrite_dialog.exec()
                dprint(f"overwrite_dialog.clickedButton(): {overwrite_dialog.clickedButton().text()}")
                if overwrite_dialog.clickedButton().text() == "&No":
                    dprint("[TEXT POPUP] User cancelled", color = 'red')
                    return 
        elif os.path.exists(filename):
            dprint(f"[TEXT POPUP] file already exists: {filename}", color = 'red')
            ## Open a dialog to ask if the user wants to overwrite the file
            overwrite_dialog = QtWidgets.QMessageBox()
            overwrite_dialog.setIcon(QtWidgets.QMessageBox.Icon.Warning)
            overwrite_dialog.setWindowTitle("File Already Exists")
            overwrite_dialog.setText(f"File {filename} already exists. Do you want to overwrite it?")
            overwrite_dialog.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
            overwrite_dialog.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)
            overwrite_dialog.exec()
            #dprint(f"overwrite_dialog.clickedButton(): {overwrite_dialog.clickedButton().text()}")
            if overwrite_dialog.clickedButton().text() == "&No":
                dprint("[TEXT POPUP] User cancelled", color = 'red')
                return 

        
        
        with open(filename, "w+") as f:
            f.write(self.textEdit.toPlainText())

        self.file_path = filename
        self.setWindowTitle(filename)
        self.last_modified = datetime.fromtimestamp(os.path.getmtime(filename))
        self.saved = True 
        self.update_label_info()

        dprint(f"[TEXT POPUP] file saved: {filename}", color = 'green')
        #self.close()
        
    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key.Key_Escape:
            self.close()
        elif event.key() == QtCore.Qt.Key.Key_S and event.modifiers() == QtCore.Qt.KeyboardModifier.ControlModifier:
            self.save_file()
        else: 
            super().keyPressEvent(event)



    
def open_text_popup(self, text:str = None, file:str = None, style_path:str = None):
    self.window = SK_Text_Popup(text = text, file = file, style_path = style_path)
    self.window.show()
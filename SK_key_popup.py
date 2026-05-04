from PyQt6 import QtWidgets, QtCore
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QClipboard
from GUI_PLOT_KEY_POPUP import Ui_key_popup
from SK_common import *


class KeyPopup(QtWidgets.QDialog, Ui_key_popup):
    result = pyqtSignal(dict)
    data = {}
    def __init__(self, *args, data: dict = {}, **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        self.setWindowTitle("Serial Killer Plot Keys")
        self.toolButton_add_row.clicked.connect(self.add_row)
        self.data = data
        


        


    def any_value_changed(self):
        data = self.tableWidget.get_data()
        s = plot_elements_to_str(data)
        self.label_debug.setText("'" + s + "'")

    def show(self):
        super().show()
        
        self.tableWidget.set_data(self.data)
        self.any_value_changed()
        self.tableWidget.cellChanged.connect(self.any_value_changed)
        self.tableWidget.any_change.connect(self.any_value_changed)
        

    def add_row(self):
        self.tableWidget.insert_row(self.tableWidget.rowCount())

    def accept(self):
        self.result.emit(self.tableWidget.get_data())
        super().accept()

    def reject(self):
        super().reject()


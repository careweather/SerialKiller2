from SK_common import *
from SK_help import *
import copy
import time

from PyQt6 import QtCore, QtGui, QtWidgets


class GroupBoxProxyStyle(QtWidgets.QProxyStyle):
    def drawPrimitive(self, element, option, painter, widget):
        if element == QtWidgets.QStyle.PrimitiveElement.PE_IndicatorCheckBox and isinstance(widget, QtWidgets.QGroupBox):
            super().drawPrimitive(
                QtWidgets.QStyle.PrimitiveElement.PE_IndicatorArrowDown if widget.isChecked() else QtWidgets.QStyle.PrimitiveElement.PE_IndicatorArrowRight,
                option,
                painter,
                widget,
            )
        else:
            super().drawPrimitive(element, option, painter, widget)


class CollapsingGroupBox(QtWidgets.QGroupBox):
    grid_margins = None
    grid_spacing = None
    layout_margins = None
    layout_spacing = None
    open_height = None 

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        if not self.isCheckable():
            self.setCheckable(True)
        self.clicked.connect(self.toggle_collapse)
        self.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeading | QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignVCenter)


    def showEvent(self, event):
        if self.open_height is None:
            self.open_height = self.height() 
        self.toggle_collapse(self.isChecked())
        super().showEvent(event)

    def toggle_collapse(self, checked):
        if self.grid_margins is None:
            self.grid_spacing = self.layout().spacing()
            self.grid_margins = (
                self.layout().contentsMargins().left(),
                self.layout().contentsMargins().top(),
                self.layout().contentsMargins().right(),
                self.layout().contentsMargins().bottom(),
            )
            self.layout_margins = (self.contentsMargins().left(), self.contentsMargins().top(), self.contentsMargins().right(), self.contentsMargins().bottom())
            # self.layout_spacing = self.layout().setSizeConstraint()
            # print(f" {self.objectName()} grid_margins {self.grid_margins} layout_margins {self.layout_margins}")

        if checked:
            # self.layout().setContentsMargins(*self.grid_margins)
            # # self.layout().unsetContentsMargins()
            # self.layout().setSpacing(self.grid_spacing)
            # self.setContentsMargins(*self.layout_margins)
            # self.setSizePolicy(QtWidgets.QSizePolicy.Policy.Minimum, QtWidgets.QSizePolicy.Policy.Minimum)
            #print(self.layout_margins, self.maximumHeight())
            self.setFixedHeight(self.open_height)

        else:
            # #print("notchecked")
            # self.layout().setSpacing(0)
            # self.layout().setContentsMargins(0, 0, 0, 0)
            # self.setContentsMargins(0, 0, 0, 0)
            # self.contentsRect().setHeight(0)
            self.setFixedHeight(22)

        # for child in self.layout().children

        return 

        for child in self.children():
            if getattr(child, "show", None):
                if checked:
                    child.show()
                else:
                    child.hide()
        # print(f"checked {checked} \n contents rect {self.contentsRect().height()} {self.contentsRect().x()} {self.contentsRect().y()} {self.contentsRect().}")


class ScriptTextEdit(QtWidgets.QTextEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setTabStopDistance(20)
        # print("ScriptTextEdit init", args, kwargs)

    def insertFromMimeData(self, source: QtCore.QMimeData):
        #print("insertFromMimeData", source)
        if source.hasText():
            self.insertPlainText(source.text())
        else:
            super().insertFromMimeData(source)
        

    
class ColorComboBox(QtWidgets.QComboBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.addItems(COLOR_DICT.keys())


def event_to_string(event: QtGui.QKeyEvent):
    s = f"""key-press event: text: <{event.text()}> key: <{event.key()}> modifiers: <{event.modifiers()}> \
    nativeVirtualKey: <{event.nativeVirtualKey()}> isAutoRepeat: <{event.isAutoRepeat()}> count: <{event.count()}> \
    type: <{event.type()}>"""
    return s





class CaptureLineEdit(QtWidgets.QLineEdit):
    SPECIAL_KEYS = {
        QtCore.Qt.Key.Key_Tab: "TAB",
        QtCore.Qt.Key.Key_Return: "RETURN",
        QtCore.Qt.Key.Key_Enter: "ENTER",
        QtCore.Qt.Key.Key_Left: "LEFT",
        QtCore.Qt.Key.Key_Right: "RIGHT",
        QtCore.Qt.Key.Key_Up: "UP",
        QtCore.Qt.Key.Key_Down: "DOWN",
        QtCore.Qt.Key.Key_Backspace: "BACKSPACE",
        QtCore.Qt.Key.Key_F1: "F1",
        QtCore.Qt.Key.Key_F2: "F2",
        QtCore.Qt.Key.Key_F3: "F3",
        QtCore.Qt.Key.Key_F4: "F4",
        QtCore.Qt.Key.Key_F5: "F5",
        QtCore.Qt.Key.Key_F6: "F6",
        QtCore.Qt.Key.Key_F7: "F7",
        QtCore.Qt.Key.Key_F8: "F8",
        QtCore.Qt.Key.Key_F9: "F9",
        QtCore.Qt.Key.Key_F10: "F10",
    }

    keyPress = QtCore.pyqtSignal(str)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # self.setValidator(QtGui.QIntValidator(0, 255))

    ## Needed to prevent tabbing to the next widget
    def focusNextPrevChild(self, next):
        return False

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if DEBUG_LEVEL & 128:
            cprint(event_to_string(event), color="magenta")
        if event.key() == QtCore.Qt.Key.Key_Escape:
            super().keyPressEvent(event)
            return
        elif event.key() in self.SPECIAL_KEYS:
            self.keyPress.emit(self.SPECIAL_KEYS[event.key()])
        elif event.text():
            self.keyPress.emit(event.text())
            return
        else:
            super().keyPressEvent(event)
            return


class KeyTableWidget(QtWidgets.QTableWidget):
    any_change = QtCore.pyqtSignal(bool)
    def __init__(self, *args, **kwargs):
        #print("key table widget init", args, kwargs)
        super().__init__(*args, **kwargs)

        
    def set_data(self, data: dict = {}):
        self.setRowCount(0)
        #print("data", data)
        if not data:
            self.insert_row(self.rowCount(), "", EMPTY_PLOT_ELEMENT)
            return
        for key in data:
            self.insert_row(self.rowCount(), key, data[key])


    def _any_change(self):
        self.any_change.emit(True)


        

    def get_row_data(self, row: int):
        data = EMPTY_PLOT_ELEMENT.copy()
        data["mult"] = round(float(self.item(row, 1).text()), 4)
        data["color"] = self.cellWidget(row, 2).currentText()
        if data["color"] == "default":
            data["color"] = None
        data["points"] = self.item(row, 3).text()
        if data["points"] == "default" or data["points"] == "" or data["points"] == "None":
            data["points"] = None
        data["export"] = self.cellWidget(row, 4).isChecked()
        return data

    def get_data(self):
        data = {}
        for row in range(self.rowCount()):
            key = self.item(row, 0).text()
            if not key: 
                continue
            data[key] = self.get_row_data(row)
        return data

    def insert_row(self, row: int, key: str = "", data: dict = EMPTY_PLOT_ELEMENT):
        mult = data.get("mult", 1.00)
        points = data.get("points", None)
        color = data.get("color", None)
        self.insertRow(row)
        key_item = QtWidgets.QTableWidgetItem(key)
        #key_item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter | QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.setItem(row, 0, key_item)
        self.setItem(row, 1, QtWidgets.QTableWidgetItem(str(mult)))
        combo_box = ColorComboBox()
        combo_box.currentTextChanged.connect(self._any_change)
        if color in COLOR_DICT:
            combo_box.setCurrentText(color)
        self.setCellWidget(row, 2, combo_box)
        if points is None:
            points = "default"
        self.setItem(row, 3, QtWidgets.QTableWidgetItem(str(points)))
        checkBox = QtWidgets.QCheckBox()
        checkBox.stateChanged.connect(self._any_change)
        checkBox.setChecked(data.get("export", True))
        self.setCellWidget(row, 4, checkBox)
        


    def showEvent(self, event):
        #print("key table widget show event")
        super().showEvent(event)
        #self.setRowCount(0)
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(["Key", "Multiplier", "Color", "Points", "Export"])
        self.horizontalHeader().setStretchLastSection(True)
        self.horizontalHeader().setVisible(True)
        self.insert_row(self.rowCount())

from SK_common import *
from SK_help import *
import copy 
import time 

from PyQt6 import QtCore, QtGui, QtWidgets

KEY_MODIFIERS = {
    QtCore.Qt.Key.Key_Backspace: chr(0x08),
    QtCore.Qt.Key.Key_Enter: chr(0x0D),
    QtCore.Qt.Key.Key_Return: chr(0x0D),
    QtCore.Qt.Key.Key_Escape: chr(0x1B),
    QtCore.Qt.Key.Key_Tab: chr(0x09),
    QtCore.Qt.Key.Key_Up: "\x1B[A",
    QtCore.Qt.Key.Key_Down: "\x1B[B",
    QtCore.Qt.Key.Key_Left: "\x1B[D",
    QtCore.Qt.Key.Key_Right: "\x1B[C",
}

class TerminalWidget(QtWidgets.QPlainTextEdit):
    escape_buffer = None 
    escape_sequence:bytes = None
    display_attributes = {'4': lambda x: x}
    auto_scroll = True 
    typed = QtCore.pyqtSignal(str)
    format = "UTF-8"
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setTextInteractionFlags(
            QtCore.Qt.TextInteractionFlag.TextSelectableByKeyboard | QtCore.Qt.TextInteractionFlag.TextSelectableByMouse | QtCore.Qt.TextInteractionFlag.TextBrowserInteraction
        )
        self.fmt = self.currentCharFormat()
        

    def keyPressEvent(self, event:QtGui.QKeyEvent):
        #print(f"{event.key()} {type(event.key())}\n\t{event.text()} {type(event.text())}\n\t{event.modifiers()} {type(event.modifiers())}\n\t{event.nativeVirtualKey()} {type(event.nativeVirtualKey())}")
        k = event.key()

        #print(self.textCursor().selectionStart(), self.textCursor().selectionEnd())   
        if self.textCursor().selectionStart() != self.textCursor().selectionEnd():
            super().keyPressEvent(event)
            return 
        if k == QtCore.Qt.Key.Key_Escape:
            super().keyPressEvent(event)
            return 

        if k in KEY_MODIFIERS:
            #char_pressed = KEY_MODIFIERS[k]
            char_pressed = KEY_MODIFIERS[k]
            #print(f"MODIFIER {k} {KEY_MODIFIERS[event.key()]}")
        elif event.text():
            char_pressed = event.text()
        elif event.modifiers() == QtCore.Qt.KeyboardModifier.ControlModifier:
            #print("Control modifier")
            super().keyPressEvent(event)
            return 
        else:
            super().keyPressEvent(event)
            return 

        if (DEBUG_LEVEL & 0xF) > DEBUG_LEVEL_VERBOSE:
            dprint(f"[TERMINAL] Key Pressed: {char_pressed}", color = "yellow")
        self.typed.emit(char_pressed)



    def set_text_color(self, color:QtGui.QColor):
        self.fmt.setForeground(QtGui.QBrush(color))
        self.setCurrentCharFormat(self.fmt)

    def add_text(self, text:str = "", color:QtGui.QColor = COLOR_WHITE):
        self.fmt.setForeground(QtGui.QBrush(color))
        self.moveCursor(QtGui.QTextCursor.MoveOperation.End)
        self.setCurrentCharFormat(self.fmt)
        self.insertPlainText(text)
        vprint(text)

    def focusNextPrevChild(self, next):
        #print(f"focusNextPrevChild {next}")
        return False 
    
    def set_background_color(self, color:QtGui.QColor):
        self.setStyleSheet(f"background-color: {color.name()};")

    def evaluate_escape_sequence(self, escape_sequence:str):
        start_t = time.perf_counter_ns()
        if not escape_sequence:
            return 0 
        if (DEBUG_LEVEL & 0xF) > DEBUG_LEVEL_VERBOSE:
            vprint(f"Evaluating escape sequence: {escape_sequence}", color = "cyan")
        if escape_sequence.startswith("[") and escape_sequence.endswith("m"):
            display_attributes = escape_sequence[1:-1].split(";")
            
            if not display_attributes[0]:
                display_attributes = ['0']
                #dprint("No display attributes", color = "red")
            #dprint(f"display_attributes: {display_attributes}", color = "cyan")
            for attribute in display_attributes:
                if attribute == '0':
                    #print(f"self.fmt {self.fmt.foreground().color().name()} default_fmt {self.default_fmt.foreground().color().name()}")
                    self.clear_formatting()
                elif attribute == '1':
                    self.fmt.setFontWeight(QtGui.QFont.Weight.Bold)
                elif attribute == '2':
                    self.fmt.setFontWeight(QtGui.QFont.Weight.Light)
                elif attribute == '4':
                    self.fmt.setFontUnderline(True)
                elif attribute == '5': ## Blink 
                    pass 
                elif attribute == '7': ## Reverse 
                    pass 
                    ##self.fmt.setForeground(QtGui.QBrush(COLOR_BLACK))
                elif attribute == '8':
                    self.fmt.setForeground(QtGui.QBrush(COLOR_BLACK))
                elif len(attribute) == 2: 
                    if attribute[1] in ESCAPE_COLORS:
                        if attribute[0] == '3':
                            self.fmt.setForeground(QtGui.QBrush(ESCAPE_COLORS[attribute[1]]))
                        elif attribute[0] == '4':
                            self.fmt.setBackground(QtGui.QBrush(ESCAPE_COLORS[attribute[1]]))
            self.setCurrentCharFormat(self.fmt)
            return time.perf_counter_ns() - start_t
        if escape_sequence == "[J":
            vprint("DELETE")
            #self.moveCursor(QtGui.QTextCursor.MoveOperation.End)
            self.textCursor().deletePreviousChar()
            return time.perf_counter_ns() - start_t
            #self.textCursor().deletePreviousChar()
            #vprint(f"fmt: {self.fmt.foreground().color().name()} {self.fmt.background().color().name()}")
                
        

    def clear_formatting(self):
        self.fmt.clearBackground()
        self.fmt.clearForeground()
        self.fmt.clearProperty(QtGui.QTextFormat.Property.FontWeight)
        self.fmt.clearProperty(QtGui.QTextFormat.Property.FontItalic)
        self.fmt.clearProperty(QtGui.QTextFormat.Property.FontUnderline)
        self.fmt.clearProperty(QtGui.QTextFormat.Property.FontStrikeOut)

    def put_chars(self, data: bytes):
        start_t = time.perf_counter_ns() 

        if not self.auto_scroll:
            prev_bar_position = self.verticalScrollBar().value()
        if not self.textCursor().atEnd():
            cursor = self.textCursor()
            now_pos = cursor.position()
            cursor.movePosition(QtGui.QTextCursor.MoveOperation.End)
            self.setTextCursor(cursor)
        mct = time.perf_counter_ns() - start_t
        insert_text_time = 0 
        escape_seq_time = 0 

        if not self.escape_sequence:
            self.set_text_color(COLOR_WHITE)

        if self.format != "UTF-8":
            if self.format == "Hex":
                self.textCursor().insertText(data.hex())
                return
            elif self.format == "Hex+Space":
                self.textCursor().insertText(data.hex(" "))
                return
            elif self.format == "Hex+Newline":
                self.textCursor().insertText(data.hex("\n") + "\n")
                return
            elif self.format == "Bin+Space":
                ## Convert bytes to a string of 8 bit ints separated by spaces
                self.textCursor().insertText(" ".join(f"{byte:08b}" for byte in data))
                return
            elif self.format == "Bin+Newline":
                self.textCursor().insertText("\n".join(f"{byte:08b}" for byte in data) + "\n")
                return
            elif self.format == "Int+Space":
                self.textCursor().insertText(" ".join(f"{byte:d}" for byte in data))
                return
            elif self.format == "Int+Newline":
                self.textCursor().insertText("\n".join(f"{byte:d}" for byte in data) + "\n")
                return

        text_buffer = ""
        if b"\x1B" in data or self.escape_sequence:
            start_index = 1 
            if self.escape_sequence:
                data = self.escape_sequence + data
                self.escape_sequence = None 
                start_index = 0 
                
            chunks = data.split(b"\x1B")
            if not self.escape_sequence:
                self.insertPlainText(chunks[0].decode("utf-8", errors = "replace"))
            
            for chunk in chunks[start_index:]:
                if (DEBUG_LEVEL & 0xF) > DEBUG_LEVEL_VERBOSE:
                    vprint(f"chunk: {chunk}", color = "yellow")
                if not chunk: continue 
                split_index = 0
                for i, byte in enumerate(chunk):
                    if byte in ESCAPE_SEQUENCE_TERMINATORS:
                        split_index = i + 1
                        escape_seq_time += self.evaluate_escape_sequence(chunk[:split_index].decode("utf-8", errors = "replace"))
                        break 
                if not split_index: ## Escape sequence not terminated
                    self.escape_sequence = chunk
                    continue 

                t = chunk[split_index:].decode("utf-8", errors = "replace")
                text_buffer_start = time.perf_counter_ns()
                
                self.textCursor().insertText(t)
                insert_text_time += time.perf_counter_ns() - text_buffer_start
                if (DEBUG_LEVEL & 0xF) >= DEBUG_LEVEL_VERBOSE:
                    vprint(t, end = "", flush = True)
            # for byte in data:
            #     c = chr(byte)
            #     if self.escape_buffer is not None:
            #         self.escape_buffer += c
            #         if chr(byte) in ESCAPE_SEQUENCE_TERMINATORS:
            #             if text_buffer:
            #                 text_buffer_start = time.perf_counter_ns()
            #                 self.textCursor().insertText(text_buffer)
            #                 self.insertPlainText(text_buffer)
            #                 insert_text_time += time.perf_counter_ns() - text_buffer_start

            #                 if DEBUG_LEVEL > 1:
            #                     vprint(text_buffer, end = "", flush = True)
            #                 text_buffer = ""
            #             self.evaluate_escape_sequence(self.escape_buffer)
            #             self.escape_buffer = None
            #         continue 
            #     if byte == 27:
            #         self.escape_buffer = ""
            #         continue 
            #     elif byte not in [7, 8]:
            #         text_buffer += c
        else: 
            text_buffer = data.decode("utf-8", errors = "replace")
            #text_buffer = text_buffer.replace("\x07", "").replace("\x08", "")
        if text_buffer:
            insert_text_start = time.perf_counter_ns()
            #self.moveCursor(QtGui.QTextCursor.MoveOperation.End)
            self.textCursor().insertText(text_buffer)
            insert_text_time += time.perf_counter_ns() - insert_text_start
            if (DEBUG_LEVEL & 0xF) >= DEBUG_LEVEL_VERBOSE:
                vprint(text_buffer, end = "", flush = True)
            
        if self.auto_scroll:
            self.ensureCursorVisible()
        else: 
            self.verticalScrollBar().setValue(prev_bar_position)
        

        if DEBUG_LEVEL & 128:    
            
            
            #vprint(f"insertPlainText {(time.perf_counter_ns() - insert_text_start) / 1000} us", color = 'green')
            cprint(f"put_chars {(time.perf_counter_ns() - start_t) / 1000} us Insert: {insert_text_time / 1000} us Escape: {escape_seq_time / 1000} us mct {mct / 1000} us Len: {len(data)} Blocks: {self.blockCount()}", color = 'magenta')
            
            #vprint(f"data: {data}", color = 'yellow')


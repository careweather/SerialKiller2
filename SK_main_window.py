from PyQt6 import QtCore, QtGui, QtWidgets
from PyQt6.QtWidgets import QApplication
from SK_commands import Command, Option
from PyQt6.QtCore import QThread
from GUI_SK2_MAIN_WINDOW import Ui_MainWindow
import sys
import serial
import time
import json
import re
import math
import shutil
import datetime
import shutil
import subprocess
from SK_scripting import ScriptWorker
from SK_ScriptSyntaxHighlighter import ScriptSyntaxHighlighter
from SK_common import *
from SK_help import *
from SK_widgets import *
from SK_serial_worker import *
from SK_logger import *
from SK_text_popup import *
from SK_terminal import *
from SK_extensions import SK_Extension
import numpy as np
import importlib
from SK_key_popup import KeyPopup

sys.path.append(DEFAULT_EXTENSION_PATH)


PARITIES = {"NONE": serial.PARITY_NONE, "EVEN": serial.PARITY_EVEN, "ODD": serial.PARITY_ODD, "MARK": serial.PARITY_MARK, "SPACE": serial.PARITY_SPACE}


class MainWindow(QtWidgets.QMainWindow, Ui_MainWindow):
    history = [""]
    history_index = 1
    ports = {}
    current_port: SK_Port = None
    last_connected_port = None
    auto_reconnect_port = None
    settings_saved = True
    save_delay = 2000  ## Time in ms to wait before saving settings
    current_settings = {"last_opened_script": None, "user_expressions": {}, "key_commands": {}, "aliases": {}}

    script_thread: QThread = None
    script_worker: ScriptWorker = None

    serial_worker: SerialWorker = None
    serial_thread: QThread = None

    extension_worker: SK_Extension = None
    extension_thread: QThread = None
    extension_active = False

    logger: SK_Logger = None
    init_done = False

    ext_debug_level = 0
    extension_module = None

    last_escape_time = 0

    outgoing_fmt = "UTF-8"
    incoming_fmt = "UTF-8"

    key_popup: KeyPopup = None 
    port_aliases = {}

    external_text_editor_options = {
        "Built-in": {"call": None, "args": ""},
        "gedit": {"call": "gedit", "args": "-s __FILE__"},
        "VSCode": {"call": "code", "args": " __PATH__ __FILE__"},
        "notepad": {"call": "notepad", "args": "__FILE__"},
        "notepad++": {"call": "notepad-plus-plus", "args": "__FILE__"},
        "Custom": {"call": None, "args": ""},
    }

    key_popup: KeyPopup = None

    def __init__(self, *args, open_commands=[], **kwargs):
        super().__init__(*args, **kwargs)
        self.setupUi(self)
        setComboBox_items(self.comboBox_baud, serial.Serial.BAUDRATES)
        setComboBox_items(self.comboBox_parity, PARITIES)
        self.save_timer = QtCore.QTimer()
        self.last_save_time = time.perf_counter()
        self.setWindowTitle("Serial Killer")
        self.determine_log_open_options()
        self.settings_create()
        self.recall_settings()
        self.label_status_bar = QtWidgets.QLabel("TEST")
        self.label_status_bar.setSizePolicy(QtWidgets.QSizePolicy.Policy.MinimumExpanding, QtWidgets.QSizePolicy.Policy.Expanding)
        #self.label_status_bar.setWordWrap(True)
        self.label_status_bar.setTextFormat(QtCore.Qt.TextFormat.PlainText)
        self.label_status_bar.setFont(QtGui.QFont("Monospace", 8))

        self.statusBar().addWidget(self.label_status_bar)
        self.connect_ui()

        self.cmd_list = [
            Command("help", self.print_help, options=[Option(("-a", "--all"), type=str, default=None), Option(("-l", "--list"), type=int, default=[])]),
            #Command("quit", self.make_quit, []),
            Command("exit", self.make_quit, []),
            Command("clear", self.clear_terminal, []),
            Command("ports", self.list_ports, []),
            
            Command(
                "con",
                self.serial_connect,
                [
                    Option(("-b", "--baud")),
                    Option(("-p", "--parity")),
                    Option(("-r", "--rtscts")),
                    Option(("-x", "--xonxoff")),
                    Option(("-d", "--dsrdtr")),
                    Option(("-h", "--help")),
                ],
            ),
            Command("dcon", self.serial_disconnect, []),
            Command(
                "settings",
                self.settings_command,
                [
                    Option(("--save", "-s")),
                    Option(("--load", "-l")),
                    Option(("--list", "-ls")),
                    Option(("-h", "--help")),
                ],
            ),
            Command(
                "plot",
                self.plot_command,
                [
                    Option(("-h", "--help")),
                    Option(("-p", "--points")),
                    Option(("-k", "--keys")),
                    Option(("-s", "--seps")),
                    Option(("-r", "--refs")),
                    Option(("-l", "--limits")),
                    Option(("-t", "--title")),
                    Option(("--export", "-e", "export")),
                    Option(("--open",)),
                    Option(("--round",)),
                    Option(("--size",), default=[]),
                    Option(("--header",)),
                    Option(("--time-fmt",)),
                    Option(("--popup",)), 
                ],
            ),
            Command(
                "log",
                self.log_command,
                [
                    Option(("-h", "--help")),
                    Option(("-o", "--open", "open")),
                    Option(("-s", "--save", "save")),
                    Option(("-n", "--new", "new")),
                    Option(("-ls", "--list")),
                    Option(("on", "--on")),
                    Option(("off", "--off")),
                    Option(("--line-fmt",)),
                    Option(("--time-fmt",)),
                ],
            ),
            Command(
                "script",
                self.script_command,
                [
                    Option(("-o", "--open")),
                    Option(("-h", "--help")),
                    Option(("-s", "--save")),
                    Option(("-n", "--new")),
                    Option(("-d", "--delay")),
                    Option(("-t", "--tab")),
                    Option(("-ls", "--list", "list")),
                ],
            ),
            Command(
                "cowsay",
                self.cowsay,
                [
                    Option(("-p", "--pink")), 
                    Option(("-n", "--nerd")),
                    Option(("-d", "--dead")),
                ],
            ),
            Command("sk-set", self.sk_set, []),
            Command("sk-info", self.sk_info, []),
            Command("sk-open", 
                    self.sk_open, 
                    [Option(("-h", "--help")), 
                     Option(("-e", "--ext"), type=str, default=None),
                     Option(("-d", "--dir"), type=str, default=None),
                     ]
                    ),
            Command(
                "key",
                self.key_command,
                [
                    Option(("-ls", "--list")),
                    Option(("-h", "--help")),
                    Option(("--clear", "clear")),
                    Option(("--save", "-s"), type=str, default=None),
                ],
            ),
            Command(
                "alias",
                self.port_alias,
                [
                    Option(("-ls", "--list")),
                    Option(("-h", "--help")),
                    #Option(("--clear", "clear")),
                ],
            ),
            Command(
                "ext",
                self.extension_command,
                [
                    Option(("list", "-ls")),
                    Option(("-h", "--help")),
                    Option(("open", "--open", "-o")),
                    Option(("run", "--run", "-r")),
                    Option(("stop", "--stop", "-s", "end")),
                    Option(("cmd", "--cmd", "-c"), default=[]),
                    Option(("new", "--new", "-n")),
                    Option(("--debug", "-d"), default=1),
                ],
            ),
            
        ]

        self.log_configure()

        if self.current_settings["last_opened_script"]:
            self.open_script(self.current_settings["last_opened_script"])
        self.start_rescan_worker()
        self.update_ports(get_ports())
        self.script_highlighter = ScriptSyntaxHighlighter(self.textEdit_script)

        self.update_status_bar()
        self.tabWidget.setCurrentIndex(0)
        self.lineEdit_send.setFocus()
        self.log_config_changed()

        

        if open_commands:
            while open_commands:
                open_command = open_commands.pop(0)
                dprint(f"Opening with command: {open_command}", color="yellow")
                self.send_clicked(open_command, append_to_history=True)
                time.sleep(0.01)

        self.terminal.auto_scroll = self.checkBox_auto_scroll.isChecked()

        self.wrap_text_toggled()
        self.extension_debug_level_changed(0)
        self.init_time = time.time()
        # self.statusBar().setFont(QtGui.QFont("Monospace"))
        # print(self.statusBar().font().family())

        self.update_status_bar()
        # time.sleep(0.2)
        self.pushButton_save_as_script.setStyleSheet(STYLESHEET_BUTTON_DEFAULT)
        self.textEdit_script.textChanged.connect(self.script_edited)


        #####################################################################################
        self.init_done = True  ## THIS MUST BE THE LAST LINE OF __INIT__ ###
        #####################################################################################

    def connect_ui(self):

        self.terminal.setPlaceholderText(TERMINAL_PLACEHOLDER)

        self.textEdit_script.setTabStopDistance(20)
        # self.textEdit_script.
        self.tableWidget_expressions.itemChanged.connect(self.user_expressions_edited)
        self.tableWidget_keys.itemChanged.connect(self.key_commands_edited)
        self.tableWidget_expressions.horizontalHeader().setStretchLastSection(True)
        self.tableWidget_keys.horizontalHeader().setStretchLastSection(True)
        self.tableWidget_expressions.horizontalHeader().show()

        self.groupBox_settings_terminal.setChecked(False)
        self.groupBox_settings_scripts.setChecked(False)
        self.groupBox_settings_commands.setChecked(False)
        self.groupBox_settings_port.setChecked(False)
        self.groupBox_settings_plot.setChecked(False)
        self.groupBox_settings_extensions.setChecked(False)
        ## PUSH BUTTONS
        self.pushButton_connect.setStyleSheet(STYLESHEET_BUTTON_INACTIVE)
        self.pushButton_connect.clicked.connect(self.connect_clicked)
        self.pushButton_clear.clicked.connect(self.clear_terminal)
        self.pushButton_send.clicked.connect(self.send_clicked)
        self.pushButton_plot_start.clicked.connect(self.plot_start_pause_clicked)
        self.pushButton_plot_start.setStyleSheet(STYLESHEET_BUTTON_GREEN)
        self.pushButton_plot_reset.clicked.connect(self.plot_reset)
        self.pushButton_select_log.clicked.connect(self.log_directory_select_clicked)
        self.pushButton_default_log_name.clicked.connect(lambda: self.lineEdit_default_log_name.setText(DEFAULT_LOG_NAME))
        self.pushButton_default_log_line_format.clicked.connect(lambda: self.lineEdit_log_line_format.setText(DEFAULT_LOG_FORMAT))
        self.pushButton_default_time_format.clicked.connect(lambda: self.lineEdit_log_time_format.setText(DEFAULT_TIME_FORMAT))
        self.pushButton_run_script.clicked.connect(self.run_script_clicked)
        self.pushButton_run_script.setStyleSheet(STYLESHEET_BUTTON_GREEN)
        self.pushButton_clear_table.clicked.connect(lambda: self.key_command(**{"--clear": None}))
        # self.pushButton_restart_logger.clicked.connect(lambda: self.log_start(force_reconfigure=True))
        self.pushButton_plot_export.clicked.connect(self.plot_export)
        self.pushButton_plot_export.setEnabled(False)
        self.pushButton_open_script.clicked.connect(self.open_script)
        self.pushButton_load_settings.clicked.connect(lambda: self.settings_command(**{"--load": None}))
        self.pushButton_save_settings_as.clicked.connect(lambda: self.settings_command(**{"--save": None}))
        self.pushButton_set_max_lines.clicked.connect(self.max_lines_set_pressed)
        self.pushButton_launch_key_popup.clicked.connect(self.launch_plot_popup)
        self.pushButton_export_script.clicked.connect(self.key_export_script)

        ## CHECK BOXES
        self.checkBox_auto_reconnect.stateChanged.connect(self.autoreconnect_clicked)
        self.checkBox_auto_scroll.stateChanged.connect(self.autoscroll_clicked)
        self.checkBox_wrap_text.stateChanged.connect(self.wrap_text_toggled)
        self.checkBox_auto_log.stateChanged.connect(self.auto_log_toggled)
        self.comboBox_incoming_fmt.currentTextChanged.connect(self.incoming_fmt_changed)
        self.comboBox_outgoing_fmt.currentTextChanged.connect(self.outgoing_fmt_changed)

        ## LINE EDIT
        self.lineEdit_send.returnPressed.connect(self.send_clicked)
        self.lineEdit_send.setPlaceholderText("SEND to device OR COMMAND")
        self.lineEdit_key_ctrl.setPlaceholderText("Key ctrl")
        self.lineEdit_key_ctrl.keyPress.connect(self.key_command_keypressed)
        self.lineEdit_log_line_format.textChanged.connect(self.log_config_changed)
        self.lineEdit_log_time_format.textChanged.connect(self.log_config_changed)
        self.lineEdit_default_log_name.textChanged.connect(self.log_config_changed)
        self.lineEdit_rescan_interval.setValidator(QtGui.QIntValidator(0, 2147483647))
        self.lineEdit_rescan_interval.textChanged.connect(self.auto_rescan_interval_changed)
        self.lineEdit_max_lines.setValidator(QtGui.QIntValidator(0, 2147483647))
        self.lineEdit_max_lines.textChanged.connect(self.max_lines_edited)
        

        self.terminal.typed.connect(self.terminal_typed)

        ## ACTIONS
        self.action_script_open.triggered.connect(self.open_script)
        self.action_script_save.triggered.connect(lambda: self.save_script(save_as=False))
        self.action_script_save_as.triggered.connect(lambda: self.save_script(save_as=True))
        self.action_script_run.triggered.connect(self.run_script_clicked)
        self.action_script_new.triggered.connect(lambda: self.script_command(**{"-n": None}))
        self.action_log_open.triggered.connect(self.log_open)
        self.action_log_open_current.triggered.connect(lambda: self.log_open(latest=True))
        self.action_log_save_current.triggered.connect(lambda: self.log_command(**{"-s": None}))
        self.action_log_new.triggered.connect(lambda: self.log_command(**{"-n": None}))
        self.action_settings_load.triggered.connect(lambda: self.settings_command(**{"--load": None}))
        self.action_settings_save_as.triggered.connect(lambda: self.settings_command(**{"--save": None}))
        self.action_extension_load.triggered.connect(lambda: self.extension_command(**{"run": None}))
        self.action_extension_stop.triggered.connect(lambda: self.extension_command(**{"stop": None}))
        self.action_extension_edit.triggered.connect(self.extension_open)
        self.action_extension_new.triggered.connect(self.extension_new)
        self.action_help_open_help.triggered.connect(self.print_help)

        

        self.action_ext_debug_0.triggered.connect(lambda: self.extension_debug_level_changed(0))
        self.action_ext_debug_1.triggered.connect(lambda: self.extension_debug_level_changed(1))
        self.action_ext_debug_2.triggered.connect(lambda: self.extension_debug_level_changed(2))
        self.action_ext_debug_3.triggered.connect(lambda: self.extension_debug_level_changed(3))

        
        
        self.statusBar().messageChanged.connect(self.statusBar_changed)

    def statusBar_changed(self, text: str):
        dprint(f"statusBar_changed: {text}", color="yellow")

    def keyPressEvent(self, event: QtGui.QKeyEvent):
        if DEBUG_LEVEL & 0xF > DEBUG_LEVEL_VERBOSE:
            cprint(event_to_string(event), color="cyan")
        if self.lineEdit_send.hasFocus():
            if event.key() == QtCore.Qt.Key.Key_Up:
                self.scroll_history(scroll_down=False)
            elif event.key() == QtCore.Qt.Key.Key_Down:
                self.scroll_history(scroll_down=True)
        if event.key() == QtCore.Qt.Key.Key_Escape:
            if self.script_worker:
                if self.script_worker.active:
                    self.script_cancel()
            if self.extension_active:
                if time.time() - self.last_escape_time < 1:
                    self.extension_request_end()
                else:
                    self.last_escape_time = time.time()
            self.lineEdit_send.setFocus()
        if event.modifiers() == QtCore.Qt.KeyboardModifier.AltModifier:
            if event.key() == QtCore.Qt.Key.Key_Right:
                self.shift_tab(1)
            elif event.key() == QtCore.Qt.Key.Key_Left:
                self.shift_tab(-1)
        else:
            super().keyPressEvent(event)

    def shift_tab(self, shift=1):
        current_tab = self.tabWidget.currentIndex()
        current_tab += shift
        if current_tab < 0:
            current_tab = 0
        elif current_tab >= self.tabWidget.count():
            current_tab = self.tabWidget.count() - 1
        self.tabWidget.setCurrentIndex(current_tab)

    def print_help(self, *args, **kwargs):
        # i = int(kwargs)
        dprint(f"Help Command: {args} {kwargs}")
        
        # help_filepath = os.path.join(BASE_DIR, "help.html")
        open_text_popup(self, file=DEFAULT_HELP_PATH, style_path=DEFAULT_HELP_STYLE_PATH)

    def clear_terminal(self):
        self.set_debug_text("")
        self.terminal.clear()

    def auto_rescan_interval_changed(self, interval: str):
        dprint(f"Auto Rescan Interval Changed: {interval}")
        try: 
            interval = int(interval)
            self.rescan_worker.update_interval = interval 
            self.lineEdit_rescan_interval.setStyleSheet(STYLESHEET_LINE_EDIT_DEFAULT)
        except Exception as E:
            self.lineEdit_rescan_interval.setStyleSheet(STYLESHEET_LINE_EDIT_ERROR)
            eprint(E)

    def evaluate_input_text(self, text: str):
        if self.current_settings["user_expressions"] and self.checkBox_allow_expressions.isChecked():
            for key, value in self.current_settings["user_expressions"].items():
                if key in text:
                    text = text.replace(key, value)

        if self.checkBox_allow_expressions.isChecked():
            found_expressions = re.findall(r"\$\{(.*?)\}", text)
            for expression in found_expressions:
                try:
                    if not expression:
                        text = text.replace("${}", "")
                        continue
                    expression_resp = str(eval(expression))
                    text = text.replace(f"${{{expression}}}", expression_resp, 1)
                    vprint(f"EXPRESSION ${{{expression}}} = {expression_resp}", color="green")
                except Exception as E:
                    eprint(E)
                    self.terminal_add_text(f"ERR IN EXPR: ${{{expression}}} {str(E)}", type=TYPE_ERROR)
                    return None
        # if self.checkBox_allow_commands.isChecked():
        #     for cmd in self.cmd_list:
        #         is_cmd, error = cmd.execute(text)
        #         if is_cmd:
        #             if error:
        #                 self.terminal_add_text(error, type=TYPE_ERROR)
        #             return None
        return text

    def user_expressions_edited(self):
        if self.tableWidget_expressions.currentRow() == self.tableWidget_expressions.rowCount() - 1:
            if not self.tableWidget_expressions.currentItem():
                return
            self.tableWidget_expressions.setRowCount(self.tableWidget_expressions.rowCount() + 1)
        self.current_settings["user_expressions"] = get_table_items(self.tableWidget_expressions)
        vprint(self.current_settings["user_expressions"], color="green")
        self.settings_save(update_all=False)

    def execute_command(self, text: str):
        """Returns None if a command is executed, else returns original text"""
        if self.checkBox_allow_commands.isChecked():
            cmd_start_index = 0
            cmd_char = self.lineEdit_command_char.text()
            if cmd_char:
                if text.startswith(cmd_char):
                    cmd_start_index = len(cmd_char)
                else:
                    return text
            for cmd in self.cmd_list:
                is_cmd, error = cmd.execute(text[cmd_start_index:])
                if is_cmd:
                    if error:
                        self.terminal_add_text(error, type=TYPE_ERROR)
                    return None
        return text

    def scroll_history(self, scroll_down=True):
        if scroll_down:
            if len(self.history) > 0:
                self.history_index -= 1
                if self.history_index < 0:
                    self.history_index = 0
            else:
                return
        else:
            self.history_index += 1
            if self.history_index >= len(self.history):
                self.history_index = len(self.history)
                self.lineEdit_send.clear()
                return

        self.lineEdit_send.setText(self.history[self.history_index])

    def append_to_history(self, text: str):
        if not text:
            return
        self.history_index = 0
        if len(self.history) > 1 and self.history[1] == text:
            return
        self.history.insert(1, text)

    def send_clicked(self, input: str = None, append_to_history: bool = True):
        if input is None or input == False:
            input = self.lineEdit_send.text()
            self.lineEdit_send.clear()
        if append_to_history:
            self.append_to_history(input)

        input = self.evaluate_input_text(input)
        if input == None:
            return
        input = self.execute_command(input)
        if input == None:
            return
        if self.outgoing_fmt == "UTF-8":
            text = replace_control_chars(self.lineEdit_prepend.text())
            text += input
            text += replace_control_chars(self.lineEdit_append.text())
            self.serial_send(text)
            self.terminal_add_text(self.lineEdit_prepend_tx.text() + text, type=TYPE_TX)
        elif self.outgoing_fmt == "Int":
            send = bytes(replace_control_chars(self.lineEdit_prepend.text()), "utf-8")
            tokens = char_split(input, " ,;")
            try: 
                for token in tokens:
                    send += bytes([int(token)])
                send += bytes(replace_control_chars(self.lineEdit_append.text()), "utf-8")
            except Exception as E:
                eprint(E)
                self.terminal_add_text(f"ERR IN INT: {input} {str(E)}", type=TYPE_ERROR)
                return
            self.serial_send(send)
            self.terminal_add_text(self.lineEdit_prepend_tx.text() + send.decode("utf-8"), type=TYPE_TX)
            vprint(send, color="cyan")
        elif self.outgoing_fmt == "Hex":
            send = bytes(replace_control_chars(self.lineEdit_prepend.text()), "utf-8")
            try: 
                send += bytes.fromhex(input)
                send += bytes(replace_control_chars(self.lineEdit_append.text()), "utf-8")
            except Exception as E:
                eprint(E)
                self.terminal_add_text(f"ERR IN HEX: {input} {str(E)}", type=TYPE_ERROR)
                return
            self.serial_send(send)
            self.terminal_add_text(self.lineEdit_prepend_tx.text() + send.decode("utf-8"), type=TYPE_TX)
            vprint(send, color="cyan")
        # print(text)
        # self.lineEdit_send.clear()
        
        # self.terminal.add_text("ok\n", COLOR_GREEN)

    def terminal_typed(self, text: str):
        self.serial_send(text)
        # self.lineEdit_send.clear()
        # self.terminal_add_text(self.lineEdit_prepend_tx.text() + text, type=TYPE_TX)

    def receive_lines(self, lines: list[str]):
        # return
        if (DEBUG_LEVEL & 0xF) >= DEBUG_LEVEL_VERBOSE:
            vprint(f"recieve_lines: {lines}", color="blue")
        if self.extension_active:
            try:
                self.extension_worker._receive_lines(lines)
            except Exception as e:
                self.terminal_add_text(f"Error in extension receive_lines: {e}", type=TYPE_ERROR)
        for line in lines:
            self.receive_line(line)

    def receive_line(self, line: str):
        if self.plot.type is not None:
            self.plot.update(line)
        if self.checkBox_log_rx.isChecked():
            self.logger.write_line(line)

    def set_debug_text(self, *args, color: QColor = None):
        text = " ".join(args)
        if color:
            style = f"font-size: 13px; color: {color_to_style_sheet(color)}; font-weight: bold;"
            self.label_debug.setStyleSheet(style)
        else:
            self.label_debug.setStyleSheet("font-size: 13px; font-weight: bold;")

        self.label_debug.setText(text)

    def update_status_bar(self):
        text = "Port: "
        if ser.is_open:
            text += ser.port
        else:
            text += "None"

        text += f' | Auto: {self.auto_reconnect_port} | Saved: {"Y" if self.settings_saved else "N"}'
        text += f' | Script: {"Y" if self.script_worker and self.script_worker.active else "N"}'
        text += f' | Plot: {"Y" if self.plot.type is not None and self.plot.active else "N"} '
        if self.logger is not None:
            text += f' | Log: {"Y" if self.logger.active else "N"}'
        text += f' | Ext: {"Y" if self.extension_active else "N"}'

        self.label_status_bar.setText(text)
        #self.statusBar().showMessage(text)

    def wrap_text_toggled(self, val: bool = None):
        if val is None:
            val = self.checkBox_wrap_text.isChecked()
        dprint(f"wrap_text_toggled: {val}", color="yellow")
        if val:
            # print(QtWidgets.QTextEdit.LineWrapMode.WidgetWidth.name)
            self.terminal.setLineWrapMode(self.terminal.LineWrapMode.WidgetWidth)
        else:
            self.terminal.setLineWrapMode(self.terminal.LineWrapMode.NoWrap)

    def autoscroll_clicked(self, state):
        if state:
            self.terminal.auto_scroll = True
        else:
            self.terminal.auto_scroll = False

    def incoming_fmt_changed(self, fmt: str):
        vprint(f"incoming_fmt_changed: {fmt}")
        self.incoming_fmt = fmt
        self.terminal.format = fmt


    def outgoing_fmt_changed(self, fmt: str):
        vprint(f"outgoing_fmt_changed: {fmt}")
        self.outgoing_fmt = fmt


    def max_lines_edited(self, text:str = None):
        if text is None:
            text = self.lineEdit_max_lines.text()

        self.pushButton_set_max_lines.setStyleSheet(STYLESHEET_BUTTON_GREEN)

    def max_lines_set_pressed(self):
        text = self.lineEdit_max_lines.text()
        if not text:
            text = "0"
        lines = int(text)
        if lines == 0:
            vprint("set max terminal lines: infinite")
            self.terminal.setMaximumBlockCount(0)
        else:
            vprint(f"set max terminal lines: {lines}")
            self.terminal.setMaximumBlockCount(lines)
        self.pushButton_set_max_lines.setStyleSheet(STYLESHEET_BUTTON_DEFAULT)

    def autoreconnect_clicked(self, state):
        if state:
            if ser.is_open:
                print(self.ports)
                for port in self.ports:
                    if port == ser.port:
                        self.auto_reconnect_port = port.__dict__[self.comboBox_auto_reconnect_on.currentText()]
                        break
        else:
            self.auto_reconnect_port = None
        self.update_status_bar()

    def connect_clicked(self):
        vprint("connect_clicked", ser.is_open)
        if ser.is_open:
            self.serial_disconnect()
        else:
            self.serial_connect()

    def terminal_evaluate_escape_sequence(self, sequence: str):
        self.terminal.evaluate_escape_sequence(sequence)
        if self.serial_worker is not None:
            self.serial_worker.main_busy = False

    def terminal_add_text(self, text: str, type: int = TYPE_RX):
        if not self.checkBox_auto_scroll.isChecked():
            prev_bar_position = self.terminal.verticalScrollBar().value()
        self.terminal.moveCursor(QtGui.QTextCursor.MoveOperation.End)

        type_src = type & 0x07
        color_config = type & 0x78  ## selects only color bits
        color = COLOR_MODIFIERS[color_config]
        self.terminal.set_text_color(color)

        if type_src == TYPE_SRC_RX:  ## Incoming FROM device...
            # self.terminal.set_text_color(COLOR_WHITE)
            vprint("<", text.replace("\r", ""), ">", color="white", end="", sep="", flush=True)
            self.terminal.insertPlainText(text)
        elif type_src == TYPE_SRC_TX:  ## Outgoing TO device...
            vprint(text.replace("\r", ""), color="cyan", end="", sep="", flush=True)
            # self.terminal.set_text_color(COLOR_LIGHT_BLUE)
            self.terminal.insertPlainText(text)
            self.terminal.clear_formatting()
            if self.checkBox_log_tx.isChecked():
                self.logger.write(text)
        elif type_src == TYPE_SRC_INFO:  ## Informational...
            text = self.lineEdit_prepend_info.text() + text.replace("\n", "\n" + self.lineEdit_prepend_info.text()) + "\n"
            # self.terminal.set_text_color(color)
            self.terminal.insertPlainText(text)
            self.terminal.clear_formatting()
            vprint(text, color="yellow", end="")
            if self.checkBox_log_info.isChecked():
                self.logger.write(text)

        elif type_src == TYPE_SRC_ERROR:  ## Error...
            text = self.lineEdit_prepend_error.text() + text.replace("\n", "\n" + self.lineEdit_prepend_error.text()) + "\n"
            # self.terminal.set_text_color(color)
            self.terminal.insertPlainText(text)
            self.terminal.clear_formatting()
            eprint(text, color="red", end="")
            if self.checkBox_log_error.isChecked():
                self.logger.write(text)

        if not self.checkBox_auto_scroll.isChecked():
            self.terminal.verticalScrollBar().setValue(prev_bar_position)
        else:
            self.terminal.ensureCursorVisible()

        if self.serial_worker is not None:
            self.serial_worker.main_busy = False

    def terminal_add_bytes(self, bytes: bytes):
        self.terminal.put_chars(bytes)

    ############################################################
    ################### SERIAL FUNCTIONS #######################
    ############################################################

    def serial_connect(self, *args, **kwargs):

        if "-h" in kwargs:
            self.terminal_add_text(CONNECT_HELP, TYPE_INFO)
            return

        if ser.is_open:
            if args or kwargs:
                self.serial_disconnect()
            else:
                self.set_debug_text("Already Connected", color=COLOR_LIGHT_YELLOW)
                return
        if ser.is_open:
            self.set_debug_text("Cannot Disconnect!", color=COLOR_RED)
            return

        port: SK_Port = None
        baud = None
        parity = None
        rtscts = None
        xonxoff = None
        dsrdtr = None
        for index, arg in enumerate(args):
            if index == 0:
                port = find_serial_port(arg, self.ports)
                if port is None:
                    self.set_debug_text(f"Port '{arg}' not found", color=COLOR_RED)
                    return

            elif index == 1:
                kwargs["-b"] = arg
                break

        if port == None:
            port = find_serial_port(self.comboBox_port.currentText(), self.ports)
            if port == None:
                self.set_debug_text("Invalid Port", color=COLOR_RED)
                return

        if "-b" in kwargs:
            if kwargs["-b"] not in getComboBox_items(self.comboBox_baud):
                self.terminal_add_text(f"Invalid Baud Rate: {kwargs['-b']}", type=TYPE_ERROR)
                return
            self.comboBox_baud.setCurrentText(kwargs["-b"])
            baud = int(kwargs["-b"])
        else:
            baud = int(self.comboBox_baud.currentText())

        if "-p" in kwargs:
            if kwargs["-p"] not in PARITIES:
                self.set_debug_text(f"Invalid Parity: {kwargs['-p']}", color=COLOR_RED)
                return
            parity = PARITIES[kwargs["-p"]]
        else:
            parity = PARITIES[self.comboBox_parity.currentText()]

        if "-r" in kwargs:
            rtscts = bool(kwargs["-r"])
            self.checkBox_rtscts.setChecked(rtscts)
        else:
            rtscts = self.checkBox_rtscts.isChecked()

        if "-x" in kwargs:
            xonxoff = bool(kwargs["-x"])
            self.checkBox_xonxoff.setChecked(xonxoff)
        else:
            xonxoff = self.checkBox_xonxoff.isChecked()

        if "-d" in kwargs:
            dsrdtr = bool(kwargs["-d"])
            self.checkBox_dsrdtr.setChecked(dsrdtr)
        else:
            dsrdtr = self.checkBox_dsrdtr.isChecked()

        dprint(f"Connecting to {port}", color="yellow")

        ser.rtscts = rtscts
        ser.xonxoff = xonxoff
        ser.dsrdtr = dsrdtr
        ser.baudrate = baud
        ser.parity = parity
        ser.port = port.Device

        self.last_connected_port = port.Device
        self.current_port = port

        ser.close()
        ser.open()
        ser.set_low_latency_mode(True)

        if not ser.is_open:
            self.set_debug_text(f"Failed to connect to {port}", color=COLOR_RED)
            return

        dprint("Connected!", color="green")
        self.set_debug_text(f"Connected to {port}", color=COLOR_GREEN)
        self.terminal_add_text(f"Connected to {port} at {baud} baud", type=TYPE_INFO_GREEN)
        # self.terminal.add_text(f"Connected to {port} at {baud} baud\n", color = COLOR_GREEN)

        if self.checkBox_auto_reconnect.isChecked():
            self.auto_reconnect_port = port.__dict__[self.comboBox_auto_reconnect_on.currentText()]

        ## UI CHANGES
        self.terminal.set_background_color(COLOR_BLACK)
        self.pushButton_connect.setStyleSheet(STYLESHEET_BUTTON_ACTIVE)
        self.pushButton_connect.setText("Disconnect")
        self.comboBox_baud.setEnabled(True)
        self.comboBox_parity.setEnabled(True)
        self.checkBox_rtscts.setEnabled(True)
        self.checkBox_xonxoff.setEnabled(True)
        self.checkBox_dsrdtr.setEnabled(True)
        self.pushButton_send.setStyleSheet(STYLESHEET_BUTTON_GREEN)

        self.comboBox_port.setCurrentText(str(port))
        self.logger.set_serial_port(self.current_port)

        ## START SERIAL WORKER
        self.serial_thread = QThread()
        self.serial_worker = SerialWorker()
        self.serial_worker.moveToThread(self.serial_thread)
        self.serial_thread.started.connect(self.serial_worker.run)
        # self.serial_worker.line.connect(self.recieve_line)
        # self.serial_worker.escape_sequence.connect(self.terminal.evaluate_escape_sequence)
        # self.serial_worker.text.connect(self.terminal_add_text)
        self.serial_worker.lines.connect(self.receive_lines)
        self.serial_worker.raw.connect(self.terminal.put_chars)
        self.serial_worker.error.connect(self.serial_error)
        # self.serial_worker.output.connect(self.terminal_add_text)
        # self.serial_worker.raw.connect(self.terminal.put_chars)
        self.serial_thread.start(QThread.Priority.HighPriority)
        self.serial_worker.main_busy = False

        if self.extension_active:
            try:
                self.extension_worker._serial_connected(self.current_port)
            except Exception as e:
                self.terminal_add_text(f"Error in extension serial_connected: {e}", type=TYPE_ERROR)

        self.update_status_bar()

    def serial_send(self, text: str | bytes):
        if not ser.is_open:
            self.set_debug_text("Warning: Not Connected", color=COLOR_LIGHT_YELLOW)
            return
        try:
            ser.flush()
            if isinstance(text, bytes):
                ser.write(text)
            else:
                ser.write(text.encode("utf-8"))
        except Exception as e:
            self.terminal_add_text(f"Error in serial_send: {e} Text: {text}", type=TYPE_ERROR)
            # eprint(f"Error in serial_send: {e} Text: {text}", color = "red")

    def serial_disconnect(self, *args, intentional=True, **kwargs):
        dprint("serial_disconnect. intentional = ", intentional, color="yellow")
        if not ser.is_open:
            if intentional:
                self.set_debug_text("Already Disconnected", color=COLOR_LIGHT_YELLOW)
            return

        if intentional:
            self.auto_reconnect_port = None
            # self.terminal_add_text("Auto Reconnect Disabled", type = TYPE_INFO)
            pass

        self.serial_worker.stop()
        time.sleep(0.02)
        self.serial_thread.exit()

        ser.cancel_read()
        ser.cancel_write()
        time.sleep(0.01)
        ser.close()

        ## UI CHANGES
        self.terminal.set_background_color(COLOR_DARK_GREY)
        self.set_debug_text("Disconnected", color=COLOR_LIGHT_YELLOW)
        self.terminal_add_text("Disconnected", type=TYPE_INFO)
        self.pushButton_connect.setStyleSheet(STYLESHEET_BUTTON_INACTIVE)
        self.pushButton_connect.setText("Connect")
        self.comboBox_baud.setEnabled(True)
        self.comboBox_parity.setEnabled(True)
        self.checkBox_rtscts.setEnabled(True)
        self.checkBox_xonxoff.setEnabled(True)
        self.checkBox_dsrdtr.setEnabled(True)
        self.pushButton_send.setStyleSheet(STYLESHEET_BUTTON_DEFAULT)
        if self.extension_active:
            try:
                self.extension_worker._serial_disconnected()
            except Exception as e:
                self.terminal_add_text(f"Error in extension serial_disconnected: {e}", type=TYPE_ERROR)

        self.current_port = None

        self.logger.set_serial_port(self.current_port)

        self.update_status_bar()

        self.serial_worker = None
        self.serial_thread = None

        ## STOP SERIAL WORKER

    def serial_error(self, error: str = None):
        if error is None:
            error = "Serial Error"
        self.set_debug_text(error, color=COLOR_RED)
        self.terminal_add_text(error, type=TYPE_ERROR)
        self.serial_disconnect(intentional=False)

    ############################################################
    ################### LOGGER FUNCTIONS #######################
    ############################################################

    def determine_log_open_options(self):
        temp_options = self.external_text_editor_options.copy()
        vprint("Determining log open options", color="yellow")
        for option in temp_options:
            if temp_options[option]["call"]:
                # vprint(f"Checking if {temp_options[option]['call']} exists", color="yellow")
                path = shutil.which(temp_options[option]["call"])
                if path:
                    self.external_text_editor_options[option]["call"] = path
                    # vprint(f"{temp_options[option]['call']} exists", color="green")
                    # self.comboBox_open_logs_with.addItem(option)
                else:
                    vprint(f"{self.external_text_editor_options[option]['call']} does not exist", color="red")
                    self.external_text_editor_options.pop(option)

        setComboBox_items(self.comboBox_open_logs_with, list(self.external_text_editor_options.keys()))
        setComboBox_items(self.comboBox_open_extensions_with, list(self.external_text_editor_options.keys()))
        # setComboBox_items(self.comboBox_open)
        vprint("Log Open Options: ", self.external_text_editor_options.keys(), color="cyan")

        # actions = (self.action_extension_debug_level_0, self.action_extension_debug_level_1, self.action_extension_debug_level_2, self.action_extension_debug_level_3)
        # if self.extension_active:
        # self.extension_worker.debug_level = self.spinBox_extension_debug_level.value()

    def log_command(self, *args, **kwargs):
        dprint("log command", args, kwargs)

        if not args and not kwargs:
            self.log_open(latest=True)
            return

        if "-h" in kwargs:
            self.terminal_add_text(LOG_HELP, type=TYPE_INFO)
            return
        
        if "on" in kwargs:
            self.checkBox_auto_log.setChecked(True)

        if "off" in kwargs:
            self.checkBox_auto_log.setChecked(False)

        if "--line-fmt" in kwargs and kwargs["--line-fmt"]:
            self.lineEdit_log_line_format.setText(kwargs["--line-fmt"])

        if "--time-fmt" in kwargs and kwargs["--time-fmt"]:
            self.lineEdit_log_time_format.setText(kwargs["--time-fmt"])

        if "-o" in kwargs:
            self.log_open(kwargs["-o"])
            return

        if "-s" in kwargs:
            self.log_save(kwargs["-s"])
            return

        if "-n" in kwargs:
            self.checkBox_auto_log.setChecked(True)
            self.log_configure(kwargs["-n"])
            return

        if "-ls" in kwargs:
            self.terminal_add_text(self.list_files(self.lineEdit_log_directory.text(), extensions=".txt"), type=TYPE_INFO)
            self.tabWidget.setCurrentIndex(0)
            return

    def get_log_settings(self, filename: str = None):

        dir = self.lineEdit_log_directory.text()

        if not dir or not os.path.exists(dir):
            self.terminal_add_text(f"Invalid Log Directory {dir}", type=TYPE_ERROR)
            self.lineEdit_log_directory.setStyleSheet(STYLESHEET_LINE_EDIT_ERROR)
            return None, None, None

        using_default_name = False
        if not filename:
            filename = self.lineEdit_default_log_name.text()
            using_default_name = True
        try:
            filename = time.strftime(filename)
            filename = clean_filepath(filename, dir, (".txt",))
        except Exception as e:
            self.terminal_add_text(f"Invalid Log Name: ({filename}) {e}", type=TYPE_ERROR)
            if using_default_name:
                self.lineEdit_default_log_name.setStyleSheet(STYLESHEET_LINE_EDIT_ERROR)

        line_fmt = replace_control_chars(self.lineEdit_log_line_format.text())
        if not line_fmt:
            self.set_debug_text("Invalid Log Format", color=COLOR_RED)

        time_fmt = self.lineEdit_log_time_format.text()
        if not time_fmt:
            self.set_debug_text("Invalid Log Time Format", color=COLOR_RED)

        return filename, line_fmt, time_fmt

    def auto_log_toggled(self, state: int):
        if self.init_done:
            self.logger.set_enabled(state)

    def restart_logger_clicked(self):
        if self.checkBox_auto_log.isChecked():
            self.log_configure()

    def log_configure(self, filename: str = None, force_state: bool = None):
        filename, line_fmt, time_fmt = self.get_log_settings(filename)
        if not filename:
            return 
        self.logger = SK_Logger(filename, line_fmt, time_fmt, self.current_port)
        self.logger.filename_changed.connect(self.label_current_log.setText)
        if force_state is None:
            self.logger.set_enabled(self.checkBox_auto_log.isChecked())
        else:
            self.checkBox_auto_log.setChecked(force_state)

    def log_directory_select_clicked(self):
        dir = QFileDialog.getExistingDirectory(self, "Select Log Directory")
        if not dir:
            return

        self.lineEdit_log_directory.setText(dir)
        self.log_configure()

    def log_config_changed(self):
        filename, line_fmt, time_fmt = self.get_log_settings()
        p = ""
        try:
            p += "Log Sample: " + filename + "\n----------\n"
            p += self.logger.sample_output("LINE1", line_fmt, time_fmt, self.current_port) + "\n"
            time.sleep(0.05)

        except Exception as e:
            self.label_log_sample.setText(f"Error in log_config_changed {e}")
            return

        p += self.logger.sample_output("LINE2", line_fmt, time_fmt, self.current_port) + "\n"
        p += self.logger.sample_output("LINE3", line_fmt, time_fmt, self.current_port) + "\n"
        p += "----------\n"
        self.label_log_sample.setText(p)

        if self.init_done:
            self.pushButton_restart_logger.setStyleSheet(STYLESHEET_BUTTON_GREEN)
            vprint(p, color="yellow")

    def log_save(self, filepath: str = None, overwrite_existing: bool = False):
        if not filepath:
            filepath = self.get_save_file_popup(self.lineEdit_log_directory.text(), extensions=("*.txt", "*.csv", "*.log"))
            if not filepath:
                dprint("No file selected, no action taken", color="red")
                return
        else:
            filepath = clean_filepath(filepath, self.lineEdit_log_directory.text(), (".txt", ".csv", ".log"))

        if not self.logger:
            self.terminal_add_text("No log file open", type=TYPE_ERROR)
            return
        if not self.logger.filepath:
            self.terminal_add_text("No log file open", type=TYPE_ERROR)
            return

        dprint(f"Saving current log {self.logger.filepath} to {filepath}", color="green")

        if not overwrite_existing:
            backup_filepath = get_backup_filepath(filepath)
            if backup_filepath:
                self.terminal_add_text(f"Backing up existing file: {filepath}\n to: {backup_filepath}", type=TYPE_INFO)
                shutil.copy2(filepath, backup_filepath)

        shutil.copy2(self.logger.filepath, filepath)

    def log_open(self, filename: str = None, latest: bool = False, open_with: str = None):
        if latest:
            filename = self.logger.filepath

        if not filename:
            filename = self.get_file_popup(self.lineEdit_log_directory.text(), extensions=("*.txt", "*.csv", "*.log", "*.png", "*.svg"))
            if not filename:
                dprint("No file selected", color="red")
                return
        else:
            filename = clean_filepath(filename, self.lineEdit_log_directory.text(), (".txt", ".csv", ".log", ".png", ".svg"), True)
        dprint(f"Opening log from {filename}", color="green")
        if not os.path.exists(filename):
            dprint(f"File {filename} does not exist", color="red")
            self.terminal_add_text(f"File {filename} does not exist", type=TYPE_ERROR)
            return

        if self.comboBox_open_logs_with.currentText() == "Built-in":  ## Special case for built-in text viewer
            open_text_popup(self, file=filename)
            return

        if open_with is None:
            open_with = self.comboBox_open_logs_with.currentText()

        if open_with not in getComboBox_items(self.comboBox_open_logs_with):
            # dprint(f"Invalid open_with option: {open_with}", color="red")
            self.terminal_add_text(f"Invalid open_with option: {open_with}", type=TYPE_ERROR)
            return

        if open_with == "Custom":
            cmd = self.lineEdit_custom_log_command.text() + " "
        else:
            cmd = None

        self.open_in_external_editor(filename, open_with, DEFAULT_LOG_PATH, cmd)

    ############################################################
    ################### PORT FUNCTIONS #########################
    ############################################################

    def list_ports(self, *args, **kwargs):
        if not self.ports:
            self.set_debug_text("No ports found", color=COLOR_LIGHT_YELLOW)
            self.terminal_add_text("No ports found", type=TYPE_INFO)
            return

        small_str = "Ports: "
        p_str = f"--#---NAME------------PROD----------------\n"
        for index, port in enumerate(self.ports):
            small_str += f"{port.Display}, "
            p_str += f"({index:<3}) {port.Display:<15} {port.Prod}\n"
            if args:
                p_str += port.info()
        self.set_debug_text(small_str, color=COLOR_LIGHT_YELLOW)
        self.terminal_add_text(p_str.removesuffix("\n"), type=TYPE_INFO)

    def update_ports(self, ports: list[SK_Port]):
        if not self.ports and not ports:
            return
        vprint(f"Port Changed: {ports}", color="yellow")

        prev_port_names = [str(x) for x in self.ports]
        new_port_names = [str(x) for x in ports]

        # print(prev_port_names, new_port_names)

        ports_lost = set(prev_port_names).difference(set(new_port_names))
        ports_found = set(new_port_names).difference(set(prev_port_names))

        if ports_lost:
            dprint("LOST PORTS: ", ports_lost)
            self.set_debug_text(f"Lost Ports: {str(ports_lost).removeprefix('{').removesuffix('}')}", color=COLOR_RED)
        if ports_found:
            dprint("FOUND PORTS: ", ports_found)
            self.set_debug_text(f"Found Ports: {str(ports_found).removeprefix('{').removesuffix('}')}", color=COLOR_GREEN)
        self.ports = ports

        setComboBox_items(self.comboBox_port, ports)

        if self.last_connected_port:
            if self.last_connected_port in ports:
                self.comboBox_port.setCurrentText(self.last_connected_port)

        if (not ser.is_open) and self.checkBox_auto_reconnect.isChecked() and self.auto_reconnect_port:
            if self.auto_reconnect_port in ports:
                self.serial_connect(self.auto_reconnect_port)

    def start_rescan_worker(self):
        self.rescan_thread = QThread()
        self.rescan_worker = RescanWorker()
        self.rescan_worker.aliases = self.port_aliases
        self.rescan_worker.moveToThread(self.rescan_thread)
        self.rescan_thread.started.connect(self.rescan_worker.run)
        self.rescan_worker.new_ports.connect(self.update_ports)
        self.rescan_thread.start(QThread.Priority.LowPriority)

    ############################################################
    ################### SETTINGS FUNCTIONS #####################
    ############################################################

    def settings_command(self, *args, **kwargs):
        dprint("Settings Command: ", args, kwargs)

        if not args and not kwargs:
            self.terminal_add_text(pretty_format_dict(self.current_settings), TYPE_INFO)
            return

        if "-h" in kwargs:
            self.terminal_add_text(SETTINGS_HELP, TYPE_INFO)
            return

        if "--load" in kwargs:
            self.settings_load(kwargs["--load"])
            return

        if "--save" in kwargs:
            self.settings_save_as(kwargs["--save"])
            return

        if "--list" in kwargs:
            self.terminal_add_text(self.list_files(DEFAULT_SETTINGS_PATH, extensions=(".json")), type=TYPE_INFO)
            return

        for arg in args:
            arg: str
            toks = arg.split("=", 1)
            setting = toks[0]
            value = None
            if len(toks) == 2:
                value = toks[1]

            if setting in self.current_settings:
                if value is not None:
                    try:
                        if isinstance(self.current_settings[setting], bool):
                            if value.upper() == "TRUE" or value == "1":
                                value = True
                            elif value.upper() == "FALSE" or value == "0":
                                value = False
                        else:
                            value = type(self.current_settings[setting])(value)
                        self.current_settings[setting] = value
                        dprint(f"Updating Existing Setting: {setting} = {value}")
                        dprint(value)
                    except Exception as E:
                        self.terminal_add_text(E, type=TYPE_ERROR)
                        # print(E)
                self.terminal_add_text(f"{setting}={self.current_settings[setting]}", type=TYPE_INFO)
                # dprint(type(self.current_settings[setting]))
                # print(self.settings[setting])

            vprint(setting, value, color="green")
            self.settings_update_ui()

    def settings_create(self):
        self.save_checkboxes = [
            self.checkBox_dsrdtr,
            self.checkBox_rtscts,
            self.checkBox_xonxoff,
            self.checkBox_allow_commands,
            self.checkBox_allow_expressions,
            self.checkBox_auto_log,
            self.checkBox_auto_reconnect,
            self.checkBox_auto_scroll,
            self.checkBox_terminal_tx,
            self.checkBox_terminal_rx,
            self.checkBox_terminal_info,
            self.checkBox_terminal_error,
            self.checkBox_log_error,
            self.checkBox_log_info,
            self.checkBox_log_rx,
            self.checkBox_log_tx,
            self.checkBox_include_header,
            self.checkBox_wrap_text,
            self.checkBox_auto_save_settings,
        ]

        self.save_lineEdits = [
            self.lineEdit_prepend,
            self.lineEdit_append,
            self.lineEdit_prepend_tx,
            self.lineEdit_prepend_rx,
            self.lineEdit_command_char,
            self.lineEdit_default_log_name,
            self.lineEdit_prepend_info,
            self.lineEdit_prepend_error,
            self.lineEdit_log_directory,
            self.lineEdit_script_dir,
            self.lineEdit_plot_export_directory,
            self.lineEdit_default_log_name,
            self.lineEdit_log_time_format,
            self.lineEdit_log_line_format,
            self.lineEdit_custom_extension_command,
            self.lineEdit_custom_log_command,
            # self.lineEdit_custom_command,
            # self.lineEdit_custom_open_command,
        ]

        self.save_comboBoxes = [
            self.comboBox_baud,
            self.comboBox_parity,
            self.comboBox_auto_reconnect_on,
            self.comboBox_export_timestamp_format,
            self.comboBox_open_logs_with,
            self.comboBox_open_extensions_with,
        ]

        for checkbox in self.save_checkboxes:
            checkbox.stateChanged.connect(self.settings_save_needed)
            self.current_settings[checkbox.objectName()] = checkbox.isChecked()

        for lineEdit in self.save_lineEdits:
            lineEdit.textChanged.connect(self.settings_save_needed)
            self.current_settings[lineEdit.objectName()] = lineEdit.text()
        for comboBox in self.save_comboBoxes:
            comboBox.currentTextChanged.connect(self.settings_save_needed)
            self.current_settings[comboBox.objectName()] = comboBox.currentText()

        #self.settings_recall()

    def settings_save_needed(self):
        if not self.init_done:
            return
        self.settings_saved = False
        self.update_status_bar()
        if not self.checkBox_auto_save_settings.isChecked():
            return
        if time.perf_counter() - self.last_save_time < (self.save_delay / 1000):
            return
        self.last_save_time = time.perf_counter()
        self.save_timer.singleShot(self.save_delay, self.settings_save)
        dprint("save needed", color="yellow")

    def settings_save(self, filepath: str = None, update_all=True):
        if filepath is None:
            filepath = DEFAULT_SETTINGS_FILE

        vprint(f"Saving settings to {filepath} update_all: {update_all}", color="yellow")
        if update_all:
            for checkbox in self.save_checkboxes:
                if checkbox.objectName() in self.current_settings:
                    self.current_settings[checkbox.objectName()] = checkbox.isChecked()
            for lineEdit in self.save_lineEdits:
                if lineEdit.objectName() in self.current_settings:
                    self.current_settings[lineEdit.objectName()] = lineEdit.text()
            for comboBox in self.save_comboBoxes:
                if comboBox.objectName() in self.current_settings:
                    self.current_settings[comboBox.objectName()] = comboBox.currentText()
            self.settings_saved = True
            vprint(pretty_format_dict(self.current_settings), color="green")

        with open(filepath, "w+") as f:
            json.dump(self.current_settings, f)

        self.update_status_bar()

    def settings_update_ui(self):
        try:
            for checkbox in self.save_checkboxes:
                if checkbox.objectName() in self.current_settings:
                    checkbox.setChecked(self.current_settings[checkbox.objectName()])
                else:
                    self.set_debug_text(f"Setting {checkbox.objectName()} not found in settings file", color="red")
                    self.terminal_add_text(f"Setting {checkbox.objectName()} not found in settings file", type=TYPE_ERROR)
            for lineEdit in self.save_lineEdits:
                if lineEdit.objectName() in self.current_settings:
                    lineEdit.setText(self.current_settings[lineEdit.objectName()])
                else:
                    self.terminal_add_text(f"Setting {lineEdit.objectName()} not found in settings file", type=TYPE_ERROR)
            for comboBox in self.save_comboBoxes:
                comboBox: QtWidgets.QComboBox
                if comboBox.objectName() in self.current_settings:
                    comboBox.setCurrentText(self.current_settings[comboBox.objectName()])
                else:
                    self.terminal_add_text(f"Setting {comboBox.objectName()} not found in settings file", type=TYPE_ERROR)
        except Exception as e:
            eprint(f"RECALL SETTINGS MISMATCH: {e}", color="red")

        if not os.path.exists(self.lineEdit_log_directory.text()):
            self.lineEdit_log_directory.setText(DEFAULT_LOG_PATH)
        if not os.path.exists(self.lineEdit_script_dir.text()):
            self.lineEdit_script_dir.setText(DEFAULT_SCRIPT_PATH)
        if not os.path.exists(self.lineEdit_plot_export_directory.text()):
            self.lineEdit_plot_export_directory.setText(DEFAULT_PLOT_EXPORT_PATH)

        set_table_items(self.tableWidget_keys, self.current_settings["key_commands"])
        set_table_items(self.tableWidget_expressions, self.current_settings["user_expressions"])
        if "aliases" in self.current_settings:
            set_table_items(self.tableWidget_port_aliases, self.current_settings["aliases"])
            self.port_aliases = self.current_settings["aliases"]

    def recall_settings(self, filepath: str = None):
        if filepath is None:
            filepath = DEFAULT_SETTINGS_FILE
            if not os.path.exists(filepath):
                eprint(f"Settings file {filepath} does not exist, creating new default settings")
                self.current_settings["key_commands"] = {}
                self.current_settings["user_expressions"] = {}
                self.current_settings["aliases"] = {}
                self.current_settings["last_opened_script"] = ""
                self.current_settings["key_commands"] = get_table_items(self.tableWidget_keys)
                self.current_settings["user_expressions"] = get_table_items(self.tableWidget_expressions)
                self.current_settings["aliases"] = get_table_items(self.tableWidget_port_aliases)
                self.settings_save(DEFAULT_SETTINGS_FILE)
                # self.settings_save(DEFAULT_SETTINGS_FILE)
        with open(filepath, "r") as f:
            settings = json.load(f)
            self.current_settings.update(settings)

        vprint(f"Recalling Settings {filepath}", color="yellow")

        self.settings_update_ui()

        return self.current_settings

    def settings_load(self, filename: str = None):
        if not filename:
            filename = self.get_file_popup(DEFAULT_SETTINGS_PATH, extensions=("*.json"))
            if not filename:
                return

        filename = clean_filepath(filename, default_path=DEFAULT_SETTINGS_PATH, extensions=(".json"))

        if not os.path.exists(filename):
            self.terminal_add_text(f"Settings file {filename} does not exist", type=TYPE_ERROR)
            return

        self.terminal_add_text(f"Loading settings from {filename}", type=TYPE_INFO_GREEN)
        self.settings_recall(filename)

    def settings_save_as(self, filename: str = None):
        if not filename:
            filename = self.get_save_file_popup(DEFAULT_SETTINGS_PATH, extensions=("*.json"))
            if not filename:
                return
        filename = clean_filepath(filename, default_path=DEFAULT_SETTINGS_PATH, extensions=(".json"))
        self.terminal_add_text(f"Saving settings to {filename}", type=TYPE_INFO_GREEN)
        self.settings_save(filename)

    ############################################################
    ################### PLOT FUNCTIONS #######################
    ############################################################

    def plot_command(self, *args, **kwargs):
        dprint("plot command", args, kwargs, color="yellow")

        if not args and not kwargs:
            self.tabWidget.setCurrentIndex(2)
            return

        if "-h" in kwargs:
            self.terminal_add_text(PLOT_HELP, TYPE_INFO)
            return
        
        if "--popup" in kwargs:
            self.launch_plot_popup(kwargs["--popup"])
            return

        if "--export" in kwargs:
            filename = kwargs["--export"]
            rounding = None
            include_header = None
            image_size = None
            time_format = None
            open = False
            if filename is not None:
                filename = clean_filepath(filename, default_path=self.lineEdit_plot_export_directory.text(), extensions=(".csv", ".png", ".svg"))

            if "--time-fmt" in kwargs:
                time_format = kwargs["--time-fmt"]
                if time_format not in ("UNIX", "Zero", "Plot-Start", "None"):
                    self.terminal_add_text(f"Invalid time format: {time_format} valid options are: UNIX, Zero, Plot-Start, None", type=TYPE_ERROR)
                    return

            if "--round" in kwargs:
                rounding = str_to_float(kwargs["--round"])

            if "--header" in kwargs:
                include_header = kwargs["--header"]

            if "--size" in kwargs:
                image_size = []
                for item in kwargs["--size"]:
                    image_size.append(int(item))

            if "--open" in kwargs:
                open = True

            self.plot_export(filename, rounding, include_header, image_size, time_format, open)
            return

        if "-s" in kwargs:
            if kwargs["-s"] is not None:
                self.lineEdit_seps.setText(kwargs["-s"])

        if "-p" in kwargs:
            if kwargs["-p"] is not None:
                self.lineEdit_points.setText(kwargs["-p"])

        if "-k" in kwargs:
            if kwargs["-k"] is not None:
                self.lineEdit_keys.setText(kwargs["-k"])
            else:
                self.lineEdit_keys.setText("")

        if "-l" in kwargs:
            if kwargs["-l"] is not None:
                self.lineEdit_limits.setText(kwargs["-l"])
            else:
                self.lineEdit_limits.setText("")

        if "-r" in kwargs:
            if kwargs["-r"] is not None:
                self.lineEdit_refs.setText(kwargs["-r"])
            else:
                self.lineEdit_refs.setText("")
            # self.lineEdit_refs.setText("")

        title = ""
        if "-t" in kwargs:
            if kwargs["-t"] is not None:
                title = kwargs["-t"]

        plot_type = None

        a = list(args)

        while a:
            arg: str = a.pop(0)
            if arg == "pause":
                self.plot_pause()
                return
            elif arg == "reset":
                self.plot_reset()
                # return
            elif arg == "resume":
                self.plot_resume()
                return
            elif arg == "start":
                # self.plot_start()
                plot_type = self.comboBox_plot_type.currentText()
            elif arg == "test":
                test_str = " ".join(a)
                self.terminal_add_text(f"--> '{test_str}'", type=TYPE_INFO)
                start_t = time.perf_counter_ns()
                s = self.plot.update(test_str, True)
                end_t = time.perf_counter_ns()
                self.terminal_add_text(f" RESULT: {s}", type=TYPE_INFO_GREEN)
                self.terminal_add_text(f" Update Time: {(end_t - start_t)/1000:.4f}us", type=TYPE_INFO)
                return
            elif arg == "kv" or arg.upper() == "KEY-VALUE":
                plot_type = "Key-Value"
            elif arg == "iv" or arg.upper() == "INDEX-VALUE":
                plot_type = "Index-Value"
            elif arg == "ka" or arg.upper() == "KEY-ARRAY":
                plot_type = "Key-Array"
            elif arg == "sv" or arg.upper() == "SINGLE-VALUE":
                plot_type = "Single-Value"
            elif arg == "sa" or arg.upper() == "SINGLE-ARRAY":
                plot_type = "Single-Array"
            else:
                self.terminal_add_text(f"Invalid plot command: '{arg}' try -h for help", type=TYPE_ERROR)
                return

        if plot_type is not None:
            self.comboBox_plot_type.setCurrentText(plot_type)
            self.plot_start(title=title)

    def launch_plot_popup(self, item_str:str = None, **kwargs):
        print("launch plot popup", item_str, kwargs)

        data = {}
        if not item_str:
            item_str = self.lineEdit_keys.text()
        if item_str: 
            data = str_to_plot_elements(item_str)

        dprint("Opening Key Popup with Data:", data, color="yellow")
        self.key_popup = KeyPopup(data=data)
        self.key_popup.result.connect(self.key_popup_accepted)
        self.key_popup.rejected.connect(self.key_popup_rejected)
        self.key_popup.show()

    def key_popup_rejected(self):
        dprint("key popup rejected")
        self.key_popup = None 

    def key_popup_accepted(self, result: str = None):
        dprint("key popup result:", result, color = "green")
        if result == None: 
            return 
        self.lineEdit_keys.setText(plot_elements_to_str(result))
        self.key_popup = None 



    def plot_export(self, filepath: str = None, rounding: float = None, include_header: bool = False, image_size: tuple[int, int] = None, time_format: str = None, open=False):
        if self.plot.type is None:
            self.terminal_add_text("No plot in progress", type=TYPE_ERROR)
            self.set_debug_text("No plot in progress", color=COLOR_RED)
            return

        if not self.plot.elements:
            self.terminal_add_text("No data to export", type=TYPE_ERROR)
            self.set_debug_text("No data to export", color=COLOR_RED)
            return

        if filepath is None:  ## Using UI filepaths
            if not self.lineEdit_export_plot.text():
                filepath = self.get_save_file_popup(self.lineEdit_plot_export_directory.text(), extensions=("*.csv", "*.png", "*.svg"))
                if not filepath:
                    return
            else:
                filepath = os.path.join(self.lineEdit_plot_export_directory.text(), self.lineEdit_export_plot.text() + self.comboBox_export_extension.currentText())

        ext = os.path.splitext(filepath)[1]

        if ext not in (".csv", ".png", ".svg"):
            self.set_debug_text(f"Invalid file extension: {ext}. Only .csv, .png, and .svg are supported", color=COLOR_RED)
            self.terminal_add_text(f"Invalid file extension: {ext}. Only .csv, .png, and .svg are supported", type=TYPE_ERROR)
            return

        backup_filepath = get_backup_filepath(filepath)
        if backup_filepath:
            shutil.copy2(filepath, backup_filepath)
            backup_name = os.path.split(backup_filepath)[1]
            file_name = os.path.split(filepath)[1]
            self.terminal_add_text(f"File already exists: {file_name}", type=TYPE_INFO)
            self.terminal_add_text(f"Copying existing file to backup: {backup_name}", type=TYPE_INFO)

        dprint(f"Exporting to {filepath} with rounding: {rounding} and include_header: {include_header}", color="yellow")

        if ext == ".csv":
            if rounding is None:
                rounding = str_to_float(self.lineEdit_export_timestep_rounding.text())

            if time_format is None:
                time_format = self.comboBox_export_timestamp_format.currentText()

            if include_header is None:
                include_header = self.checkBox_include_header.isChecked()
            self.plot.export_csv(filepath, rounding, include_header, time_format)

            if open:
                open_text_popup(self, file=filepath)

        elif ext in (".png", ".svg"):
            self.plot.export_image(filepath, image_size)

        self.terminal_add_text(f"Exported plot to {filepath}", type=TYPE_INFO_GREEN)
        self.set_debug_text(f"Exported plot", color=COLOR_GREEN)

    def plot_start(self, junk=None, title=""):
        # if self.plot.type is not None:
        #     self.plot_reset()

        type = self.comboBox_plot_type.currentText()
        points = int(self.lineEdit_points.text())
        keys = self.lineEdit_keys.text()

        separators = replace_control_chars(self.lineEdit_seps.text())
        refs = self.lineEdit_refs.text()
        limits = self.lineEdit_limits.text()

        self.plot.start(type=type, points=points, keys=keys, separators=separators, refs=refs, title=title, limits=limits)
        ## UI CHANGES
        self.pushButton_plot_start.setText("Pause")
        self.pushButton_plot_start.setStyleSheet(STYLESHEET_BUTTON_YELLOW)
        self.pushButton_plot_reset.setStyleSheet(STYLESHEET_BUTTON_RED)
        self.pushButton_plot_export.setEnabled(True)
        # self.pushButton_plot_export.setEnabled(True)
        # self.comboBox_plot_type.setEnabled(False)
        # self.lineEdit_points.setEnabled(False)
        # self.lineEdit_keys.setEnabled(False)
        # self.lineEdit_seps.setEnabled(False)
        # self.lineEdit_limits.setEnabled(False)
        # self.lineEdit_refs.setEnabled(False)
        self.tabWidget.setCurrentIndex(2)
        self.update_status_bar()

    def plot_reset(self):
        if self.plot.type is None:
            return
        self.plot.reset()
        ## UI CHANGES
        self.pushButton_plot_start.setText("Start")
        self.pushButton_plot_start.setStyleSheet(STYLESHEET_BUTTON_GREEN)
        self.pushButton_plot_reset.setStyleSheet(STYLESHEET_BUTTON_DEFAULT)
        self.comboBox_plot_type.setEnabled(True)
        # self.lineEdit_points.setEnabled(True)
        # self.lineEdit_keys.setEnabled(True)
        # self.lineEdit_seps.setEnabled(True)
        # self.lineEdit_limits.setEnabled(True)
        # self.lineEdit_refs.setEnabled(True)
        self.pushButton_plot_export.setEnabled(False)
        self.update_status_bar()

    def plot_pause(self):
        if self.plot.type is None:
            return
        if not self.plot.active:
            return
        self.plot.pause()
        self.pushButton_plot_start.setText("Resume")
        self.pushButton_plot_start.setStyleSheet(STYLESHEET_BUTTON_GREEN)
        self.pushButton_plot_reset.setStyleSheet(STYLESHEET_BUTTON_RED)
        self.update_status_bar()

    def plot_resume(self):
        if self.plot.type is None:
            return
        if self.plot.active:
            return
        self.plot.resume()
        self.pushButton_plot_start.setText("Pause")
        self.pushButton_plot_start.setStyleSheet(STYLESHEET_BUTTON_YELLOW)
        self.pushButton_plot_reset.setStyleSheet(STYLESHEET_BUTTON_RED)
        self.update_status_bar()

    def plot_start_pause_clicked(self):
        if self.plot.type is None:
            self.plot_start()
            return
        elif self.plot.active:
            self.plot_pause()
        else:
            self.plot_resume()

    ############################################################
    ################### SCRIPT FUNCTIONS #####################
    ############################################################

    def script_command(self, *args, **kwargs):
        dprint("script command", args, kwargs)

        if "-t" in kwargs:
            self.tabWidget.setCurrentIndex(1)
            self.textEdit_script.setFocus()
            return

        if "-h" in kwargs:
            self.terminal_add_text(SCRIPT_HELP, TYPE_INFO)
            self.terminal_add_text(SCRIPT_SYNTAX_HELP, TYPE_INFO)
            self.tabWidget.setCurrentIndex(0)
            return

        if "-ls" in kwargs:
            self.terminal_add_text(self.list_files(self.lineEdit_script_dir.text()), TYPE_INFO)
            self.tabWidget.setCurrentIndex(0)
            return

        if "-o" in kwargs:
            self.open_script(kwargs["-o"])
            return

        if "-s" in kwargs:
            self.save_script(kwargs["-s"])
            return

        if "-n" in kwargs:
            self.textEdit_script.setPlainText("")
            if kwargs["-n"]:
                self.lineEdit_save_as_script.setText(kwargs["-n"])
            else:
                self.lineEdit_save_as_script.setText("")
            self.tabWidget.setCurrentIndex(1)
            self.lineEdit_save_as_script.setFocus()
            return

        if "-d" in kwargs:
            if kwargs["-d"]:
                delay = str_to_float(kwargs["-d"])
                if delay is None or delay < 0:
                    self.terminal_add_text(f"Invalid delay: {kwargs['-d']}", type=TYPE_ERROR)
                    return
                self.lineEdit_delay.setText(kwargs["-d"])
            else:
                self.terminal_add_text("Error: No delay specified with -d", type=TYPE_ERROR)

        self.run_script(args)

    def script_edited(self):
        if time.time() - self.init_time < 0.2:
            return
        self.pushButton_save_as_script.setStyleSheet(STYLESHEET_BUTTON_GREEN)

    def open_script(self, filepath: str = None):
        if not filepath:
            filepath = self.get_file_popup(self.lineEdit_script_dir.text(), extensions="*.txt")
            if not filepath:
                return
        filepath = clean_filepath(filepath, default_path=self.lineEdit_script_dir.text(), extensions=".txt")
        dprint(f"Opening Script: {filepath}", color="yellow")
        script_text = self.read_file(filepath)
        if script_text is None:
            self.terminal_add_text(f"Failed to open script: {filepath}", type=TYPE_ERROR)
            return
        self.textEdit_script.setPlainText(script_text)
        self.lineEdit_save_as_script.setText(os.path.split(filepath)[1].removesuffix(".txt"))
        self.tabWidget.setCurrentIndex(1)
        self.textEdit_script.setFocus()
        self.current_settings["last_opened_script"] = filepath
        self.pushButton_save_as_script.setStyleSheet(STYLESHEET_BUTTON_DEFAULT)
        # self.save_settings(update_all=False)

    def script_line(self, line: tuple[str, int]):
        if (line[1] & 0x07) == TYPE_SRC_TX:
            self.lineEdit_send.setText(line[0])
            self.send_clicked(None, False)
            self.lineEdit_send.setText(line[0])
            return
        else:
            text = self.evaluate_input_text(line[0])
            if line[1] == TYPE_SRC_COMMAND:
                text = self.execute_command(text)
                return
            self.terminal_add_text(text, type=line[1])

    def run_script(self, args: list[str] = []):
        delay = str_to_float(self.lineEdit_delay.text())
        if delay is None or delay < 0:
            self.terminal_add_text("Invalid delay", type=TYPE_ERROR)
            return

        text = self.textEdit_script.toPlainText()
        if not text:
            self.terminal_add_text("No script to run", type=TYPE_ERROR)
            return

        if self.lineEdit_save_as_script.text() and self.checkBox_save_on_run.isChecked():
            self.save_script()

        self.script_thread = QThread()
        self.script_worker = ScriptWorker(text=self.textEdit_script.toPlainText(), delay=delay, args=args)
        self.script_worker.moveToThread(self.script_thread)
        self.script_thread.started.connect(self.script_worker.run)
        self.script_worker.output.connect(self.script_line)
        self.script_worker.finished.connect(self.stop_script)
        self.script_thread.start()

        self.set_debug_text("Use ESC to cancel script", color=COLOR_LIGHT_YELLOW)
        self.tabWidget.setCurrentIndex(0)

        ## UI CHANGES
        self.lineEdit_send.setEnabled(False)
        # self.pushButton_run_script.setEnabled(False)
        self.pushButton_run_script.setText("Cancel")
        self.pushButton_run_script.setStyleSheet(STYLESHEET_BUTTON_RED)
        self.pushButton_send.setEnabled(False)
        self.action_script_run.setText("Cancel")
        self.update_status_bar()

    def run_script_clicked(self):
        if self.script_worker is not None:
            self.script_cancel()
        else:
            self.run_script()

    def script_cancel(self):
        if self.script_worker is None:
            return
        self.script_worker.cancel()

    def stop_script(self, error: str = None):
        if self.script_worker is None:
            return
        if error:
            self.terminal_add_text(error, type=TYPE_INFO)

        self.set_debug_text(f"Script Finished in: {time.perf_counter() - self.script_worker.start_time:.2f}s", color=COLOR_LIGHT_YELLOW)
        vprint(f"Script Stopped. Error: {error}", color="green")

        self.script_worker.stop()
        self.script_thread.exit()
        self.script_worker = None

        ## UI CHANGES
        self.lineEdit_send.setEnabled(True)
        # self.pushButton_run_script.setEnabled(True)
        self.pushButton_send.setEnabled(True)
        self.pushButton_run_script.setText("Run")
        self.action_script_run.setText("Run")
        self.pushButton_run_script.setStyleSheet(STYLESHEET_BUTTON_ACTIVE)
        self.lineEdit_send.setText("")
        self.lineEdit_send.setFocus()
        self.update_status_bar()

    def save_script(self, filepath: str = None, save_as: bool = False):
        if save_as:
            filepath = self.get_save_file_popup(self.lineEdit_script_dir.text())
            if not filepath:
                return
        if not filepath:
            filepath = self.lineEdit_save_as_script.text()
            if not filepath:
                filepath = self.get_save_file_popup(self.lineEdit_script_dir.text())
                if not filepath:
                    return
        filepath = clean_filepath(filepath, default_path=self.lineEdit_script_dir.text(), extensions=".txt")
        with open(filepath, "w+") as f:
            f.write(self.textEdit_script.toPlainText())
        self.current_settings["last_opened_script"] = filepath
        self.settings_save(update_all=False)
        self.lineEdit_save_as_script.setText(os.path.split(filepath)[1].removesuffix(".txt"))
        self.pushButton_save_as_script.setStyleSheet(STYLESHEET_BUTTON_DEFAULT)
        self.set_debug_text(f"Saved script to {filepath}", color=COLOR_GREEN)

    ############################################################
    ################### EXTENSION FUNCTIONS ####################
    ############################################################

    def extension_command(self, *args, **kwargs):
        dprint("extension command", args, kwargs)

        if "-h" in kwargs:
            self.terminal_add_text(EXTENSION_HELP, type=TYPE_INFO)
            self.tabWidget.setCurrentIndex(0)
            return

        debug_level = self.ext_debug_level
        if "--debug" in kwargs:
            debug_level = int(kwargs["--debug"])
            self.extension_debug_level_changed(debug_level)
            if self.extension_active:
                self.extension_worker.debug_level = debug_level
                return

        if "new" in kwargs:
            self.extension_new(kwargs["new"])
            return

        if "stop" in kwargs:
            self.extension_request_end()
            return

        if "cmd" in kwargs:
            if self.extension_active:
                self.extension_worker._receive_commands(kwargs["cmd"])
                return

        if "list" in kwargs:
            self.terminal_add_text(self.list_files(DEFAULT_EXTENSION_PATH), type=TYPE_INFO)
            return

        if "open" in kwargs:
            self.extension_open(kwargs["open"])
            return

        filename = None
        input_args = []
        if not args and not kwargs:
            filename = self.get_file_popup(DEFAULT_EXTENSION_PATH, extensions="*.py")
            if not filename:
                return

        if "run" in kwargs:
            if kwargs["run"]:
                filename = kwargs["run"]
                # self.extension_run(args[0], debug_level, kwargs["cmd"])
                return
            else:
                filename = self.get_file_popup(DEFAULT_EXTENSION_PATH, extensions="*.py")
                if not filename:
                    return

        if not args:
            self.terminal_add_text("No extension filename specified", type=TYPE_ERROR)
            return

        if not filename:
            filename = args[0]
            input_args = args[1:]
        else:
            input_args = args

        self.extension_run(filename, debug_level, input_args)

    def extension_run(self, filename: str = None, debug_level: int = None, args: list[str] = []):
        if debug_level is None:
            debug_level = self.ext_debug_level
        if not filename:
            filename = self.get_file_popup(DEFAULT_EXTENSION_PATH, extensions="*.py", title="Select Extension")
            if not filename:
                return
        filename = clean_filepath(filename, default_path=DEFAULT_EXTENSION_PATH, extensions=".py")

        if self.extension_active:
            self.terminal_add_text("Extension already running. Terminate with 'ext stop'", type=TYPE_ERROR)
            return

        if not os.path.exists(filename):
            self.terminal_add_text(f"File Not Found:\n\t{filename}", type=TYPE_ERROR)
            return

        s = os.path.split(filename)
        path = s[0]
        name, ext = os.path.splitext(s[1])

        if path != DEFAULT_EXTENSION_PATH:
            self.terminal_add_text(f"Extension not in default path. Copying to default path...", type=TYPE_INFO)
            shutil.copy2(filename, os.path.join(DEFAULT_EXTENSION_PATH, name + ext))
            filename = os.path.join(DEFAULT_EXTENSION_PATH, name + ext)
            sys.path.remove(DEFAULT_EXTENSION_PATH)
            sys.path.append(DEFAULT_EXTENSION_PATH)

        dprint(f"Running Extension: {name} with debug level: {debug_level}", color="yellow")

        try:
            if name in sys.modules:
                self.extension_module = sys.modules[name]
                importlib.reload(self.extension_module)
                self.terminal_add_text(f"Reloaded Extension: {name}", type=TYPE_INFO)
            else:
                self.extension_module = importlib.import_module(name)
            vprint(f"module: {self.extension_module} type {type(self.extension_module)}", color="green")
            self.extension_worker = self.extension_module.Extension(self)
            self.extension_worker.debug_level = debug_level
            self.extension_thread = QThread(parent=self)
            self.extension_worker.moveToThread(self.extension_thread)
            self.extension_thread.started.connect(self.extension_worker.start)
            self.extension_worker.output.connect(self.extension_output)
            self.extension_worker.exit.connect(self.extension_end)
            self.extension_thread.start()
            self.terminal_add_text(f"Extension Loaded: {self.extension_worker.name}", type=TYPE_INFO_GREEN)

            if args:
                self.extension_worker._receive_commands(args)

            if self.current_port is not None:
                self.extension_worker._serial_connected(self.current_port)

            self.extension_active = True
            self.update_status_bar()
            return

        except Exception as e:
            extension_error = traceback.format_exc()
            eprint(f"Extension Error: {extension_error}\n", color="red")
            self.terminal_add_text(f"Error importing extension: {e} \n {extension_error}", type=TYPE_ERROR)
            self.update_status_bar()
            return

    def extension_output(self, output: tuple[str, int]):
        vprint("extension_output", output)
        if output[1] & 0x07 == TYPE_SRC_TX:
            if output[1] & TYPE_CONFIG_RAW:
                self.serial_send(output[0])
                self.terminal_add_text(output[0], type=TYPE_TX)
            else:
                self.send_clicked(output[0], False)
            return
        else:
            if (output[1] & 0x0F) == TYPE_SRC_COMMAND:
                c = self.evaluate_input_text(output[0])
                self.execute_command(c)
                return
            self.terminal_add_text(output[0], type=output[1])

    def extension_open(self, filename: str = None):
        vprint("extension_open", filename)
        if not filename:
            filename = self.get_file_popup(DEFAULT_EXTENSION_PATH, extensions="*.py")
            if not filename:
                return
        filename = clean_filepath(filename, default_path=DEFAULT_EXTENSION_PATH, extensions=".py")
        if not os.path.exists(filename):
            self.terminal_add_text(f"Extension file not found: {filename}", type=TYPE_ERROR)
            return

        open_with = self.comboBox_open_extensions_with.currentText()

        cmd = None
        if open_with == "Built-in":
            open_text_popup(self, file=filename)
            return
        elif open_with == "Custom":
            cmd = self.lineEdit_custom_extension_command.text()
        self.open_in_external_editor(filename, open_with, BASE_DIR, cmd=cmd)

    def extension_request_end(self):
        if not self.extension_active:
            self.terminal_add_text("No extension active", type=TYPE_ERROR)
            return
        try:
            self.extension_worker.end()
        except Exception as e:
            self.terminal_add_text(f"Error ending extension: {e}", type=TYPE_ERROR)

    def extension_debug_level_changed(self, level: int = 0):
        vprint(f"Extension Debug Level Changed: {level}", color="yellow")
        actions = (self.action_ext_debug_0, self.action_ext_debug_1, self.action_ext_debug_2, self.action_ext_debug_3)
        for action in actions:
            action.setChecked(False)
        if level < len(actions):
            actions[level].setChecked(True)
        self.menuDebug_Level.setTitle(f"Debug Level ({level})")
        self.ext_debug_level = level

    def extension_new(self, name: str = None):
        if not name:
            name = self.get_save_file_popup(DEFAULT_EXTENSION_PATH, extensions="*.py", title="Select Extension")
            if not name:
                return
        filepath = clean_filepath(name, default_path=DEFAULT_EXTENSION_PATH, extensions=".py")
        if os.path.exists(filepath):
            self.terminal_add_text(f"Extension file already exists: {filepath}", type=TYPE_ERROR)
            return

        self.terminal_add_text(f"Creating new extension file: {filepath}", type=TYPE_INFO)

        shutil.copy2(EXTENSION_TEMPLATE_PATH, filepath)

        self.extension_open(filepath)

    def extension_end(self, result: str = ""):
        if not self.extension_active:
            return
        dprint("extension_end", result)
        self.extension_active = False
        self.extension_thread.exit()
        time.sleep(0.1)
        self.terminal_add_text(f"Extension Ended: {self.extension_worker.name} {result}", type=TYPE_INFO)
        self.extension_worker = None
        self.extension_thread = None
        self.update_status_bar()

    ############################################################
    ################### KEYBOARD FUNCTIONS ####################
    ############################################################

    def key_command(self, *args, **kwargs):
        dprint("key_command", args, kwargs)
        if not args and not kwargs:
            self.lineEdit_key_ctrl.setFocus()
            return
        if "-h" in kwargs:
            self.terminal_add_text(KEY_COMMAND_HELP, TYPE_INFO)
            self.tabWidget.setCurrentIndex(0)
            return
        elif "-ls" in kwargs:
            t = pretty_format_dict(self.current_settings["key_commands"])
            self.terminal_add_text(t, TYPE_INFO)
            self.tabWidget.setCurrentIndex(0)
            return
        elif "--clear" in kwargs:
            self.tableWidget_keys.setRowCount(0)
            self.tableWidget_keys.setRowCount(1)
            self.key_commands_edited()
            return
        elif "--save" in kwargs: 
            self.key_export_script(kwargs["--save"])
            return

        if len(args) == 2:
            self.add_key_command(args[0], args[1])

    def key_export_script(self, filepath: str = None):
        if not filepath:
            filepath = self.get_save_file_popup(self.lineEdit_script_dir.text(), extensions="*.txt", title = "Export Key Commands")
            if not filepath:
                return
        
        filepath = clean_filepath(filepath, default_path=self.lineEdit_script_dir.text(), extensions=".txt")
        dprint(f"Exporting Key Commands to {filepath}", color = "green")
        vprint(self.current_settings["key_commands"], color="green")
    
        with open(filepath, "w+") as f:
            f.write("# Auto - Export Key Commands\n")
            f.write("@key clear\n")
            for key, send in self.current_settings["key_commands"].items():
                f.write(f"@key {key}  '{send}'\n")



    def key_commands_edited(self):
        if self.tableWidget_keys.currentRow() == self.tableWidget_keys.rowCount() - 1:
            if not self.tableWidget_keys.currentItem():
                return
            self.tableWidget_keys.setRowCount(self.tableWidget_keys.rowCount() + 1)
        self.current_settings["key_commands"] = get_table_items(self.tableWidget_keys)
        vprint(self.current_settings["key_commands"], color="green")
        self.settings_save(update_all=False)

    def add_key_command(self, key: str, send: str):
        index = None
        items = self.tableWidget_keys.findItems(key, QtCore.Qt.MatchFlag.MatchExactly)
        for item in items:
            if item.column() == 0:
                index = item.row()
                break
        if index is None:
            index = self.tableWidget_keys.rowCount() - 1
            self.tableWidget_keys.setRowCount(index + 2)

        self.tableWidget_keys.setItem(index, 0, QtWidgets.QTableWidgetItem(key))
        self.tableWidget_keys.setItem(index, 1, QtWidgets.QTableWidgetItem(send))
        # self.key_commands_edited()

    def key_command_keypressed(self, key: str):
        if key in self.current_settings["key_commands"]:
            self.lineEdit_send.setText(self.current_settings["key_commands"][key])
            self.send_clicked(None, False)
        else:
            self.set_debug_text(f"Key Command not found: {key}", color=COLOR_RED)
            # self.serial_send(self.current_settings["key_commands"][key])


    ############################################################
    ################### PORT ALIAS FUNTIONS #######################
    ############################################################
    def port_alias(self, *args, **kwargs):
        vprint("port_alias", args, kwargs)
        
        if "-ls" in kwargs: 
            self.terminal_add_text(pretty_format_dict(self.port_aliases), type=TYPE_INFO)
            return
        elif "-h" in kwargs or not args: 
            self.terminal_add_text(PORT_ALIAS_HELP, type=TYPE_INFO)
            return
        
        if not self.current_port: 
            self.terminal_add_text("Alias can only be set when a serial port is connected", type=TYPE_ERROR)
            return
        
        settings = f"lineEdit_prepend='{self.lineEdit_prepend.text()}' lineEdit_append='{self.lineEdit_append.text()}' comboBox_baud='{self.comboBox_baud.currentText()}'"
        settings += f"checkBox_rtscts={self.checkBox_rtscts.isChecked()} checkBox_xonxoff={self.checkBox_xonxoff.isChecked()} checkBox_dsrdtr={self.checkBox_dsrdtr.isChecked()}"
        self.port_aliases[self.current_port.SN] = [args[0], settings]
        set_table_items(self.tableWidget_port_aliases, self.port_aliases)
        self.current_port.Alias = args[0]
        self.current_port.Settings = settings
        self.update_ports(get_ports(self.port_aliases))
        self.aliases_edited()
    
    def aliases_edited(self):
        self.current_settings["aliases"] = get_table_items(self.tableWidget_port_aliases)
        
        if self.rescan_worker is not None: 
            self.rescan_worker.aliases = self.port_aliases
        self.settings_save(update_all=False)

    
        

    ############################################################
    ################### ULITLITY FUNCTIONS #######################
    ############################################################

    def sk_open(self, *args, **kwargs):
        #print(args, kwargs)
        ext = None 
        dir = None 
        if "-h" in kwargs: 
            self.terminal_add_text(SK_OPEN_HELP, type=TYPE_INFO)
            return
        if "-e" in kwargs: 
            ext = get_extension_string(kwargs["-e"])
        if "-d" in kwargs: 
            dir = kwargs["-d"]
        file = None 
        if not args: 
            file = self.get_file_popup(file_path=dir, extensions=ext)
            if not file: 
                return 
        else: 
            file = args[0]
        if not os.path.exists(file):
            self.terminal_add_text(f"sk_open: File not found: {file}", type=TYPE_ERROR)
            self.terminal_add_text(SK_OPEN_HELP, type=TYPE_INFO)
            return
        if os.path.isdir(file):
            self.terminal_add_text(f"sk_open: {file} is a directory", type=TYPE_ERROR)
            self.terminal_add_text(SK_OPEN_HELP, type=TYPE_INFO)
            return
        open_text_popup(self, file=file)

    def get_save_file_popup(self, file_path: str = None, extensions: str = None, title: str = "Select File") -> str | None:
        if isinstance(extensions, (list, tuple)):
            extensions = ";;".join(extensions)
        elif isinstance(extensions, str):
            extensions = extensions.strip().rstrip().replace(",", ";;").replace(" ", ";;")
        else:
            extensions = None
        path, selected_filter = QFileDialog.getSaveFileName(self, title, directory=file_path, filter=extensions)
        if not path:
            vprint("get save file popup cancelled", color="yellow")
            return None
        path_ext = os.path.splitext(path)[1]
        if not path_ext:
            path = path + os.path.splitext(selected_filter)[1]

        vprint(f"get save file popup: {path}, selected filter: {selected_filter}, path ext: {path_ext}", color="yellow")

        return path

    def get_file_popup(self, file_path: str = None, extensions: str = None, title: str = "Select File") -> str | None:
        if isinstance(extensions, (list, tuple)):
            extensions = ";;".join(extensions)
        path = QFileDialog.getOpenFileName(self, "Select File", directory=file_path, filter=extensions)[0]
        vprint(path, color="yellow")
        return path

    def get_dir_popup(self, dir_path: str = None):
        path = QFileDialog.getExistingDirectory(self, "Select Directory", dir_path)
        # print(path)
        return path

    def read_file(self, filepath: str):
        if not os.path.exists(filepath):
            return None
        with open(filepath, "r") as f:
            return f.read()

    def list_files(self, directory: str, extensions: str = None):
        list_of_files = filter(lambda x: os.path.isfile(os.path.join(directory, x)), os.listdir(directory))
        files = sorted(list_of_files, key=lambda x: os.path.getmtime(os.path.join(directory, x)), reverse=True)
        files_str = directory + "\n"
        for file in files:
            fp = os.path.join(directory, file)
            file_timestamp = os.path.getmtime(fp)
            last_t = datetime.datetime.fromtimestamp(file_timestamp)
            last_modified = last_t.strftime("%m/%d/%Y %H:%M")
            file_size = os.path.getsize(fp)
            files_str += f"{last_modified : <15}{file_size : >10} {file : <12}\n"
        return files_str

    def open_in_external_editor(self, filename: str, editor: str, path: str = "", cmd: str = None):
        if cmd is None:
            cmd = f"{self.external_text_editor_options[editor]['call']} {self.external_text_editor_options[editor]['args']}"
        if "__FILE__" not in cmd:
            cmd = cmd + " " + filename
        cmd = cmd.replace("__PATH__", path)
        cmd = cmd.replace("__FILE__", filename)
        cmd = cmd.replace("__FILE_NAME__", os.path.basename(filename))
        dprint(f"external editor open command: {cmd}", color="yellow")
        subprocess.Popen(cmd, shell=True)

    def cowsay(self, *args, **kwargs):
        TYPE_OPTS = (TYPE_INFO, TYPE_INFO_GREEN, TYPE_INFO_CYAN, TYPE_INFO_PINK) 
        t = TYPE_INFO 
        if "-p" in kwargs: 
            t = TYPE_INFO_PINK
        elif not args and not kwargs: 
            t = random.choice(TYPE_OPTS)
        self.terminal_add_text(get_cow(*args, **kwargs), type=t)

    def sk_info(self, *args, **kwargs):
        if args:
            pstr = " ".join(args)
        else:
            pstr = GREETINGS_TEXT
        self.terminal_add_text(pstr, type=TYPE_INFO)

    ## Recursively print all children of the main window
    def sk_set(self, *args):
        dprint("sk_set", args)

        if not args:
            self.terminal_add_text(SK_SET_HELP, type=TYPE_INFO)
            return

        settings = {}
        for arg in args:
            if arg in ("-h", "--help"):
                self.terminal_add_text(SK_SET_HELP, type=TYPE_INFO)
                return
            elif arg in ("-ls", "--list"):
                for child in self.findChildren(QtWidgets.QLineEdit):
                    child: QtWidgets.QLineEdit
                    pstr = child.objectName() + "='" + child.text() + "'"
                    self.terminal_add_text(pstr, type=TYPE_INFO)
                for child in self.findChildren(QtWidgets.QComboBox):
                    child: QtWidgets.QComboBox
                    pstr = child.objectName() + "=" + child.currentText()
                    self.terminal_add_text(pstr, type=TYPE_INFO)
                for child in self.findChildren(QtWidgets.QCheckBox):
                    child: QtWidgets.QCheckBox
                    pstr = child.objectName() + "=" + str(child.isChecked())
                    self.terminal_add_text(pstr, type=TYPE_INFO)
                return
            elif "=" in arg:
                key, value = arg.split("=")
                settings[key] = value
            else:
                self.terminal_add_text(f"Invalid argument: {arg} sk-set args must be in the form of key=value", type=TYPE_ERROR)
                return

        for child in self.findChildren(QtWidgets.QLineEdit):
            child: QtWidgets.QLineEdit
            if child.objectName() in settings:
                value = settings.pop(child.objectName())
                child.setText(value)
                self.terminal_add_text(f"Set {child.objectName()} to {value}", type=TYPE_INFO_GREEN)
        for child in self.findChildren(QtWidgets.QComboBox):
            child: QtWidgets.QComboBox
            if child.objectName() in settings:
                value = settings.pop(child.objectName())
                if value in getComboBox_items(child):
                    child.setCurrentText(value)
                    self.terminal_add_text(f"Set {child.objectName()} to {value}", type=TYPE_INFO_GREEN)
                else:
                    self.terminal_add_text(f"Invalid value for {child.objectName()}: {value}", type=TYPE_ERROR)
        for child in self.findChildren(QtWidgets.QCheckBox):
            child: QtWidgets.QCheckBox
            if child.objectName() in settings:
                value = settings.pop(child.objectName())
                if value.lower() in ("false", "0", "n", ""):
                    child.setChecked(False)
                    self.terminal_add_text(f"Set {child.objectName()} to False", type=TYPE_INFO_GREEN)
                else:
                    child.setChecked(True)
                    self.terminal_add_text(f"Set {child.objectName()} to True", type=TYPE_INFO_GREEN)

        if settings:
            self.terminal_add_text(f"Invalid settings: {settings}", type=TYPE_ERROR)



    ############################################################
    ################### QUIT FUNCTIONS #######################
    ############################################################

    def closeEvent(self, event):
        if self.key_popup is not None:
            self.key_popup.reject()
            self.key_popup = None
        self.close()

    def make_quit(self, *args, **kwargs):
        dprint("-------EXITING-------", color="red")
        #print("key_popup", self.key_popup)
        if self.key_popup is not None:
            self.key_popup.reject()
            self.key_popup = None
        self.close()
        sys.exit()


# def get_table_dict(table: QtWidgets.QTableWidget) -> dict[str, str]:
#     items = {}
#     columns = []
#     default_dict = {}
    
#     for i in range(table.columnCount()):
#         s = table.horizontalHeaderItem(i).text()
#         if s:
#             columns.append(s)
#             default_dict[s] = None

#     print("columns", columns, default_dict)


#     for row in range(table.rowCount()):
#         if table.item(row, 0) is None:
#             continue
#         items[table.item(row, 0).text()] = copy.deepcopy(default_dict)
#     return items

def get_table_items(table: QtWidgets.QTableWidget) -> dict[str, str]:
    items = {}
    n_cols = table.columnCount()
    
    for row in range(table.rowCount()):
        if table.item(row, 0) is None:
            continue
        if n_cols == 2:
            items[table.item(row, 0).text()] = table.item(row, 1).text()
        else: 
            items[table.item(row, 0).text()] = []
            for col in range(1, n_cols):
                items[table.item(row, 0).text()].append(table.item(row, col).text())
    return items



def set_table_items(table: QtWidgets.QTableWidget, items: dict[str, str]):
    table.setRowCount(0)
    n_cols = table.columnCount()
    for key, value in items.items():
        table.insertRow(table.rowCount())
        if isinstance(value, list):
            table.setItem(table.rowCount() - 1, 0, QtWidgets.QTableWidgetItem(key))
            for i, v in enumerate(value):
                table.setItem(table.rowCount() - 1, i + 1, QtWidgets.QTableWidgetItem(v))
        else:
            table.setItem(table.rowCount() - 1, 0, QtWidgets.QTableWidgetItem(key))
            table.setItem(table.rowCount() - 1, 1, QtWidgets.QTableWidgetItem(value))
    table.setRowCount(table.rowCount() + 1)


def setComboBox_items(comboBox: QtWidgets.QComboBox, items: list[str]):
    items_str = [str(item) for item in items]
    comboBox.clear()
    comboBox.addItems(items_str)


def getComboBox_items(comboBox: QtWidgets.QComboBox) -> list[str]:
    return [comboBox.itemText(i) for i in range(comboBox.count())]


def run_app(size_x=700, size_y=700, open_commands=""):
    global app
    app = QtWidgets.QApplication(sys.argv)
    app_icon = QtGui.QIcon()
    app_icon.addFile(os.path.join(BASE_DIR, "img", "SK_Icon.png"))
    app.setWindowIcon(app_icon)
    style = GroupBoxProxyStyle(app.style())
    app.setStyle(style)
    if DEBUG_LEVEL > 0:
        cprint(GREETINGS_TEXT, color="green")
    window = MainWindow(open_commands=open_commands)
    window.setWindowIcon(app_icon)
    window.resize(size_x, size_y)
    window.show()
    app.aboutToQuit.connect(window.make_quit)
    status = app.exec()

    sys.exit(status)


if __name__ == "__main__":
    import SK

    SK.run()

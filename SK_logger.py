import os
from datetime import date
import logging
import time 
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from io import StringIO

from SK_common import *
from SK_serial_worker import SK_Port
import traceback

DEFAULT_LOG_NAME = "log-%y-%m-%d.txt"
DEFAULT_LOG_FORMAT = "%(Name)s\\t|%(asctime)s.%(msecs)03d|\\t%(message)s"
DEFAULT_TIME_FORMAT = "%I:%M:%S"

class SK_Logger(QObject):
    handler: logging.Handler = None
    formatter: logging.Formatter = None
    logger: logging.Logger = None 
    filepath: str = None 
    line_fmt:str = DEFAULT_LOG_FORMAT
    time_fmt:str = DEFAULT_TIME_FORMAT
    port_properties:dict = {"port": "None",
                            "Name": "None",
                            "Device": "None",
                            "Descr": "None",
                            "PID": "None",
                            "VID": "None",
                            "Mfgr": "None",
                            "SN": "None",
                            "Prod": "None"}

    active: bool = False 
    enabled = False 


    filename_changed = pyqtSignal(str)

    def __init__(self, filepath:str = None, line_fmt:str = None, time_fmt:str = None, port:SK_Port = None):
        if filepath is not None:
            self.filepath = filepath 
        if self.line_fmt is not None:
            self.line_fmt = line_fmt
        if self.time_fmt is not None:
            self.time_fmt = time_fmt
        self.set_serial_port(port)
        super().__init__()

    def parse_port_properties(self, port:SK_Port):
        if port is None:
            p = {
                "port": "None",
                "Name": "None",
                            "Device": "None",
                            "Descr": "None",
                            "PID": "None",
                            "VID": "None",
                            "Mfgr": "None",
                            "SN": "None",
                            "Prod": "None"}
            return p
        p = port.__dict__
        p["port"] = port.Name

        return p 

    def set_serial_port(self, port: SK_Port):
        self.port_properties = self.parse_port_properties(port)

    def set_enabled(self, enabled:int = 0):
        self.enabled = enabled 
        if self.enabled:
            self.start() 
        else:
            self.stop()

    def start(self):
        if self.active:
            self.stop()

        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.DEBUG)

        self.formatter = logging.Formatter(fmt = self.line_fmt, datefmt = self.time_fmt, validate = True)
        self.handler = logging.FileHandler(self.filepath)
        self.handler.setFormatter(self.formatter)
        self.logger.addHandler(self.handler)
        self.active = True

        self.filename_changed.emit("Current Log: " + self.filepath)

        vprint(f"Logger Started {self.filepath} \n\twith format {self.line_fmt} \n\tand time format {self.time_fmt}", color = "cyan")

    def stop(self):
        if self.logger is not None:
            for handler in self.logger.handlers:
                self.logger.removeHandler(handler)

        self.filename_changed.emit("Current Log: None")
        self.active = False 

    def write_line(self, text:str):
        if not self.enabled:
            return 
        try: 
            self.logger.warning(text, extra = self.port_properties)
        except Exception as e:
            vprint(f"Error writing to logger: {e}", color = "red")
            vprint(f"Text: {text}", color = "red")
            vprint(f"Traceback: {traceback.format_exc()}", color = "red")

    def write(self, text: str):
        if not self.enabled:
            return 
        text = text.rstrip()
        for line in text.splitlines():
            self.write_line(line)
        

    ## This function should return a sample of text that could be written to the logger
    def sample_output(self, input:str, line_fmt:str = None, time_fmt:str = None, port:SK_Port = None) -> str:
        #streamer = StringIO()
        temp_formatter = logging.Formatter(fmt = line_fmt, datefmt = time_fmt, validate = False)
        temp_logger = logging.getLogger(None)
        temp_logger.setLevel(logging.DEBUG)
        record = temp_logger.makeRecord(name = "test", level = logging.WARNING, fn = "test", lno = 1, msg = input, args = None, exc_info = None, extra = self.parse_port_properties(port))
        s = temp_formatter.format(record)
        #print(temp_formatter.format(record))
        return s



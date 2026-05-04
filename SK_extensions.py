from SK_common import * 
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
#from SK_main_window import MainWindow
from SK_serial_worker import SK_Port
import time 

EXTENSION_INTERNAL_DEBUG_COLOR = TYPE_INFO_PINK
EXTENSION_INTERNAL_DEBUG_LEVEL = 3

class SK_Extension(QObject):
    
    output = pyqtSignal(tuple)
    exit = pyqtSignal(str)
    serial_is_connected = False 
    started = False 
    debug_level = 0 
    name = "EXT"
    is_ending = False 

    def __init__(self, main_window):
        super().__init__()
        from SK_main_window import MainWindow
        self.main_window:MainWindow = main_window


    def start(self):
        self.started = True 
        if self.debug_level >= EXTENSION_INTERNAL_DEBUG_LEVEL:
            self.debug("Extension Started", debug_level = 0, type = EXTENSION_INTERNAL_DEBUG_COLOR)
        self.event_start()

    def _serial_connected(self, port:SK_Port = None):
        self.serial_is_connected = True
        if self.debug_level >= EXTENSION_INTERNAL_DEBUG_LEVEL:
            self.debug("Serial Connected", debug_level = 0, type = EXTENSION_INTERNAL_DEBUG_COLOR)
        self.event_serial_connected(port)
    
    def _receive_lines(self, lines:list[str]):
        if self.debug_level >= EXTENSION_INTERNAL_DEBUG_LEVEL:
            for line in lines: 
                self.debug(f"receive line: {line}", debug_level = 0, type = EXTENSION_INTERNAL_DEBUG_COLOR)
        start_t = time.perf_counter_ns() 
        r = self.event_receive_lines(lines) 
        end_t = time.perf_counter_ns() 
        if self.debug_level >= EXTENSION_INTERNAL_DEBUG_LEVEL + 1:
            self.debug(f"receive lines took {(end_t - start_t) / 1000} uS", debug_level = 0, type = EXTENSION_INTERNAL_DEBUG_COLOR)
        return r 

    def _serial_disconnected(self):
        if self.debug_level >= EXTENSION_INTERNAL_DEBUG_LEVEL:
            self.debug(f"Disconnected", debug_level = 0, type = EXTENSION_INTERNAL_DEBUG_COLOR)
        self.serial_connected = False
        self.event_serial_disconnected()
    
    def _receive_commands(self, commands:list[str]):
        if self.debug_level >= EXTENSION_INTERNAL_DEBUG_LEVEL:
            self.debug(f"Got Command: {commands}", debug_level = 0, type = EXTENSION_INTERNAL_DEBUG_COLOR)
        self.event_receive_commands(commands)

    def end(self, message:str = ""):
        self.is_ending = True 
        if self.debug_level >= EXTENSION_INTERNAL_DEBUG_LEVEL:
            self.debug(f"Extension Ended", debug_level = 0, type = EXTENSION_INTERNAL_DEBUG_COLOR)
        m = self.event_end()
        if m is not None: 
            message = m 
        self.started = False 
        self.exit.emit(message)


    def event_start(self):
        '''User-Defined event for when the extension is started'''
        self.debug("Default Start Event", debug_level=1)
        return None 

    def event_serial_connected(self, port:SK_Port = None): 
        '''User-Defined event for when the extension is connected to a serial port'''
        self.debug("Default Serial Connected Event", debug_level=1)
        return None 

    def event_serial_disconnected(self):
        '''User-Defined event for when the serial port is disconnected'''
        self.debug("Default Serial Disconnected Event", debug_level=1)
        return None 

    def event_receive_lines(self, lines:list[str]): 
        '''User-Defined event for when the extension recieves a line'''
        self.debug(f"Default Recieve Line Event, Line: {lines}", debug_level=1)
        return None 
    
    def event_receive_commands(self, commands:list[str]):
        '''User-Defined event for when the extension recieves a command'''
        self.debug(f"Default Recieve Command Event, Command: {commands}", debug_level=1)
        return None 

    def event_end(self) -> str:
        '''User-Defined event for when the extension is ended'''
        self.debug("Default End Event", debug_level=1)
        return None 

    def debug(self, *args, debug_level:int = 0, type:int = TYPE_INFO_MAGENTA, prefix:bool = True):
        '''This will send a debug message to the terminal. Prepended with the name of the extension. 
        If self.debug_level >= debug_level, the message will be output. 
        Type is the type of debug message send to the terminal. Usually TYPE_INFO, or TYPE_ERROR. Default is INFO with a magenta color. 
        '''
        if self.debug_level >= debug_level:
            s = ""
            if prefix:
                s = f"[{self.name}] "
            s += " ".join(str(arg) for arg in args)
            s = s.replace("\n", f"\n[{self.name}] ")
            self.output.emit((s, type))

    def send(self, text:str, interpret:bool = True):
        '''
        Send a message to the serial device. 
        Parameters
        ----------
        text: str
            The message to send to the serial device. 
        interpret: bool
            If True, the message will be copied to the "send" textbox in the main window. 
                All conditions apply (expressions, commands, and prepending/appending textboxes)
            If False, the message will be sent as raw text. newlines may need to be appended. 
        '''
        if interpret:
            type = TYPE_TX | TYPE_CONFIG_DEFAULT
        else:
            type = TYPE_TX | TYPE_CONFIG_RAW
        self.output.emit((text, type))

    

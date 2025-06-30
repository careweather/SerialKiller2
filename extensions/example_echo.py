import sys
import os 
sys.path.append("..")
from SK_common import * 
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from SK_extensions import SK_Extension
from SK_serial_worker import SK_Port

'''
This is a template for creating a custom extension for interacting with a serial device. 

The Extension works by reacting to events from the Main Window. 
To handle these events, override the functions in this template file. 

-------------------------------------------------------------------------------------------
SENDING DEBUGGING MESSAGES TO THE TERMINAL ----------------------------------------------------
-------------------------------------------------------------------------------------------

self.debug(*args, debug_level:int = 0, type:int = TYPE_INFO_MAGENTA):
    This is a debug function. All *args will be converted to strings and joined with spaces. (much like print())
    if self.debug_level >= debug_level, the message will be output. 
    Type is the type of debug message send to the terminal. Usually TYPE_INFO, or TYPE_ERROR. Default is TYPE_INFO_MAGENTA. 

self.debug_level: int = 0
    The debug level of the extension. This is used to determine if the extension should output debug messages.
    It may be set by the extension itself, or when the extension is loaded by the main window. 

-------------------------------------------------------------------------------------------
SENDING MESSAGES TO THE SERIAL DEVICE ----------------------------------------------------
-------------------------------------------------------------------------------------------

self.send(text:str, interpret:bool = True)
    This sends text to the connected device. 
    If interpret is True, it will be handled exactly as if it were typed in the terminal. 
    If False, it will be sent as raw text. Remember to append newline characters if required. 

self.serial_connected: bool = False 
    This will be True if a serial device is connected in the main SerialKiller Window. 

-------------------------------------------------------------------------------------------
OTHER USEFUL FUNCTIONS---------------------------------------------------------------------
-------------------------------------------------------------------------------------------

self.end()
    This will end the extension. 
    This is NOT the same as self.event_end(), which will be called shortly after self.end() is called. 

'''
class Extension(SK_Extension):
    '''To Be Loaded Correctly, the class must be named "Extension" and inherit the SK_Extension class. '''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ## Recomended to set the name of the extension to the name of the file
        self.name = os.path.splitext(os.path.basename(__file__))[0]

    '''User-Defined event for when the extension is started
    args* are optional arguments passed in when the extension is started'''
    def event_start(self, *args):
        self.debug("Extension Started?", debug_level = 0, type = TYPE_INFO_GREEN)
        return 

    '''User-Defined event for when a connection is made to a serial port'''
    '''If the extension is started with a port already connected, this will happen just after event_start()'''
    def event_serial_connected(self, port: SK_Port = None):
        self.debug(f"Serial Connected. Port mfgr {port.Mfgr}", debug_level = 0, type = TYPE_INFO_GREEN)
        return 
    
    '''User-Defined event triggered when the serial port is disconnected'''
    def event_serial_disconnected(self):
        self.debug("Serial Disconnected! What a tragedy!", debug_level = 0, type = TYPE_ERROR)
        return 

    '''User-Defined event for when the extension recieves lines from the serial device'''
    def event_receive_lines(self, lines:list[str]):
        for line in lines:
            self.debug(f"Got Line: {line}", debug_level = 0, type = TYPE_INFO_CYAN)
        return

    '''User-Defined event for extension commands i.e ext --commands [args]'''
    def event_receive_commands(self, commands:list[str]):
        for command in commands:
            self.debug(f"Got Command: {command}", debug_level = 0, type = TYPE_INFO_CYAN)
        return 

    '''User-Defined event that occurs when the extension is ended'''
    '''Note that calling this function will NOT end the extension by itself'''
    '''If you want to end the extension, you must call self.end(), which in turn will call this function'''
    def event_end(self):
        self.debug("Extension Ended", debug_level = 0, type = TYPE_INFO)
        return 
    



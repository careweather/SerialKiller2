import sys
import os 
sys.path.append("..")
from SK_common import * 
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from SK_extensions import SK_Extension
from SK_serial_worker import SK_Port
import socket 
import time 

HOST = "127.0.0.1"
PORT = 5555

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
    socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    killed = False 
    socket_connected = False 
    connection = None
    socket_timer = None
    accept_timer = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ## Recomended to set the name of the extension to the name of the file
        self.name = os.path.splitext(os.path.basename(__file__))[0]

    def check_for_connection(self):
        """Check for incoming client connections without blocking"""
        if self.killed or self.socket_connected:
            return
            
        try:
            # Set socket to non-blocking mode for accept
            self.socket.setblocking(False)
            
            # Try to accept a connection
            conn, addr = self.socket.accept()
            self.connection = conn
            self.socket_connected = True
            self.debug(f"Connected by {addr}")
            
            # Stop the accept timer since we have a connection
            if self.accept_timer:
                self.accept_timer.stop()
            
            # Start the socket timer to check for incoming data
            self.socket_timer.start(10)  # Check every 10ms
                
        except socket.error as e:
            # No connection available (EAGAIN/EWOULDBLOCK) or other error
            if e.errno in (socket.EAGAIN, socket.EWOULDBLOCK):
                pass  # No connection available, this is normal
            else:
                self.debug(f"Socket accept error: {e}", type = TYPE_ERROR)
                self.killed = True
        except Exception as e:
            self.debug(f"Unexpected error accepting connection: {e}", type = TYPE_ERROR)
            self.killed = True

    def check_socket_data(self):
        """Check for incoming data from the client without blocking"""
        if self.killed or not self.socket_connected or not self.connection:
            return
            
        try:
            # Set connection to non-blocking mode
            self.connection.setblocking(False)
            
            # Try to receive data
            data = self.connection.recv(1024)
            if data:
                s = data.decode("utf-8").rstrip().split("\n")
                #self.debug(f"Received data: {s}")
                for line in s:
                    self.send(line)
            elif not data:
                # Connection closed by client
                self.debug("Client disconnected")
                self.socket_connected = False
                self.connection.close()
                self.connection = None
                # Restart accept timer to wait for new connections
                if self.accept_timer:
                    self.accept_timer.start(100)
                
        except socket.error as e:
            # No data available (EAGAIN/EWOULDBLOCK) or connection closed
            if e.errno in (socket.EAGAIN, socket.EWOULDBLOCK):
                pass  # No data available, this is normal
            else:
                self.debug(f"Socket receive error: {e}", type = TYPE_ERROR)
                self.socket_connected = False
                if self.connection:
                    self.connection.close()
                    self.connection = None
        except Exception as e:
            self.debug(f"Unexpected error reading socket: {e}", type = TYPE_ERROR)
            self.socket_connected = False
            if self.connection:
                self.connection.close()
                self.connection = None

    '''User-Defined event for when the extension is started
    args* are optional arguments passed in when the extension is started'''
    def event_start(self, *args):
        self.killed = False 
        self.debug("Starting Server Extension")
        
        # Set up the server socket
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((HOST, PORT))
        self.socket.listen(1)
        self.debug("Waiting for connection... Start the client extension to connect")
        
        # Set up timer to check for incoming connections
        self.accept_timer = QTimer()
        self.accept_timer.timeout.connect(self.check_for_connection)
        self.accept_timer.start(100)  # Check every 100ms
        
        # Set up timer to check for incoming data (will be started when connection is established)
        self.socket_timer = QTimer()
        self.socket_timer.timeout.connect(self.check_socket_data)
        
        return 

    '''User-Defined event for when a connection is made to a serial port'''
    '''If the extension is started with a port already connected, this will happen just after event_start()'''
    def event_serial_connected(self, port: SK_Port = None):
        return 
    
    '''User-Defined event triggered when the serial port is disconnected'''
    def event_serial_disconnected(self):
        return 

    '''User-Defined event for when the extension recieves lines from the serial device'''
    def event_receive_lines(self, lines:list[str]):
        if not self.socket_connected or not self.connection:
            #self.debug("Socket not connected", type = TYPE_ERROR)
            return 
        for line in lines:
            line = line + "\n"
            #self.debug("SENDING TO CLIENT: " + line, type = TYPE_INFO)
            try:
                self.connection.sendall(line.encode("utf-8"))
            except Exception as e:
                self.debug(f"Error sending to client: {e}", type = TYPE_ERROR)
                self.socket_connected = False
                self.connection.close()
                self.connection = None
                # Restart accept timer to wait for new connections
                if self.accept_timer:
                    self.accept_timer.start(100)

    '''User-Defined event for extension commands i.e ext --commands [args]'''
    def event_receive_commands(self, commands:list[str]):
        return 

    '''User-Defined event that occurs when the extension is ended'''
    '''Note that calling this function will NOT end the extension by itself'''
    '''If you want to end the extension, you must call self.end(), which in turn will call this function'''
    def event_end(self):
        self.killed = True 
        if self.socket_timer:
            self.socket_timer.stop()
        if self.accept_timer:
            self.accept_timer.stop()
        if self.connection:
            self.connection.close()
        time.sleep(.1)
        self.socket.close()
        self.debug("Socket closed")
        return 
    


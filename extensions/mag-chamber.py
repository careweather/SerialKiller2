import sys
import os 
sys.path.append("..")
from SK_common import * 
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from SK_extensions import SK_Extension
from SK_serial_worker import SK_Port
import time 
import socket 



HOST = "127.0.0.1"
PORT = 5555
SPHERE_POINTS_FILE = os.path.join(os.path.dirname(__file__), "sphere_points.txt")

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
    sleep_time = .1 
    sphere_points = []
    sphere_point_index = 0
    killed = False 
    socket_timer = None
    serial_number = "sn-unknown"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ## Recomended to set the name of the extension to the name of the file
        self.name = os.path.splitext(os.path.basename(__file__))[0]


    def send_to_server(self, msg:str):
        self.debug("SENDING TO SERVER: " + msg, type = TYPE_INFO)
        send_msg = msg.encode("utf-8") + b"\n"
        try: 
            self.socket.sendall(send_msg)
        except Exception as E:
            self.debug(f"SOCKET BROKEN!!! Ensure server extension is running Error: {E}", type = TYPE_ERROR)
            #self.end()

    def check_socket_data(self):
        """Check for incoming data from the socket without blocking"""
        if self.killed:
            return
            
        try:
            # Set socket to non-blocking mode
            self.socket.setblocking(False)
            
            # Try to receive data
            lines = self.socket.recv(1024).decode("utf-8").split("\n")
            for line in lines:
                if line:
                    if line.startswith("sn="):
                        self.serial_number = line.split("=")[1].replace(";", "")
                    elif line.startswith("MAGX:"):
                        self.debug(f'[{self.sphere_point_index}]', line, type = TYPE_INFO)
                        self.sphere_point_index += 1
                        if self.sphere_point_index >= len(self.sphere_points):
                            self.sphere_point_index = 0
                            self.end() 
                        else: 
                            self.send(f'target={self.sphere_points[self.sphere_point_index]}')
                
        except socket.error as e:
            # No data available (EAGAIN/EWOULDBLOCK) or connection closed
            if e.errno in (socket.EAGAIN, socket.EWOULDBLOCK):
                pass  # No data available, this is normal
            else:
                self.debug(f"Socket error: {e}", type = TYPE_ERROR)
                self.killed = True
        except Exception as e:
            self.debug(f"Unexpected error reading socket: {e}", type = TYPE_ERROR)
            self.killed = True

    '''User-Defined event for when the extension is started
    args* are optional arguments passed in when the extension is started'''
    def event_start(self, *args):
        with open(SPHERE_POINTS_FILE, "r") as f:
            for line in f:
                line = line.strip().rstrip()
                if line:
                    self.sphere_points.append(line)
                    #self.debug(line, type = TYPE_INFO)

        self.debug(f"Loaded {len(self.sphere_points)} sphere points", type = TYPE_INFO)
        self.socket.connect((HOST, PORT))
        #self.send_to_server("sk-info testing\n")
        
        # Set up timer to check for socket data periodically
        self.socket_timer = QTimer()
        self.socket_timer.timeout.connect(self.check_socket_data)
        self.socket_timer.start(10)  # Check every 10ms
        time.sleep(.1)
        self.send_to_server(f'plot kv --keys "MAGX,MAGY,MAGZ,MAG2X,MAG2Y,MAG2Z,MAG3X,MAG3Y,MAG3Z" --points {len(self.sphere_points) + 1} --title "MAG CAL"')
        time.sleep(.05)
        self.send_to_server("i.cancel;i.int=0;p.int=0;i.cfg=0;")
        time.sleep(.1)
        self.send_to_server("sn") 


        
        return 

    '''User-Defined event for when a connection is made to a serial port'''
    '''If the extension is started with a port already connected, this will happen just after event_start()'''
    def event_serial_connected(self, port: SK_Port = None):
        #self.send("i.cancel;i.int=0;p.int=0;")
        self.send("tol=15;")
        time.sleep(.2)
        self.sphere_point_index = 0
        self.send(f'target={self.sphere_points[self.sphere_point_index]}')

        #self.send_to_client(f'plot kv --keys "MAGX,MAGY,MAGZ,MAG2X,MAG2Y,MAG2Z,MAG3X,MAG3Y,MAG3Z" --points {len(self.sphere_points) + 1} --title "MAG CAL"')
        return 
    
    '''User-Defined event triggered when the serial port is disconnected'''
    def event_serial_disconnected(self):
        return 

    '''User-Defined event for when the extension recieves lines from the serial device'''
    def event_receive_lines(self, lines:list[str]):
        for line in lines:
            if line.startswith("DONE: "):
                self.send_to_server(f"mags.raw")
                #self.sphere_point_index += 1

        return

    '''User-Defined event for extension commands i.e ext --commands [args]'''
    def event_receive_commands(self, commands:list[str]):
        return 

    '''User-Defined event that occurs when the extension is ended'''
    '''Note that calling this function will NOT end the extension by itself'''
    '''If you want to end the extension, you must call self.end(), which in turn will call this function'''
    def event_end(self):
        self.send("stop")
        export_name = f"mag-cal-{self.serial_number}.csv"
        self.send_to_server(f"plot export {export_name}")
        time.sleep(.1)
        self.send_to_server(f"log -o {export_name}")
        self.killed = True 
        if self.socket_timer:
            self.socket_timer.stop()
        time.sleep(.1)
        self.socket.close() 
        self.debug("Socket closed")
        return 
    


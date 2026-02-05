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

# Available test modes and their corresponding sphere point files
EXTENSION_DIR = os.path.dirname(__file__)
TEST_MODES = {
    "cal":      ("sphere_points.txt",       "Full Calibration (700mG sphere)"),
    "leo":      ("leo_sphere_points.txt",   "LEO Residual Test (200 points, 300-600mG)"),
    "leo-quick":("leo_specific_tests.txt",  "LEO Quick Test (21 key vectors)"),
}
DEFAULT_MODE = "leo"

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
    '''To Be Loaded Correctly, the class must be named "Extension" and inherit the SK_Extension class. 
    
    Usage modes (pass as argument when starting extension):
        ext mag-chamber           - Full calibration mode (default, 700mG sphere)
        ext mag-chamber leo       - LEO residual test (200 points, 300-600mG)
        ext mag-chamber leo-quick - LEO quick test (21 key vectors)
        ext mag-chamber help      - Show available modes
    '''


    socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sleep_time = .1 
    sphere_points = []
    sphere_point_index = 0
    killed = False 
    socket_timer = None
    serial_number = "sn-unknown"
    test_mode = DEFAULT_MODE
    sphere_points_file = None
    
    # Settling time (ms) to wait after DONE before reading magnetometers
    # This allows the magnetic field and magnetometer readings to stabilize
    SETTLE_TIME_MS = 500  # Adjust this value as needed (try 200-1000ms)

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
                    # Debug: show all received lines
                    self.debug(f'[RECV] "{line}"', type = TYPE_INFO_MAGENTA)
                    
                    if line.startswith("sn="):
                        self.serial_number = line.split("=")[1].replace(";", "")
                    elif line.startswith("MAGX:"):
                        # Log MAG1 reading (one line: MAGX: ... MAGY: ... MAGZ: ...)
                        self.debug(f'[{self.sphere_point_index}] MAG1: {line}', type = TYPE_INFO)
                        # For calibration mode (mags.raw), MAG1 output triggers advancement
                        # since all 3 mags are output together in a different format
                        if self.test_mode == 'cal':
                            self._advance_to_next_point()
                    elif line.startswith("MAG2X:"):
                        # Log MAG2 reading for debugging
                        self.debug(f'[{self.sphere_point_index}] MAG2: {line}', type = TYPE_INFO)
                    elif line.startswith("MAG3X:"):
                        # For leo/leo-quick modes: MAG3X line is the last magnetometer
                        # Format: MAG3X: ... MAG3Y: ... MAG3Z: ... (all on one line)
                        # Now all 3 magnetometers have been recorded, safe to advance
                        self.debug(f'[{self.sphere_point_index}] MAG3: {line}', type = TYPE_INFO)
                        self.debug(f'[{self.sphere_point_index}] All mags recorded, advancing to next point', type = TYPE_INFO)
                        if self.test_mode != 'cal':
                            self._advance_to_next_point()
                
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
    args* are optional arguments passed in when the extension is started
    
    Usage:
        ext mag-chamber           - Full calibration mode (default)
        ext mag-chamber leo       - LEO residual test (200 points)
        ext mag-chamber leo-quick - LEO quick test (21 key vectors)
        ext mag-chamber help      - Show available modes
        
    Options (can be combined with mode):
        ext mag-chamber leo settle=1000  - Set settling time to 1000ms
    '''
    def event_start(self, *args):
        # Parse arguments
        mode_arg = None
        for arg in args:
            arg = arg.strip()
            
            # Check for settle time option
            if arg.lower().startswith("settle="):
                try:
                    self.SETTLE_TIME_MS = int(arg.split("=")[1])
                    self.debug(f"Settling time set to {self.SETTLE_TIME_MS}ms", type=TYPE_INFO)
                except ValueError:
                    self.debug(f"Invalid settle time: {arg}", type=TYPE_ERROR)
                continue
            
            # First non-option arg is the mode
            if mode_arg is None:
                mode_arg = arg.lower()
        
        if mode_arg:
            # Handle help command
            if mode_arg in ["help", "-h", "--help", "?"]:
                self.debug("=" * 50, type=TYPE_INFO)
                self.debug("MAG-CHAMBER EXTENSION - Available Modes:", type=TYPE_INFO)
                self.debug("=" * 50, type=TYPE_INFO)
                for mode, (filename, description) in TEST_MODES.items():
                    self.debug(f"  {mode:<12} - {description}", type=TYPE_INFO)
                self.debug("", type=TYPE_INFO)
                self.debug("Usage: ext mag-chamber [mode] [options]", type=TYPE_INFO)
                self.debug("Example: ext mag-chamber leo-quick", type=TYPE_INFO)
                self.debug("", type=TYPE_INFO)
                self.debug("Options:", type=TYPE_INFO)
                self.debug(f"  settle=N     - Settling time in ms (default: {self.SETTLE_TIME_MS})", type=TYPE_INFO)
                self.debug("=" * 50, type=TYPE_INFO)
                self.end()
                return
            
            # Set mode if valid
            if mode_arg in TEST_MODES:
                self.test_mode = mode_arg
            else:
                self.debug(f"Unknown mode: '{mode_arg}'. Use 'help' to see available modes.", type=TYPE_ERROR)
                self.debug(f"Falling back to default mode: '{DEFAULT_MODE}'", type=TYPE_INFO)
                self.test_mode = DEFAULT_MODE
        else:
            self.test_mode = DEFAULT_MODE
        
        # Get sphere points file for this mode
        filename, description = TEST_MODES[self.test_mode]
        self.sphere_points_file = os.path.join(EXTENSION_DIR, filename)
        
        # Check if file exists
        if not os.path.exists(self.sphere_points_file):
            self.debug(f"ERROR: Sphere points file not found: {self.sphere_points_file}", type=TYPE_ERROR)
            if self.test_mode != "cal":
                self.debug("Run 'python3 generate_leo_test_points.py' to create LEO test files", type=TYPE_ERROR)
            self.end()
            return
        
        self.debug("=" * 50, type=TYPE_INFO)
        self.debug(f"MODE: {self.test_mode} - {description}", type=TYPE_INFO)
        self.debug(f"FILE: {filename}", type=TYPE_INFO)
        self.debug("=" * 50, type=TYPE_INFO)
        
        # Load sphere points
        self.sphere_points = []
        with open(self.sphere_points_file, "r") as f:
            for line in f:
                line = line.strip().rstrip()
                if line:
                    self.sphere_points.append(line)

        self.debug(f"Loaded {len(self.sphere_points)} sphere points", type = TYPE_INFO)
        self.socket.connect((HOST, PORT))
        
        # Set up timer to check for socket data periodically
        self.socket_timer = QTimer()
        self.socket_timer.timeout.connect(self.check_socket_data)
        self.socket_timer.start(10)  # Check every 10ms
        time.sleep(.1)
        
        # Set plot title based on mode
        if self.test_mode == "cal":
            plot_title = "MAG CAL"
        else:
            plot_title = f"MAG RESIDUAL TEST ({self.test_mode})"
        
        self.send_to_server(f'plot kv --keys "MAGX,MAGY,MAGZ,MAG2X,MAG2Y,MAG2Z,MAG3X,MAG3Y,MAG3Z" --points {len(self.sphere_points) + 1} --title "{plot_title}"')
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

    def _request_mag_readings(self):
        """Called after settling delay to request magnetometer readings"""
        if self.killed:
            return
        if self.test_mode == 'cal':
            self.send_to_server(f"mags.raw")
        elif self.test_mode == 'leo' or self.test_mode == 'leo-quick':
            self.send_to_server(f"mag.print;mag2.print;mag3.print;")

    def _advance_to_next_point(self):
        """Advance to the next sphere point after all magnetometer readings are recorded"""
        self.sphere_point_index += 1
        if self.sphere_point_index >= len(self.sphere_points):
            self.sphere_point_index = 0
            self.end() 
        else: 
            self.send(f'target={self.sphere_points[self.sphere_point_index]}')

    '''User-Defined event for when the extension recieves lines from the serial device'''
    def event_receive_lines(self, lines:list[str]):
        for line in lines:
            if line.startswith("DONE: "):
                # Wait for magnetic field and magnetometers to stabilize before reading
                self.debug(f"[{self.sphere_point_index}] Field set, waiting {self.SETTLE_TIME_MS}ms to stabilize...", type=TYPE_INFO)
                QTimer.singleShot(self.SETTLE_TIME_MS, self._request_mag_readings)

        return

    '''User-Defined event for extension commands i.e ext --commands [args]'''
    def event_receive_commands(self, commands:list[str]):
        return 

    '''User-Defined event that occurs when the extension is ended'''
    '''Note that calling this function will NOT end the extension by itself'''
    '''If you want to end the extension, you must call self.end(), which in turn will call this function'''
    def event_end(self):
        self.send("stop")
        
        # Use mode-specific export name
        if self.test_mode == "cal":
            export_name = f"mag-cal-{self.serial_number}.csv"
        else:
            export_name = f"mag-residual-{self.test_mode}-{self.serial_number}.csv"
        
        self.send_to_server(f"plot export {export_name}")
        time.sleep(.1)
        self.send_to_server(f"log -o {export_name}")
        self.killed = True 
        if self.socket_timer:
            self.socket_timer.stop()
        time.sleep(.1)
        self.socket.close() 
        self.debug("Socket closed")
        self.debug(f"Data exported to: {export_name}", type=TYPE_INFO)
        return 
    


import sys
import os 
import csv
sys.path.append("..")
from SK_common import * 
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from SK_extensions import SK_Extension
from SK_serial_worker import SK_Port

class Extension(SK_Extension):
    '''CSV Magnetometer Data Reader Extension for SerialKiller2'''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.name = os.path.splitext(os.path.basename(__file__))[0]
        self.csv_data = []
        self.current_index = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.send_next_data)
        self.delay_ms = 250  # Default delay between sends

    def event_start(self, *args):
        self.debug("CSV Magnetometer Reader Extension Started", debug_level=0, type=TYPE_INFO_GREEN)
        if len(args) > 0:
            csv_file = args[0]
            self.load_csv_file(csv_file)
        else:
            self.debug("No CSV file provided. Use: ext csv_mag_reader <csv_file>", debug_level=0, type=TYPE_ERROR)

    def event_serial_connected(self, port: SK_Port = None):
        self.debug(f"Serial Connected to {port.Name}", debug_level=0, type=TYPE_INFO_GREEN)
        return 
    
    def event_serial_disconnected(self):
        self.debug("Serial Disconnected", debug_level=0, type=TYPE_ERROR)
        self.timer.stop()
        return 

    def event_receive_lines(self, lines: list[str]):
        # Handle any responses from the device if needed
        for line in lines:
            self.debug(f"Received: {line}", debug_level=1, type=TYPE_INFO_CYAN)
        return

    def event_receive_commands(self, commands: list[str]):
        for command in commands:
            if command == "start":
                self.start_sending_data()
            elif command == "stop":
                self.stop_sending_data()
            elif command == "reset":
                self.current_index = 0
                self.debug("Reset to beginning of data", debug_level=0, type=TYPE_INFO)
            elif command.startswith("delay="):
                try:
                    self.delay_ms = int(command.split("=")[1])
                    self.debug(f"Set delay to {self.delay_ms}ms", debug_level=0, type=TYPE_INFO)
                except:
                    self.debug("Invalid delay format. Use: delay=<milliseconds>", debug_level=0, type=TYPE_ERROR)
            elif command.endswith('.csv') or '/' in command:
                # Handle CSV file path as command (fallback for when args don't work)
                self.debug(f"Loading CSV file from command: {command}", debug_level=0, type=TYPE_INFO)
                self.load_csv_file(command)
            else:
                self.debug(f"Unknown command: {command}", debug_level=0, type=TYPE_ERROR)
        return 

    def event_end(self):
        self.timer.stop()
        self.debug("CSV Magnetometer Reader Extension Ended", debug_level=0, type=TYPE_INFO)
        return 

    def load_csv_file(self, csv_file_path: str):
        """Load CSV file and parse magnetometer data"""
        try:
            self.csv_data = []
            with open(csv_file_path, 'r') as file:
                csv_reader = csv.reader(file)
                header = next(csv_reader)  # Skip header
                self.debug(f"CSV Header: {header}", debug_level=0, type=TYPE_INFO)
                
                for row in csv_reader:
                    if len(row) >= 4:  # time, HX, HY, HZ
                        try:
                            hx = round(float(row[1]), 1)
                            hy = round(float(row[2]), 1)
                            hz = round(float(row[3]), 1)
                            self.csv_data.append((hx, hy, hz))
                        except ValueError:
                            self.debug(f"Skipping invalid row: {row}", debug_level=0, type=TYPE_ERROR)
                            continue
                
                self.debug(f"Loaded {len(self.csv_data)} magnetometer data points", debug_level=0, type=TYPE_INFO_GREEN)
                self.current_index = 0
                
        except FileNotFoundError:
            self.debug(f"CSV file not found: {csv_file_path}", debug_level=0, type=TYPE_ERROR)
        except Exception as e:
            self.debug(f"Error loading CSV file: {str(e)}", debug_level=0, type=TYPE_ERROR)

    def start_sending_data(self):
        """Start sending magnetometer data"""
        if not self.csv_data:
            self.debug("No CSV data loaded", debug_level=0, type=TYPE_ERROR)
            return
        
        if not self.serial_connected:
            self.debug("Serial not connected", debug_level=0, type=TYPE_ERROR)
            return
            
        self.debug(f"Starting to send data at {self.delay_ms}ms intervals", debug_level=0, type=TYPE_INFO_GREEN)
        self.timer.start(self.delay_ms)

    def stop_sending_data(self):
        """Stop sending magnetometer data"""
        self.timer.stop()
        self.debug("Stopped sending data", debug_level=0, type=TYPE_INFO)

    def send_next_data(self):
        """Send the next magnetometer data point"""
        if not self.csv_data or self.current_index >= len(self.csv_data):
            self.debug("Reached end of data", debug_level=0, type=TYPE_INFO)
            self.timer.stop()
            return
        
        hx, hy, hz = self.csv_data[self.current_index]
        target_command = f"target={hx},{hy},{hz};"
        
        self.send(target_command, interpret=True)
        self.debug(f"Sent: {target_command} (point {self.current_index + 1}/{len(self.csv_data)})", debug_level=1, type=TYPE_INFO_CYAN)
        
        self.current_index += 1

import time
import traceback
import serial
import serial.tools.list_ports
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
import serial.tools.list_ports_linux
from SK_common import *
from pprint import pprint

ser = serial.Serial()
from dataclasses import dataclass


def debug_bytes(data: bytes):
    s = data.decode("utf-8", errors="replace")
    print("\n---")
    for index, byte in enumerate(data):
        c = chr(byte)
        if c == "\n":
            c = "LF"
            print(f"{byte}<{c}>,")

        elif c == "\r":
            c = "CR"
            print(f"{byte}<{c}>,", end="")
        elif byte == 27:
            c = "ESC"
            print(f"{byte}<{c}>,", end="")
        elif byte == 127:
            c = "DEL"
            print(f"{byte}<{c}>,", end="")
        else:
            print(f"{byte}<{c}>,", end="")
    print("\n---")


class SerialWorker(QObject):
    raw = pyqtSignal(bytes)
    text = pyqtSignal(str)
    error = pyqtSignal(str)
    lines = pyqtSignal(list)
    line_buffer = ""
    text_buffer = ""
    bytes_buffer = bytearray(2048)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.last_activity = time.perf_counter()
        self.active = True
        self.line_buffer = ""
        self.text_buffer = ""
        self.escape_buffer = None
        # ser.set_low_latency_mode(True)
        # ser.readinto()

    def wait_for_main(self):
        start_time = time.perf_counter()
        while self.main_busy:
            if time.perf_counter() - start_time > 0.1:
                eprint("Serial Worker Main Busy Timeout", color="red")
                self.main_busy = False
                return 0

        return time.perf_counter() - start_time

    def run(self):
        while self.active:
            try:
                in_waiting = ser.in_waiting
                if in_waiting and ser.is_open:
                    self.last_activity = time.perf_counter()
                    raw = ser.read(in_waiting)
                    self.raw.emit(raw)
                    text = self.line_buffer + raw.decode("utf-8", errors="replace")
                    lines = text.splitlines()
                    if text.endswith("\n") or text.endswith("\r"):
                        self.lines.emit(lines)
                        self.line_buffer = ""
                    else:
                        self.lines.emit(lines[:-1])
                        self.line_buffer = lines[-1]
                    end_t = time.perf_counter()
                    if DEBUG_LEVEL & 128:
                        cprint(f"Serial Read Time: {(end_t - self.last_activity) * 1000000:.3f}us Size: {in_waiting}", color="blue")

                elif (time.perf_counter() - self.last_activity) > 1.00:
                    time.sleep(0.02)
            except Exception as E:
                eprint(f"Serial Worker Error: {traceback.format_exc()}\n", color="red")
                self.error.emit(str(E))
                self.active = False

    def stop(self):
        self.active = False


###############################################################
######################## PORTS ########################
###############################################################


@dataclass
class SK_Port:
    Name: str = None
    Device: str = None
    Descr: str = None
    PID: str = None
    VID: str = None
    Mfgr: str = None
    SN: str = None
    Prod: str = None
    Alias: str = None
    Display: str = None
    Settings : str = None 

    def __post_init__(self):
        self.Display = self.Device if not self.Alias else self.Alias

    def __repr__(self):
        return self.Display

    def __eq__(self, value: object) -> bool:
        if isinstance(value, SK_Port):
            if value.SN == self.SN:
                return True
            return False
        if isinstance(value, int):
            value = str(value)
        if isinstance(value, str):
            if not value:
                return False
            if value == self.Name:
                return True
            elif value == self.SN:
                return True
            elif value == self.Device:
                return True
            elif value == self.PID:
                return True
            elif value == self.VID:
                return True
            elif value == self.Alias:
                return True

        return False

    def info(self, detail: bool = False) -> str:
        s = ""
        for element in self.__dict__:
            s += f"\t{element}: \t{self.__dict__[element]}\n"

        return s


def find_serial_port(port_name: str, ports: list[SK_Port]) -> SK_Port | None:
    for port in ports:
        if port_name == port:
            return port

    for port in ports:
        if port.Display.endswith(port_name):
            return port

    return None


###############################################################
######################## RESCAN WORKER ########################
###############################################################


def get_ports(aliases: dict = None) -> dict:
    ports = []
    for port in serial.tools.list_ports.comports():
        alias = None
        settings = None
        if aliases:
            for key, value in aliases.items():
                if port.serial_number == key:
                    alias = value[0]
                    settings = value[1]
                    break
        if not port.manufacturer:
            continue
        this_port = SK_Port(str(port.name), str(port.device), str(port.description), str(port.pid), str(port.vid), str(port.manufacturer), str(port.serial_number), str(port.product), alias, settings)
        ports.append(this_port)

        
    return ports


class RescanWorker(QObject):
    new_ports = pyqtSignal(list)
    active = False
    update_interval = 400
    existing_ports = []

    aliases = None 

    def __init__(self, *args, existing_ports=[], **kwargs):
        self.existing_ports = existing_ports
        super().__init__(*args, **kwargs)

    def run(self):
        self.active = True
        while self.active:
            try:
                new_ports = get_ports(self.aliases)
                if self.existing_ports != new_ports:
                    self.existing_ports = new_ports
                    self.new_ports.emit(new_ports)
                time.sleep(self.update_interval / 1000)
            except Exception as e:
                print(e)

    def rescan(self):
        ports = get_ports()
        # print(ports)

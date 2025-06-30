import PyQt6.QtCore as QtCore
from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtGui import QTextCharFormat, QTextCursor, QSyntaxHighlighter
from PyQt6.QtWidgets import QTextEdit
import time 
from SK_common import * 
import shlex


class Loop_Struct:
    end_index: int = None 
    index:int = 0 
    increment:int = 1 

    start_line:int = 0
    def __init__(self, start_line:int, index:int = 0, end_index:int = None, increment:int = 1):
        self.start_line = start_line
        self.index = index
        self.end_index = end_index
        self.increment = increment

    def __str__(self):
        return str(self.index)
    
    def __repr__(self):
        return str(self.index)
    
    def hit(self):
        self.index += self.increment
        if self.end_index is None:
            return False 
        
        if self.increment > 0:
            if self.index >= self.end_index:
                return True 
        else:
            if self.index <= self.end_index:
                return True 
        
        return False 


class ScriptWorker(QObject):
    output = pyqtSignal(tuple)
    finished = pyqtSignal(str)


    active = False
    is_exiting = False 
    delay:float = 100 # ms
    on_exit:list[str] = []
    vars: dict = {}
    lines:list[str] = []
    start_time:float = 0
    current_line:int = 0

    delay_timer:QTimer = None

    timeout:int = 1000

    loops:list[Loop_Struct] = []

    def __init__(self, text:str = None, delay:float = 100, args:list[str] = []):
        super().__init__()
        self.lines = text.split("\n")
        self.total_lines = len(self.lines)
        self.exit_commands:list[str] = []
        self.input_args: list[str] = list(args)
        self.delay = delay
        self.delay_timer = QTimer()
        self.delay_timer.setSingleShot(True)
        #self.delay_timer.timeout.connect(self.next_line)
        self.timeout_timer = QTimer()
        self.last_send_time = -self.delay
        self.vars["$ARG"] = self.input_args
        dprint(f"[SCRIPT] Script Initialized\nTEXT---------------\n{text}\nARGS---------------\n{args}\nDELAY---------------\n{delay}", color="green")

        print(f"ID: {self.delay_timer.timerId()} {self.delay_timer.isActive()}")

    def recieve(self, input:str):
        pass

    def send(self, output:str):
        remaining = self.delay - ((time.perf_counter() - self.last_send_time) * 1000)
        
        if remaining <= 0:
            self.last_send_time = time.perf_counter()
            self.output.emit((output, TYPE_TX))
            return True 
        else: 
            self.delay_timer.singleShot(int(remaining), self.next_line)
            return False 

    def handle_command(self, command:str):
        command = command.strip()
        vprint(f"[SCRIPT] Command: {command}", color="yellow")
        if command.startswith("loop"):
            command = command.replace("=", " ").replace(",", " ")
            toks = command.split(" ")
            increment = 1 
            end_index = None 
            start_index = 0 

            if len(toks) == 2:
                a = int(toks[1])
                if a > 0: 
                    end_index = a 
                else: 
                    end_index = 0 
                    start_index = -a 
                    increment = -1 
            elif len(toks) == 3:
                start_index = int(toks[1])
                end_index = int(toks[2])
                if start_index > end_index:
                    increment = -1 
            elif len(toks) == 4:
                start_index = int(toks[1])
                end_index = int(toks[2])
                increment = int(toks[3])

            

            self.loops.insert(0, Loop_Struct(start_line=self.current_line, index=start_index, end_index=end_index, increment=increment))
            self.vars["$LOOP"] = self.loops
            
            vprint(f"[SCRIPT] Loop Added: {self.loops[0]}", color="green")
            return True 
        
        if command.startswith("endloop"):
            if not self.loops:
                dprint("[SCRIPT] No loop to end", color="red")
                return True 
            
            if self.loops[0].hit():
                self.loops.pop(0)
            else: 
                self.current_line = self.loops[0].start_line
            return True 
        
        if command.startswith("exitcmd="):
            self.on_exit.append(command.split("=", 1)[1])
            return True 
        
        if command.startswith("info-g="):
            self.output.emit((command.split(" ", 1)[1], TYPE_INFO_GREEN))
            return True 

        if command.startswith("info="):
            self.output.emit((command.split("=", 1)[1], TYPE_INFO))
            return True 
    
        
        if command.startswith("error="):
            self.output.emit((command.split("=", 1)[1], TYPE_ERROR))
            return True 

        if command.startswith("args"):
            if command.startswith("args="):
                command = command.replace("args=", "args ")
            tokens = shlex.split(command.split(" ", 1)[1])
            len_input_args = len(self.input_args)
            for index, token in enumerate(tokens): 
                if index >= len_input_args:
                    self.input_args.append(token)

            vprint(f"Input Args: {self.input_args}", color="green")
            self.vars["$ARG"] = self.input_args
            return True 

        if command.startswith("delay"):
            command = command.replace("=", " ").replace(",", " ")
            self.delay = float(command.split(" ")[1])
            return True 
        
        if command.startswith("timeout"):
            command = command.replace("=", " ").replace(",", " ")
            self.timeout = int(float(command.split(" ")[1]))
            return True 
        
        if command.startswith("wait"):
            command = command.replace("=", " ").replace(",", " ")
            toks = command.split(" ")
            if len(toks) == 2:
                dur = float(toks[1])    
                vprint(f"[SCRIPT] Waiting for {dur}ms", color="yellow")
                if dur > 0:
                    self.delay_timer.stop()
                    self.delay_timer.singleShot(int(dur), self.next_line)
            self.current_line += 1
            return False 
        
        if command == "stop" or command == "end" or command == "exit":
            toks = command.split(" ", 1)
            stop_message = ""
            if len(toks) > 1:
                stop_message = toks[1]
            #self.active = False
            self.stop(stop_message)
            return False
        
        self.output.emit((command, TYPE_SRC_COMMAND))
        
        return True 
    
    def wait_for_input(self, input:str):
        pass

    def replace_vars(self, line: str) -> str:
        """Replace variables in the line with their values, including list indexing."""
        for var in self.vars:
            if var in line:
                
            
                # Handle list variables differently
                if isinstance(self.vars[var], (list, tuple)):
                    str_rep = ""
                    for v in self.vars[var]:
                        str_rep += f"{v} "
                    if len(self.vars[var]) == 0:
                        line = line.replace(var, "")
                        continue
                    for i in range(len(self.vars[var]), 0, -1):
                        possible_replace = f"{var}{i-1}"
                        if possible_replace in line:
                            line = line.replace(possible_replace, str(self.vars[var][i-1]))
                        
                    line = line.replace(var, str_rep.removesuffix(" "))
                else:
                    # For non-list variables, just do a simple replacement
                    line = line.replace(var, str(self.vars[var]))
        return line

    def execute(self, line:str):
        if not self.active or self.is_exiting:
            return False 

        vprint(f"[SCRIPT] Executing: {line}", color="blue")
        if f"\{SCRIPT_CHAR_COMMENT}" in line: 
            line = line.replace(SCRIPT_CHAR_COMMENT, chr(0x00))
        if SCRIPT_CHAR_COMMENT in line: ## Comments 
            line = line.split(SCRIPT_CHAR_COMMENT, 1)[0]
        if not line:
            return True 
            
        line = line.strip()
            
        line = self.replace_vars(line)
        
        if line.strip().startswith(SCRIPT_CHAR_CMD):
            return self.handle_command(line.strip()[1:])
            #self.delay_timer.singleShot(int(self.delay), self.next_line)
            
        
        if line.strip().startswith(SCRIPT_CHAR_RX):
            self.wait_for_input(line.strip()[1:])
            return False 
        
        if line.strip().startswith(SCRIPT_CHAR_SEND):
            return self.send(line.strip()[1:])
        

        return self.send(line)

        

    def next_line(self):
        if self.current_line == self.total_lines:
            self.stop() 
            return
        while not self.is_exiting: 
            #print(f"AAAA {self.delay_timer.timerId()} {self.delay_timer.isActive()} {self.delay_timer.remainingTime()}")
            if self.execute(self.lines[self.current_line]):
                #print(f"BBBB {self.delay_timer.timerId()} {self.delay_timer.isActive()} {self.delay_timer.remainingTime()}")
                self.current_line += 1
                if self.current_line == self.total_lines:
                    self.stop() 
                    return
            else:
                return 

    def run(self):
        self.active = True
        self.current_line = 0
        self.start_time = time.perf_counter()
        self.vars["$TIME"] = self.start_time
        self.is_exiting = False 
        self.on_exit = []
        
        self.loops = []
        self.next_line()

    def cancel(self):
        self.stop("Script Cancelled")

    def stop(self, message:str = ""):
        if self.is_exiting:
            return 
        
        self.is_exiting = True 
        if self.delay_timer.isActive():
            self.delay_timer.stop()
        if self.on_exit:
            for command in self.on_exit:
                if command.strip().startswith("@"):
                    self.handle_command(command.strip()[1:])
                else: 
                    self.output.emit((command, TYPE_TX))

        self.active = False

        self.finished.emit(message)




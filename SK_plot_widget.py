import time 
from SK_common import * 
import numpy as np 
import pyqtgraph as pg 
import pyqtgraph.exporters
from PyQt6 import QtWidgets, QtCore
#import pyqtgraph.opengl as gl
import csv 

class PlotElement:
    key:str = None 
    mult:float = None 
    color:str = None 
    points:int = None 
    export:bool = True 

class PlotWidget(pg.GraphicsLayoutWidget):
    type:str = None 
    points:int = None 
    keys:list = {}
    plot:pg.PlotItem = None 
    separators:str = " ;=,"
    start_time:float = None 
    prev_color = 0
    active = False 
    start_timestamp = None 
    limits:list = [None, None]

    # plot_3d: gl.GLLinePlotItem = None 
    
    

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #self.set_plot_item()

    def parse_keys(self, keys:str = ""):
        pass 


    def start(self, type:str = "Key-Value", points: int = 100, keys:list = [], separators:str = " :;=,", refs:list = [], title:str = "", limits:list = []):
        if self.type is not None:
            self.reset()
        self.type = type
        self.points = points    
        self.elements = {}

        
        self.separators = separators
        self.array_lengths = []

        ##### LIMITS #####
        self.limits = [None, None]
        if isinstance(limits, str):
            tokens = limits.split(",")
            for i,t in enumerate(tokens): 
                val = str_to_float(t)
                if i < 2:
                    self.limits[i] = val 
        else:
            self.limits = limits 

        ##### KEYS #####
        self.keys = {}
        if isinstance(keys, str):
            keys = char_split(keys, self.separators)
        if keys:    
            for key in keys: 
                mult = 1.00
                if "*" in key: 
                    toks = key.split("*")
                    key = toks[0]
                    mult = str_to_float(toks[1])
                elif "/" in key: 
                    toks = key.split("/")
                    key = toks[0]
                    mult = 1.00 / str_to_float(toks[1])
                self.keys[key] = {'mult': mult}

        ##### REFERENCE LINES #####
        ref_lines = []
        if isinstance(refs, (float, int)):
            ref_lines = [refs]
        elif isinstance(refs, str):
            if refs:
                toks = char_split(refs, ',')
                for t in toks: 
                    val = str_to_float(t)
                    if val is not None: 
                        ref_lines.append(val)
        elif isinstance(refs, list):
            ref_lines = refs

        dprint(f"Starting plot. Type: {self.type}, Points: {self.points}, Keys: {self.keys} Refs: {ref_lines} Limits: {self.limits}", color = "green")

        self.plot = pg.PlotItem()
        self.addItem(self.plot)
        self.plot.setTitle(title)

        for line in ref_lines:
            self.plot.addLine(y=line, pen = pg.mkPen(style = QtCore.Qt.PenStyle.DashLine))

        self.legend = pg.LegendItem(offset = (30, 30))
        self.legend.setParentItem(self.plot)
        self.plot.vb.setLimits(yMin = self.limits[0], yMax = self.limits[1])
        self.active = True 
    
    def pause(self):
        dprint("[PLOT] Pausing plot", color = "yellow")
        self.active = False
        pass 

    def resume(self):
        dprint("[PLOT] Resuming plot", color = "yellow")
        self.active = True 
        pass 

    def reset(self):
        dprint("[PLOT] Resetting plot", color = "red")
        self.type = None 
        self.start_time = None 
        self.prev_color = 0

        self.plot.clearPlots()
        self.legend.clear()
        self.start_timestamp = None 
        
        #vprint(self.plot.items, color = "red")

        self.removeItem(self.plot)
        del self.plot
        #self.plot = pg.PlotItem()
        self.elements = {}
        #self.removeItem(self.legend)    
        self.active = False 
        self.array_lengths = []

    def end(self):
        self.reset()

    def update(self, line:str = "", debug:bool = False):
        if not line or not self.type or not self.active: 
            return 
        
        rstr = ""
        tokens = char_split(line, self.separators)
        if debug: 
            rstr += f"Tokens: {tokens}\n"
        if self.type == "Key-Value":
            return rstr + self.update_key_value(tokens, debug)
        if self.type == "Index-Value":
            return rstr + self.update_index_value(tokens, debug)
        if self.type == "Single-Array":
            return rstr + self.update_single_array(tokens, debug)
        if self.type == "Key-Array":
            return rstr + self.update_key_array(tokens, debug)
        
    def export_csv(self, filename:str, rounding:float = 0, include_header:bool = True, time_format:str = "Plot-Start"):
        rounding = rounding / 1000
        dprint(f"[PLOT] Exporting CSV to {filename} with rounding: {rounding} and include_header: {include_header} and time_format: {time_format}", color = "green")
        TIME_HEADER_NAME = "SECONDS"
        if time_format != "None":
            empty = {TIME_HEADER_NAME: None}
        else:
            empty = {}
        for key in self.elements: 
            empty[key] = None 
        
        data = {}
        for element in self.elements: 
            for index, timestamp in enumerate(self.elements[element]['time']): 
                timestamp:np.float64
                if np.isnan(timestamp): 
                    continue 
                real_ts = discrete_round(timestamp, rounding, precision = 6)
                if real_ts not in data: 
                    data[real_ts] = empty.copy()
                    if time_format != "None":
                        data[real_ts][TIME_HEADER_NAME] = real_ts 
                data[real_ts][element] = self.elements[element]['data'][index] / self.elements[element]['mult']
        
        data = dict(sorted(data.items(), reverse = rounding < 0))

        timestamp_offset = 0 

        if time_format == "UNIX": 
            timestamp_offset = self.start_timestamp
        if time_format == "Zero":
            timestamp_offset = sorted(list(data.keys()))[0] * -1
            #print("keys", list(data.keys()), "lowest", timestamp_offset)
        if time_format not in ("None", "Plot-Start"):
            for element in data: 
                data[element][TIME_HEADER_NAME] = round(data[element][TIME_HEADER_NAME] + timestamp_offset, 6)

        with open(filename, "w+", newline = "", encoding = "utf-8") as file: 
                writer = csv.DictWriter(file, fieldnames = empty.keys())
                if include_header: 
                    writer.writeheader()
                for element in data: 
                    writer.writerow(data[element])

    def export_image(self, filename:str = None, size:tuple[int, int] = None):
        exporter = pyqtgraph.exporters.ImageExporter(self.plot)
        if size: 
            if len(size) == 1: 
                size = (size[0], size[0])
            exporter.parameters()['width'] = size[0]
            exporter.parameters()['height'] = size[1]
        return exporter.export(filename)




    #############################################################################################################################
    ################################### LINE PLOT FUNCTIONS ########################################################
    #############################################################################################################################
    def add_line_element(self, key:str, mult:float = 1.00):

        if self.start_timestamp is None: 
            self.start_timestamp = time.time()
        if not key: 
            return 
        
        self.elements[key] = {}
        self.elements[key]['time'] = np.full(shape = self.points, fill_value=np.nan)
        self.elements[key]['data'] = np.full(shape = self.points, fill_value=np.nan)
        self.elements[key]['line'] = self.plot.plot(self.elements[key]['time'], self.elements[key]['data'], pen = pg.intColor(self.prev_color))
        self.elements[key]['mult'] = mult 
        self.legend.addItem(self.elements[key]['line'], name = key)
        #self.elements[key] = e
        
        dprint(f"[PLOT] Added line Element {key} int color: {self.prev_color}", color = "green")
        self.prev_color += 50


    ## Example: A,100,B,C,300,-1 500 -> 0:100, 1:300, 2:-1, 3:500 
    def update_index_value(self, tokens:list[str], debug:bool = False):
        time_elapsed = None 
        debug_str = None
        key_list = []
        if self.keys:
            key_list = list(self.keys)
        index = 0 
        valid_numbers:list[float] = []
        for token in tokens:
            value = str_to_float(token)
            if value is not None:
                valid_numbers.append(value)
        if not valid_numbers:
            return "" 
        now = time.perf_counter()
        if self.start_time is None: 
            self.start_time = now 
        time_elapsed = now - self.start_time 

        for index, value in enumerate(valid_numbers):
            
            name = f'[{index}]'
            mult = 1.00 
            if key_list and index < len(key_list): 
                name = key_list[index]
                mult = self.keys[name]['mult']
            if name not in self.elements:
                self.add_line_element(name, mult)
            if debug: 
                if not debug_str: 
                    debug_str = f"TIME: {time_elapsed:.4f}"
                debug_str += f"\t[{index}]{name}:{value:.4f} "
            self.elements[name]['time'][-1] = time_elapsed
            self.elements[name]['data'][-1] = value * mult
            self.elements[name]['time'] = np.roll(self.elements[name]['time'], 1)
            self.elements[name]['data'] = np.roll(self.elements[name]['data'], 1)
            self.elements[name]['line'].setData(self.elements[name]['time'], self.elements[name]['data'])
        return debug_str
                    

    def update_key_value(self, tokens: list[str], debug:bool = False):
        prev_key = None 
        prev_mult = 1.00
        time_elapsed = None 
        debug_str = ""

        if (DEBUG_LEVEL & 0xF) >= DEBUG_LEVEL_VERBOSE:
            vprint(f"[PLOT] Updating Key-Value. Tokens: {tokens}", color = "green")
            #vprint(f"elements {self.elements}")
        for token in tokens:
            value = str_to_float(token)
            if value is not None and prev_key is not None:
                if time_elapsed is None:
                    now = time.perf_counter()
                    if self.start_time is None:
                        self.start_time = now 

                time_elapsed = now - self.start_time 
                
                if prev_key not in self.elements:
                    self.add_line_element(prev_key, prev_mult)

                self.elements[prev_key]['time'][-1] = time_elapsed
                self.elements[prev_key]['data'][-1] = value * self.elements[prev_key]['mult']
                self.elements[prev_key]['time'] = np.roll(self.elements[prev_key]['time'], 1)
                self.elements[prev_key]['data'] = np.roll(self.elements[prev_key]['data'], 1)
                self.elements[prev_key]['line'].setData(self.elements[prev_key]['time'], self.elements[prev_key]['data'])
                
                if debug: 
                    if not debug_str: 
                        debug_str = f"TIME: {time_elapsed:.4f}"
                    debug_str += f"\t{prev_key}:{value:.4f} "

                prev_key = None 
                prev_mult = 1.00
                #self.elements[prev_key].update(time_elapsed, value)
                
                continue 
            if value is None: ## Not numeric value 
                if self.keys:
                    if token in self.keys:
                        prev_key = token 
                        prev_mult = self.keys[token]['mult']
                else: 
                    prev_key = token 
                continue 

        return debug_str

    
    def add_array_element(self, key:str = None, elements:int = 1, mult:float = 1.00):
        name = key 

        if self.start_timestamp is None: 
            self.start_timestamp = time.time()
        if isinstance(key, int):
            name = chr(ord('a') + len(self.elements))
            #key = f'[{key}]'
        
        self.elements[key] = {}
        self.elements[key]['data'] = np.full(shape = (self.points, elements), fill_value=np.nan)
        self.elements[key]['time'] = np.full(shape = self.points, fill_value=np.nan)
        self.elements[key]['name'] = name 
        #self.elements[key]['data'] = np.full(shape = self.points, fill_value=np.nan)
        #self.elements[key]['color'] = self.prev_color

        self.elements[key]['line'] = [self.plot.plot(self.elements[key]['data'][0], pen = pg.intColor(self.prev_color))]
        if self.points > 1:
            for i in range(1, self.points):
                alpha = 64 if i > 3 == 0 else 127
                self.elements[key]['line'].append(self.plot.plot(self.elements[key]['data'][i], pen = pg.intColor(self.prev_color, alpha = alpha)))
        self.elements[key]['mult'] = mult 
        self.legend.addItem(self.elements[key]['line'][0], name = name)
        self.prev_color += 50

    def update_single_array(self, tokens:list[str], debug:bool = False) -> str:
        valid_numbers:list[float] = []
        debug_str = ""
        for token in tokens:
            value = str_to_float(token)
            if value is not None:
                valid_numbers.append(value)
        if not valid_numbers:
            return "" 
        now = time.perf_counter()
        if self.start_time is None: 
            self.start_time = now 
        time_elapsed = now - self.start_time 

        name = len(valid_numbers)
        
        if name not in self.elements:
            self.add_array_element(name, len(valid_numbers))
        self.elements[name]['time'][-1] = time_elapsed
        self.elements[name]['data'][-1] = np.asarray(valid_numbers)
        self.elements[name]['data'] = np.roll(self.elements[name]['data'], 1, axis = 0)
        self.elements[name]['time'] = np.roll(self.elements[name]['time'], 1)
        for index, element in enumerate(self.elements[name]['data']):
            self.elements[name]['line'][index].setData(y = element)
        if debug:
            debug_str = f"\tT: {time_elapsed:.4f}"
            debug_str += f"\t{name}:{valid_numbers}"
        return debug_str
    
    def update_key_array(self, tokens:list[str], debug:bool = False):
        prev_key = None 
        prev_mult = 1.00
        now = time.perf_counter()
        if self.start_time is None:
            self.start_time = now 
        time_elapsed = now - self.start_time 
        debug_str = None
        values = []
        for token in tokens: 
            value = str_to_float(token)
            if value is None: ## Token is not a number or last token 

                if prev_key is not None and values:
                    if prev_key not in self.elements:
                        self.add_array_element(prev_key, len(values), prev_mult)
                    ### ACTUAL UPDATE HAPPENS HERE 
                    self.elements[prev_key]['time'][-1] = time_elapsed
                    self.elements[prev_key]['data'][-1] = np.asarray(values) * prev_mult
                    self.elements[prev_key]['data'] = np.roll(self.elements[prev_key]['data'], 1, axis = 0)
                    self.elements[prev_key]['time'] = np.roll(self.elements[prev_key]['time'], 1)
                    for i, element in enumerate(self.elements[prev_key]['data']):
                        if element[0] is not np.nan:    
                            self.elements[prev_key]['line'][i].setData(element)
                    if debug:
                        debug_str = f"\tT:{time_elapsed:.4f} sec"
                        debug_str += f"\n\t{prev_key}:{values}"
                    values = []
                    prev_key = None 
                    prev_mult = 1.00
                if self.keys: 
                    if token in self.keys:
                        prev_key = token 
                        prev_mult = self.keys[token]['mult']
                else: 
                    prev_key = token 
                #continue 
            else:
                values.append(value)

        if prev_key is not None and values:
            if prev_key not in self.elements:
                self.add_array_element(prev_key, len(values), prev_mult)
            ### ACTUAL UPDATE HAPPENS HERE 
            self.elements[prev_key]['time'][-1] = time_elapsed
            self.elements[prev_key]['data'][-1] = np.asarray(values) * prev_mult
            self.elements[prev_key]['data'] = np.roll(self.elements[prev_key]['data'], 1, axis = 0)
            self.elements[prev_key]['time'] = np.roll(self.elements[prev_key]['time'], 1)
            for i, element in enumerate(self.elements[prev_key]['data']):
                self.elements[prev_key]['line'][i].setData(element)
            if debug:
                debug_str += f"\n\t{prev_key}:{values}"
        return debug_str

    def update_key_3d(self, tokens:list[str], debug:bool = False):
        prev_key = None 
        prev_mult = 1.00
        now = time.perf_counter()
        if self.start_time is None:
            self.start_time = now 
            



def test_plot_widget():
    import sys  
    app = QtWidgets.QApplication(sys.argv)
    pw = PlotWidget()
    import math 
    import random 
    global indx_val
    indx_val = 0

    TYPE = "Key-Value"
    POINTS = 100
    UPDATE_DELAY = 50
    
    KEYS = []
    #KEYS = ["A", "B", "J", "c"]

    def get_kw_string() -> str:
        global indx_val
        test_str = f"A:{round((math.sin(indx_val/ 10) * 5), 4)},"
        test_str += f"J,  " # Key with no value 
        test_str += f"B:{round(random.random(),4)},"
        test_str += "1234," # Value with no key 
        test_str += f"c {random.randint(-2,5)}, "
        test_str += f"d={math.cos(indx_val / 10) * 5}"
        indx_val = indx_val + 1
        return test_str
    

    def update_plot():
        s = get_kw_string()
        print(s)
        pw.update(s)
    



    pw.start(type = TYPE, points = POINTS, keys = KEYS)

    timer = QtCore.QTimer()
    timer.timeout.connect(update_plot)
    timer.start(UPDATE_DELAY)
    # pw.update("A 100 B 333 C 663")
    # pw.update("A 532 B 222 C 150")
    # pw.update("A 222 B 666 C 999")
    # pw.update("A 222 B 666")
    # pw.update("A 222 B 666")
    # pw.update("A 222 B -666")
    pw.end()

    pw.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    test_plot_widget()


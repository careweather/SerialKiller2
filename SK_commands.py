import shlex 
import sys 
import traceback 

from SK_common import *


class Option: 
    keys:tuple[str, ...]
    type = str 
    default = None 
    is_list = False 
    def __init__(self, keys:tuple[str, ...], type = str, default:any = None):
        self.keys = keys 
        self.type = type 
        self.default = default 

        if isinstance(default, list):
            self.is_list = True 

    def __eq__(self, other:str):
        return other in self.keys 

class Command:
    name: str 
    options = []
    def __init__(self, name:str, func: callable, options:list = []):
        self.name = name 
        self.func = func
        self.options = options

    def __eq__(self, other:str):
        return other.split(" ")[0] == self.name 

    def execute(self, input:str) -> tuple[bool, str]:
        if not self.__eq__(input):
            return False, ""
        try:    
            tokens = shlex.split(input, posix = True)[1:]
            #dprint(f"COMMAND ARGS: {args}", color = "green")
        except Exception as e:
            eprint(f"ERROR SPLITTING COMMAND {input}: {e}")
            return True, e
        
        args = []
        kwargs = {}
        prev_option = None 
        for token in tokens:
            is_option = False 
            for option in self.options:
                if token == option:
                    if option.is_list:
                        kwargs[option.keys[0]] = []
                    else:
                        kwargs[option.keys[0]] = option.default
                    prev_option = option 
                    is_option = True
            if is_option:
                continue 
            if prev_option is not None:
                try:
                    val = prev_option.type(token)
                except Exception as e:
                    return True, f"CMD: <{input}> \nERROR\n{e}\n"
                if prev_option.is_list: 
                    kwargs[prev_option.keys[0]].append(val)
                else:
                    kwargs[prev_option.keys[0]] = val
                    prev_option = None 
            else:
                args.append(token)


        vprint(f"CMD: <{input}> args: {args} kwargs: {kwargs}", color = "yellow")
        try:
            self.func(*args, **kwargs)
        except Exception as e:
            error_type, value, tb = sys.exc_info()
            tb_lines = traceback.format_tb(tb)
            eprint(traceback.format_exc())
            return True, f'CMD: <{input}> \nERROR: {"".join(tb_lines[1:])}\n{value}\n'
        return True, ""

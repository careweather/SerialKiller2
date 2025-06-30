import os 
from PyQt6.QtGui import QColor
from termcolor import colored, cprint
import json 
from PyQt6 import QtWidgets 
from PyQt6.QtWidgets import QFileDialog
from SK_help import *
import random 
import pygit2
import datetime


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_SETTINGS_PATH = os.path.join(BASE_DIR, "settings")
DEFAULT_SETTINGS_FILE = os.path.join(BASE_DIR, "settings" ,"default.json")
DEFAULT_SCRIPT_PATH = os.path.join(BASE_DIR, "scripts")
DEFAULT_LOG_PATH = os.path.join(BASE_DIR, "logs")
DEFAULT_PLOT_EXPORT_PATH = os.path.join(BASE_DIR, "logs")
DEFAULT_EXTENSION_PATH = os.path.join(BASE_DIR, "extensions")
DEFAULT_RESOURCES_PATH = os.path.join(BASE_DIR, "resources")
DEFAULT_HELP_PATH = os.path.join(BASE_DIR, "readme.md")

#DEFAULT_HELP_PATH = os.path.join(BASE_DIR, "doc", "help.html")
DEFAULT_HELP_STYLE_PATH = os.path.join(BASE_DIR, "doc", "help.css")

EXTENSION_TEMPLATE_PATH = os.path.join(DEFAULT_RESOURCES_PATH, "template.py")


GIT_REPO = pygit2.Repository(BASE_DIR)
GITHUB_BRANCH = GIT_REPO.head.shorthand
GITHUB_TARGET = GIT_REPO.head.target
GITHUB_LOG = GIT_REPO.head.log()
GITHUB_COMMIT_DATE = ""
for i, l in enumerate(GITHUB_LOG):
    if i == 0:
        GITHUB_COMMIT_DATE = datetime.datetime.fromtimestamp(l.committer.time).strftime("%Y-%m-%d %H:%M:%S")
        break 

###########################################################################
################ DEBUGGING
###########################################################################




DEBUG_LEVEL_ERROR = 1
DEBUG_LEVEL_DEBUG = 2 
DEBUG_LEVEL_VERBOSE = 3

DEBUG_LEVEL = DEBUG_LEVEL_ERROR   


def eprint(*args, color:str = "red", **kwargs):
    if DEBUG_LEVEL >= DEBUG_LEVEL_ERROR:
        pstr = ""
        for arg in args:
            pstr += f"{arg} "
        cprint(pstr, color, **kwargs)

def dprint(*args, color:str = "white", **kwargs):
    if (DEBUG_LEVEL & 0xF) >= DEBUG_LEVEL_DEBUG:
        pstr = ""
        for arg in args:
            pstr += f"{arg} "
        cprint(pstr, color, **kwargs)

def vprint(*args, color:str = "white", **kwargs):
    if (DEBUG_LEVEL & 0xF) >= DEBUG_LEVEL_VERBOSE:
        pstr = ""
        for arg in args:
            pstr += f"{arg} "
        cprint(pstr, color, **kwargs)


###########################################################################
################ COLOR DEFAULTS 
###########################################################################

COLOR_WHITE = QColor(255, 255, 255)
COLOR_LIGHT_GREY = QColor(220, 220, 220)
COLOR_GREY = QColor(155, 155, 155)
COLOR_MED_DARK_GREY = QColor(100, 100, 100)
COLOR_DARK_GREY = QColor(79, 79, 79)
COLOR_BLACK = QColor(0, 0, 0)
COLOR_DARK_BLUE = QColor(0, 0, 255)
COLOR_LIGHT_BLUE = QColor(105, 207, 255)
COLOR_LAVENDER = QColor(171, 195, 255)

COLOR_LIGHT_GREEN = QColor(97, 255, 142)
COLOR_GREEN = QColor(24, 160, 0)
COLOR_DARK_GREEN = QColor(0, 100, 0)

COLOR_RED = QColor(218, 0, 0)
COLOR_LIGHT_RED = QColor(255, 110, 110)
COLOR_LIGHT_LIGHT_RED = QColor(255, 200, 200)
COLOR_MED_DARK_RED = QColor(150, 0, 0)
COLOR_DARK_RED = QColor(36, 0, 0)

COLOR_LIGHT_YELLOW = QColor(248, 252, 121)
COLOR_DARK_YELLOW = QColor(138, 140, 0)

COLOR_PINK = QColor(255, 105, 180)

COLOR_DICT = {
    "default": None,
    "white": COLOR_WHITE,
    "light grey": COLOR_LIGHT_GREY,
    "grey": COLOR_GREY,
    "dark grey": COLOR_DARK_GREY,
    "dark blue": COLOR_DARK_BLUE,
    "light blue": COLOR_LIGHT_BLUE,
    "lavender": COLOR_LAVENDER,
    "light green": COLOR_LIGHT_GREEN,
    "green": COLOR_GREEN,
    "red": COLOR_RED,
    "light red": COLOR_LIGHT_RED,
    "dark red": COLOR_DARK_RED,
    "dark yellow": COLOR_DARK_YELLOW,
    "light yellow": COLOR_LIGHT_YELLOW,
}

def color_to_style_sheet(color: QColor) -> str:
    return f"rgb({color.red()}, {color.green()}, {color.blue()})"

DEFAULT_BUTTON_FONT_SIZE = 13

STYLESHEET_BUTTON_GREEN = f"background-color: {color_to_style_sheet(COLOR_DARK_GREEN)}; font-size: {DEFAULT_BUTTON_FONT_SIZE}px;"
STYLESHEET_BUTTON_RED = f"background-color: {color_to_style_sheet(COLOR_MED_DARK_RED)}; font-size: {DEFAULT_BUTTON_FONT_SIZE}px;"
STYLESHEET_BUTTON_YELLOW = f"background-color: {color_to_style_sheet(COLOR_DARK_YELLOW)}; font-size: {DEFAULT_BUTTON_FONT_SIZE}px;"
STYLESHEET_BUTTON_GREY = f"background-color: {color_to_style_sheet(COLOR_DARK_GREY)}; font-size: {DEFAULT_BUTTON_FONT_SIZE}px;"

STYLESHEET_BUTTON_ACTIVE = STYLESHEET_BUTTON_GREEN
STYLESHEET_BUTTON_INACTIVE = STYLESHEET_BUTTON_GREY
STYLESHEET_BUTTON_CANCEL = STYLESHEET_BUTTON_RED

STYLESHEET_BUTTON_DEFAULT = f"font-size: {DEFAULT_BUTTON_FONT_SIZE}px;"

DEFAULT_LINE_EDIT_FONT_SIZE = 13
STYLESHEET_LINE_EDIT_ERROR = f"background-color: {color_to_style_sheet(COLOR_MED_DARK_RED)}; font-size: {DEFAULT_LINE_EDIT_FONT_SIZE}px;"
STYLESHEET_LINE_EDIT_DEFAULT = f"font-size: {DEFAULT_LINE_EDIT_FONT_SIZE}px;"


ESCAPE_SEQUENCE_TERMINATORS = bytes("cnRchl()HABCDfsugKJipm\r\n", 'utf-8')

ESCAPE_COLORS = {
    "0": QColor(0, 0, 0, 0),
    "1": QColor(255, 0, 0),
    "2": QColor(0, 255, 0),
    "3": QColor(255, 255, 0),
    "4": QColor(0, 0, 255),
    "5": QColor(255, 0, 255), ## Magenta 
    "6": QColor(0, 255, 255), ## Cyan 
    "7": QColor(255, 255, 255),
}


###########################################################################
################ TYPE DEFINITIONS FOR ADD_TEXT 
###########################################################################

TYPE_SRC_RX = 0
TYPE_SRC_TX = 1
TYPE_SRC_INFO = 2
TYPE_SRC_ERROR = 3
TYPE_SRC_COMMAND = 4 

## Bits 3-5 are for color modifiers 
TYPE_MOD_WHITE = 0 << 3 
TYPE_MOD_GREEN = 1 << 3 
TYPE_MOD_BLUE = 2 << 3 
TYPE_MOD_YELLOW = 3 << 3 
TYPE_MOD_RED = 4 << 3 
TYPE_MOD_CYAN = 5 << 3 
TYPE_MOD_MAGENTA = 6 << 3 
TYPE_MOD_BLACK = 7 << 3 
TYPE_MOD_PINK = 8 << 3 

## Bits 6-7 are for configs 
TYPE_CONFIG_DEFAULT = 0 << 7
TYPE_CONFIG_RAW = 1 << 7

COLOR_MODIFIERS = {
    TYPE_MOD_WHITE: COLOR_WHITE,
    TYPE_MOD_GREEN: COLOR_LIGHT_GREEN,
    TYPE_MOD_BLUE: COLOR_LIGHT_BLUE,
    TYPE_MOD_YELLOW: COLOR_LIGHT_YELLOW,
    TYPE_MOD_RED: COLOR_LIGHT_RED,
    TYPE_MOD_CYAN: COLOR_LIGHT_BLUE,
    TYPE_MOD_MAGENTA: COLOR_LAVENDER,
    TYPE_MOD_BLACK: COLOR_BLACK,
    TYPE_MOD_PINK: COLOR_PINK,
}


TYPE_RX = TYPE_SRC_RX | TYPE_MOD_WHITE | TYPE_CONFIG_DEFAULT
TYPE_TX = TYPE_SRC_TX | TYPE_MOD_BLUE | TYPE_CONFIG_DEFAULT
TYPE_INFO = TYPE_SRC_INFO | TYPE_MOD_YELLOW | TYPE_CONFIG_DEFAULT
TYPE_ERROR = TYPE_SRC_ERROR | TYPE_MOD_RED | TYPE_CONFIG_DEFAULT
TYPE_INFO_GREEN = TYPE_SRC_INFO | TYPE_MOD_GREEN 
TYPE_INFO_MAGENTA = TYPE_SRC_INFO | TYPE_MOD_MAGENTA 
TYPE_INFO_CYAN = TYPE_SRC_INFO | TYPE_MOD_CYAN 
TYPE_INFO_PINK = TYPE_SRC_INFO | TYPE_MOD_PINK 

SCRIPT_CHAR_VAR = "$"
SCRIPT_CHAR_CMD = "@"
SCRIPT_CHAR_SEND = ">"
SCRIPT_CHAR_RX = "<"
SCRIPT_CHAR_COMMENT = "#"



###########################################################################
################ UTILITY FUNCTIONS 
###########################################################################

def replace_control_chars(text:str):
    return text.replace(r"\r", "\r").replace(r"\n", "\n").replace(r"\t", "\t")

## This function will split a string by any characters in the string "char", then return a list of of the split strings with none being empty
def char_split(line: str, char: str = " ") -> list[str] | None:
    """Split a string by any characters in the delimiter string.
    
    Args:
        line: Input string to split
        char: String containing delimiter characters
    
    Returns:
        List of non-empty strings, or None if no tokens are found
    """
    if not line:
        return None
        
    # Create translation table using a unique character that won't appear in the input
    trans = str.maketrans(dict.fromkeys(char, "\x00"))
    # Replace all delimiter chars with null character and split
    items = [item for item in line.translate(trans).split("\x00") if item]
    return items if items else None


def pretty_format_dict(dict:dict):
    return str(json.dumps(dict, indent=4))

# def get_dir(dir_path:str = None):
#     path = QFileDialog.getExistingDirectory(None, "Select Directory")
#     return os.path.join()
#     return dir_path




def str_to_float(s: str) -> float | None:
    """Convert string to float, returning None if invalid.
    Returns:
        Float value or None if conversion fails
    """
    try:
        return float(s)
    except (ValueError, TypeError):
        return None

def discrete_round(value:float, step:float = 1, precision:int = 6):
    return round(step * round(value / step), precision)


def clean_filepath(input:str, default_path:str = None, extensions:list[str] = None, replace_bad_ext: bool = True) -> str | None: 
    '''Returns an absolute filepath with the correct extension if provided'''
    clean_extensions: list[str] = []
    
    if extensions is not None: 
        if isinstance(extensions, str):
            extensions = extensions.split(";;")
        for ext in extensions: 
            if "." not in ext: 
                ext = '.' + ext 
            if not ext.startswith("."):
                ext = os.path.splitext(ext)[1]
            clean_extensions.append(ext)
    filename, ext = os.path.splitext(input)
    if clean_extensions: 
        if not ext: 
            input += clean_extensions[0]
        elif ext not in clean_extensions:
            if replace_bad_ext:
                input = filename + clean_extensions[0]
            else:
                return None 

    if not os.path.isabs(input):
        input = os.path.join(default_path, input)
    
    return input



def get_backup_filepath(filepath:str):
    if not os.path.exists(filepath):
        return None 
    parent_dir, basename = os.path.split(filepath)
    basename, extension = os.path.splitext(basename)

    indx = 1 
    backup_name = os.path.join(parent_dir, f"{basename}_{indx}{extension}")
    while os.path.exists(backup_name):
        indx += 1 
        backup_name = os.path.join(parent_dir, f"{basename}_{indx}{extension}")
    return backup_name

def get_save_file_popup(parent, file_path: str = None, extensions: str = None, title: str = "Select File") -> str | None:
    if isinstance(extensions, (list, tuple)):
        extensions = ";;".join(extensions)
    path, selected_filter = QFileDialog.getSaveFileName(parent, title, directory=file_path, filter=extensions)
    if not path:
        vprint("get save file popup cancelled", color="yellow")
        return None
    path_ext = os.path.splitext(path)[1]
    if not path_ext:
        path = path + os.path.splitext(selected_filter)[1]

    vprint(f"get save file popup: {path}, selected filter: {selected_filter}, path ext: {path_ext}", color="yellow")

    return path

def get_extension_string(extensions:list|str) -> str:
    tokens = []
    if isinstance(extensions, (list, tuple)):
        tokens = extensions
    elif isinstance(extensions, str):
        tokens = char_split(extensions.strip().rstrip(), " ,;.")
    else:
        return None 
    result = ""
    for token in tokens: 
        if not token.startswith("*."):
            token = "*." + token 
        result += token + ";;"
    result = result[:-2]
    return result

def get_cow(*args, **kwargs):
    p_str = ""
    if not args and not kwargs:
        
        p_str = COW_WISDOM[random.randint(0, len(COW_WISDOM) - 1)]
        if not p_str: 
            return COW_DEAD
        else: 
            cow = COW_RANDOM[random.randint(0, len(COW_RANDOM) - 1)]
    else:   
        cow = COW_BUBBLES

    for arg in args:
        p_str += arg + " "

    if "-n" in kwargs:
        cow = COW_NERD
    
    if '-d' in kwargs:
        cow = COW_DEAD
    
    if '-l' in kwargs:
        cow = COW_IN_LOVE

    top = "_" * (len(p_str)+ 2)

    if not p_str:
        return cow

    cow_str = f"""\
 {top}
/ {p_str} \\
\\{top}/"""

    return cow_str + cow

EMPTY_PLOT_ELEMENT = {'mult': 1.0, "time": None, "data": None, "color": None, "points": None, "export": True}


def split_preserve_braces(input_str: str) -> list[str]:
    if not input_str:
        return []
        
    in_braces = False
    current_token = ""
    tokens = []
    
    for char in input_str:
        if char == '{':
            in_braces = True
            current_token += char
        elif char == '}':
            in_braces = False
            current_token += char
        elif char == ',' and not in_braces:
            if current_token:
                tokens.append(current_token.strip())
                current_token = ""
        else:
            current_token += char
            
    if current_token:
        tokens.append(current_token.strip())
        
    return tokens

def str_to_plot_elements(input:str = "") -> dict: 
    elements = {}
    if not input: 
        return {}
    tokens = split_preserve_braces(input)
    #print("t", tokens)
    for token in tokens: 
        name = ""
        attrs = EMPTY_PLOT_ELEMENT.copy()
        if ":" in token: 
            name = token[:token.find(":")]
            attrs_str = token[token.find(":")+1:]
            for attr in attrs_str.split(","): 
                attr = attr.replace("{", "").replace("}", "")
                if ":" in attr: 
                    attr_name, attr_val = attr.split(":")
                    if attr_val == "True":
                        attr_val = True 
                    elif attr_val == "False":
                        attr_val = False 
                    else:
                        try: 
                            attr_val = float(attr_val)
                        except ValueError: 
                            pass 
                    attrs[attr_name] = attr_val
        else:
            name = token 
        if "*" in name:
            sub_tokens = name.split("*")
            name = sub_tokens[0]
            attrs["mult"] = float(sub_tokens[1])
        elements[name] = attrs
    return elements

def plot_elements_to_str(elements:dict) -> str:
    rstr = ""
    for e in elements: 
        rstr += f"{e}"
        if elements[e] != EMPTY_PLOT_ELEMENT:
            #print("NEQ", elements[e])
            rstr += ":{"
            for attr in elements[e]: 
                if elements[e][attr] != EMPTY_PLOT_ELEMENT[attr]:   
                    rstr += f"{attr}:{elements[e][attr]},"
            rstr = rstr[:-1] + "}"
        rstr += ","
    return rstr[:-1]



GREETINGS_TEXT = f"""\
|----------------------------------------------------------------|
|                    _         _   _     _  _  _                 |
|                   (_)       | | | |   (_)| || |                |
|   ___   ___  _ __  _   __ _ | | | | __ _ | || |  ___  _ __     |
|  / __| / _ \| '__|| | / _` || | | |/ /| || || | / _ \| '__|    |
|  \__ \|  __/| |   | || (_| || | |   < | || || ||  __/| |       |
|  |___/ \___||_|   |_| \__,_||_| |_|\_\|_||_||_| \___||_|       |
|                                                                |
|------------------WRITTEN BY ALEX LARAWAY-----------------------|
GITHUB BRANCH:      {GITHUB_BRANCH}
GITHUB TARGET:      {GITHUB_TARGET}
GITHUB COMMIT DATE: {GITHUB_COMMIT_DATE}
BASE DIR:           {BASE_DIR}
"""

def run_tests():
    pass 

if __name__ == "__main__":
    import sys 
    args = sys.argv[1:]
    if not args: 
        args = ["A,B*3.5,C*.5:{color:red,export:False},D:{mult:1,color:red},E"]
    print("args", args)
    elements = str_to_plot_elements(args[0])
    s = plot_elements_to_str(elements)
    for e in elements: 
        print(e, elements[e])
    print("s", s)
    run_tests()

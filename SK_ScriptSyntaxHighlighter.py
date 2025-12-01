from PyQt6.QtCore import QObject, pyqtSignal, QTimer
from PyQt6.QtGui import QTextCharFormat, QTextCursor, QSyntaxHighlighter
from PyQt6.QtWidgets import QTextEdit
import time 
from SK_common import * 


'''

The parser should return a dictionary with the keys: 
    "comment"
    "send"
    "receive"
    "expression"
    "variable"
    "command"
    Each key should have a list of tuples with the start and end positions of the text

Parsing rules: 
A # is the start of a commment. It can appear anywhere in the line. No other formatting is applied to comments
A command starts with @ and is followed by a command name. The command name is followed by a space and then the command arguments
If a line starts with ">" is is a send command 
If a line starts with "<" is is a receive command 
An expression is text that starts with $ and is followed by { and } 
A variable is any word that starts with $ and is not followed by {
A variable takes the highest priority for formatting. If it is part of an expression it is highlighted as an expression.
'''

def parse_line(line: str) -> dict[str, list[tuple[int, int]]]:
    """
    Parse a line of text and return positions of special syntax elements.
    
    Args:
        line: Input string to parse
        
    Returns:
        Dictionary with keys 'comment', 'send', 'receive', 'expression', 'variable', 'command'
        containing lists of (start, end) position tuples
    """
    result = {
        "comment": [],
        "send": [],
        "receive": [],
        "expression": [],
        "variable": [],
        "command": []
    }
    
    # Handle comments first (they override other formatting)
    comment_pos = line.find('#')
    if comment_pos >= 0:
        result["comment"].append((comment_pos, len(line)))
        # Truncate line for other parsing
        line = line[:comment_pos]
    
    # Handle send/receive commands (must be at start of line)
    stripped = line.lstrip()
    leading_spaces = len(line) - len(stripped)
    if stripped.startswith('>'):
        result["send"].append((leading_spaces, len(line)))
    elif stripped.startswith('<'):
        result["receive"].append((leading_spaces, len(line)))
    
    # Handle @ commands
    if stripped.startswith('@'):
        cmd_start = leading_spaces
        # Find the end of the command (space or end of line)
        for i in range(cmd_start + 1, len(line)):
            if line[i].isspace():
                result["command"].append((cmd_start, len(line)))
                break
        else:
            result["command"].append((cmd_start, len(line)))
    
    # Find expressions ${...}
    i = 0
    while i < len(line):
        if line[i] == '$' and i + 1 < len(line) and line[i + 1] == '{':
            start = i
            level = 0
            for j in range(i, len(line)):
                if line[j] == '{':
                    level += 1
                elif line[j] == '}':
                    level -= 1
                    if level == 0:
                        result["expression"].append((start, j + 1))
                        i = j
                        break
        i += 1
    
    # Find variables ($ not followed by {)
    i = 0
    while i < len(line):
        if line[i] == '$':
            # Skip if this is part of an expression
            if i + 1 < len(line) and line[i + 1] == '{':
                i += 1
                continue
                
            # Find end of variable (space or special char)
            start = i
            for j in range(i + 1, len(line)):
                if line[j] in ' \t\n#<>${}@':
                    result["variable"].append((start, j))
                    i = j
                    break
            else:  # If we reach end of line
                result["variable"].append((start, len(line)))
        i += 1
    
    return result

def find_expressions(line: str) -> list[tuple[int, int]]:
    """
    Find all ${...} expressions in a line and return the positions of the brackets
    
    Args:
        line: Input string to parse
        
    Returns:
        List of tuples containing (start_with_$, bracket_end) for each matched expression
    """
    results = []
    level = 0
    bracket_start = None
    
    for i, char in enumerate(line):
        if char == '{' and i > 0 and line[i-1] == '$':
            if level == 0:
                bracket_start = i-1  # Include the $ position
            level += 1
        elif char == '}':
            level -= 1
            if level == 0 and bracket_start is not None:
                results.append((bracket_start, i))
                bracket_start = None
                
    return results

class ScriptSyntaxHighlighter(QSyntaxHighlighter):
    cmd_format = QTextCharFormat()
    cmd_format.setForeground(COLOR_DARK_YELLOW)

    comment_format = QTextCharFormat()
    comment_format.setForeground(COLOR_GREY)

    var_format = QTextCharFormat()
    var_format.setForeground(COLOR_LIGHT_BLUE)

    send_format = QTextCharFormat()
    send_format.setForeground(COLOR_WHITE)

    expression_format = QTextCharFormat()
    expression_format.setForeground(COLOR_LIGHT_GREEN)

    receive_format = QTextCharFormat()
    receive_format.setForeground(COLOR_LIGHT_RED)

    def __init__(self, parent: QTextEdit = None):
        super().__init__(parent)

    def highlightBlock(self, input:str) -> None: 
        results = parse_line(input)
        for item in results["command"]:
            self.setFormat(item[0], item[1] - item[0] + 1, self.cmd_format)
        for item in results["comment"]:
            self.setFormat(item[0], item[1] - item[0] + 1, self.comment_format)
        for item in results["send"]:
            self.setFormat(item[0], item[1] - item[0] + 1, self.send_format)
        for item in results["receive"]:
            self.setFormat(item[0], item[1] - item[0] + 1, self.receive_format)
        for item in results["expression"]:
            self.setFormat(item[0], item[1] - item[0] + 1, self.expression_format)
        for item in results["variable"]:
            self.setFormat(item[0], item[1] - item[0], self.var_format)




    def _highlightBlock(self, input:str) -> None: 
        #input = input.strip()
        start_comment = None 
        start_var = None 
        start_send = None 
        start_cmd = None 
        start_expression = None 

        expression_level = 0

        cmd_sections = []
        comment_sections = []
        var_sections = []
        send_sections = []
        expression_sections = []

        line_index = 0
        in_len = len(input)

        expression_sections = find_expressions(input)


        self.setFormat(0, in_len, self.cmd_format)
        for section in comment_sections:
            self.setFormat(section[0], section[1], self.comment_format)
        for section in send_sections:
            self.setFormat(section[0], section[1], self.send_format)
        for section in var_sections:
            self.setFormat(section[0], section[1], self.var_format)
        for section in expression_sections:
            self.setFormat(section[0], section[1], self.expression_format)
        for section in cmd_sections:
            self.setFormat(section[0], section[1], self.cmd_format)
        

        print(f"TEXT: {input} Exp: {expression_sections} Var {var_sections} Com {comment_sections} Send {send_sections}")
        #print(expression_sections, var_sections, comment_sections, send_sections)






TERMINAL_PLACEHOLDER = """\
Serial from the device will appear here
Keystrokes here will be sent immediately to the device

----- Commands (use arg '-h' for more info on a command)
help                    Open help window
clear                   Clear the terminal 
con [port] [-b baud]    Make a serial connection (optional [port])
dcon                    Disconnect from the device
alias [name]            Set the alias for the current serial port
ports [-a]              List available ports. Use -a to show all available info
script [args ...]       Run the script in the script tab (optional args)
script -o [file]        Open a script (optional [file].txt)
script -n [file]        New script 
script -s [file]        Save the script in the script tab (opt. [file].txt)
log                     Open the current log file 
log -o [file]           Open any log file from the directory (optional [file].txt)
log -s [file]           Save the current log file (optional [file].txt)
log -n <file>           Start logging to a new file <file>.txt 
plot [cmd] [args]       Configure or control the plotting feature (use -h for more info)
key [char] [value]      Set a new keyboard command 
ext [filename] [args]   Load an extension with the name [filename].py
ext [OPTIONS]           Configure or control the extension feature (use -h for more info)
ext end                 End the currently running extension
exit                    Exit the program 
"""


CONNECT_HELP = """\
USEAGE: 
con [port] [OPTIONS]

[port] only needs to match the end of the port name. 
ie. if "/dev/ttyACM0" exists "con 0" is valid. 

if no port or options are provided, the settings defined in the GUI are used 

OPTIONS: 
    -b, --baud      <baudrate>
    -p, --parity    [NONE|EVEN|ODD|MARK|SPACE]
    -x, --xonxoff   [1|0]
    -r, --rtscts    [1|0]
    -d, --dsrdtr    [1|0]

EXAMPLES: 
connect to the port ending in "ACM0". Set baud to 115200, and enable xonxoff
    con ACM0 -b 115200 -x 1 --rtscts 0

connect to the currently selected port at 9600
    con --baud 9600 
"""

SETTINGS_HELP = """\
USEAGE: 
settings                        List all current settings 
settings [setting] [value]      Set a specific setting 
settings -s [filename]          Save current settings to a file    
settings -l [filename]          Load settings from a file 
settings -ls                    List all settings files 

"""

PLOT_HELP = """\
USEAGE: 
plot [COMMAND] [OPTIONS] 

COMMANDS: 
  export [file] [EXPORT OPTIONS]    export the current data to file 
                                    .csv, .png, .svg extensions determine type
  reset                             reset the plot
  pause                             pause the plot
  resume                            resume the plot
  start [args]                      start the plot in whatever mode is selected)
  kv, key-value [OPTIONS]           start the plot in key-value mode
  iv, index-value [OPTIONS]         start the plot in index-value mode
  sv, single-value [OPTIONS]        start the plot in single-value mode
  av, array-value [OPTIONS]         start the plot in array-value mode
  test [string]                     test the plot parsing and plotting with a string input

OPTIONS: 
  -p, --points [numb points]        Set the number of points for each item tracked
  -k, --keys [keys]                 Keys used to determine key-value pairs.
                                    Separate keys using any sep i.e "A,B,C"
  -r, --refs [refs]                 Reference Y axis lines. Use "," to separate multiple vals 
  -l, --limits [min,max]            Set the min and max values for the Y axis
  -t, --title [title]               Set the title of the plot
EXPORT OPTIONS: 
  --round [number]                  Round timestamps to the nearest [number] milliseconds
                                    Used for aligning data that was not recieved at the same time
  --time-fmt [format]
  --header [1|0]
  --size [width,height]


EXAMPLES:
    plot export data.csv --round .01 
    plot reset 
    plot kv --keys "a,b,c" --refs "-50,0,50" --limits "-100,100" --points 100
"""

PLOT_TYPE_HELP = """\
-------Parsing------- 
Incoming text will be evaluated line-by-line.
Data on the same line will be timestamped at the same time.

Each line of text will be split into tokens by any separator or 'sep' characters. 
Tokens will be converted to numbers if possible. 
For example, if the seps are ",: =\\t" the incoming line "PI: 3.14 MYVAR 420 69:36" 
will be split into ['PI', 3.14, 'MYVAR', 420, 69, 36]  


-------Plot Types------- 
Key-Value: Plots multiple values with 
If no "Keys" are present 
"""

EXTENSION_HELP = """\
USEAGE:
ext stop,-s,end                      Stop the currently running extension    
ext [filename] [OPTIONS]          Start an extension named [filename].py
                                  if no [filename] is provided, a file popup will open
ext -c,cmd [args ...]
ext new [filename]                Create a new extension from the extension template
ext -ls                          List all available extensions 
ext -h                           Print this help text 

OPTIONS:
    -h, --help                    Print this help text 
    -ls, --list                   List all extensions
    -r, --run                     Run the extension
    -s, --stop                    Stop the extension
    -c, --cmd [cmd]               Send a command to the extension 
    -d, --debug [level]           Set the debug level for the extension
"""


LOG_HELP = """\
USEAGE: 
log                             Opens the current log file
log [OPTIONS]                   

OPTIONS: 
    on, --on                    Enable logging
    off, --off                  Disable logging
    -o, --open [filename]       Opens a log file from the directory 
    -s, --save [filename]       Saves the current log file to another file. 
    -n, --new [filename]        Starts logging to a new file. 
    -ls, --list                 List all log files in the directory 
    --line-fmt [format]         Set the format of the log lines 
    --time-fmt [format]         Set the format of the log timestamps 
    -h, --help                  Print this help text 

EXAMPLES: 
Open a log named data.txt 
    log -o data.txt
Save the current log to a new file called my_log.txt
    log -s my_log.txt

"""

KEY_COMMAND_HELP = """\
USEAGE: 
key                     jump to key textedit
key [key] [send]        set a key command
key clear               clear all key commands
key -ls                 list all key commands
key -h                  print this help text

For non character keys use: UP,DOWN,LEFT,RIGHT,RETURN,ENTER,TAB,BACKSPACE
"""

SCRIPT_HELP = """\
USEAGE: 
script                    Run the script in the script tab
script [arg0] [arg1] ...  Run the script in the script tab with cli arguments 
script -h                 Print this help text 
script -o [filename]      Open a script. 
script -n [filename]      new script 
script -t                 Jump to script tab 
script -d <milliseconds>  Set the default delay to <milliseconds> 
script -ls                List all scripts in the script directory 
"""

SCRIPT_SYNTAX_HELP = """\
SCRIPT SYNTAX: 
Each line in the will be copied into the "send" textbox and executed just as if ENTER was pressed.  

If a line is blank it will be skipped. 

If a line starts with '@' it is interpreted as a command to serial killer, and executed without a delay. 

Anything wrapped in a '${}' will be evaluated as an expression. 
This means that "pi is ${math.pi}" will be sent as "pi is 3.141592653589793"


-------- Additional commands: 
@args=<arg0> [arg1] ...           Default cli arguments if no arguments are passed to the script
@delay=<millis>                   Set the delay between sends to <millis> 
@wait=<millis>                    One-time wait for <int> milliseconds 
@exitcmd=<cmd>                    Upon exiting, this command will be run 
@info [info string]               Print text to the terminal as "info" 
@error [string]                   Print text to the terminal as "error" 

--------- Loops: 
@loop                             Start of infinite loop 
@loop=<iterations>                Start of a loop with a fixed number of iterations 
@loop=<start>,<stop>              Start of a loop from <start> until <stop> is reached
@loop=<start>,<stop>,<incr>
@endloop                          Signals the end of a loop

-------- Variables:
$ARG                    All arguments passed to the script 
$ARG0, $ARG1, etc...    Specific argument passed to the script 
$LOOP                   All active loop indexes 
$LOOP0                  Reference a specific loop index, if nested loops are used. 

"""

SK_SET_HELP = """\
USEAGE:
sk-set -ls,--list                               List all settings 
sk-set [setting]=[value] [setting]=[value] ...  Set values for the UI 
"""

PORT_ALIAS_HELP = """\
USEAGE:
alias <name>        Set the alias for the current serial port
alias -ls           List all port aliases 
alias -h            Print this help text 
"""

SK_OPEN_HELP = """\
USEAGE:
sk-open [OPTIONS]        Select a file to open in the text viewer popup
sk-open <file>           Open a file in the text viewer popup

OPTIONS: 
    -h, --help          Print this help text 
    -e, --ext [ext]     Set the extensions to filter by 
    -d, --dir [dir]     Set the directory to open in 

EXAMPLES: 
(choose a file)
    sk-open -e "*.txt;*.py" -d "/home/user/Documents"
(open a file directly)
    sk-open data.txt
"""

COW_BORED = """
      Z Z   ^__^
        z z (--)\_______
            (__)\       )\\
                ||----w |
                ||     ||
"""

COW_GREED = """
        \   \__ /
         \  (``)\_______  
            (U )\       )|
                 ||---w ||
                 ||    ||
"""

COW_DEAD = """
            ^__^         
            (XX)\_______        George, not the livestock...   
            (__)_ *  * *)---            \  ,-----, 
              U ||--*-w |               ,--'---:---`--,
                ||     ||               ==(o)-----(o)==J
"""

COW_BUBBLES = """
  O   o     ^__^
      o  o  (*-)\_______
          o (o )\       )\\
                ||----w |
                ||     ||
"""

COW_IN_LOVE = """
        ^__^ ^__^
 ______/(-oo)(--)\_______
(       /( <)(> )\       )\\
|_______||        ||----w |
LL      LL        ||     ||
"""

COW_NERD = """
        \  ^___^
         \ (oo-)\___________
           (u_ )            |->
               \            |
                ||-------WW |
                ||         ||
"""

COW_RANDOM = (COW_NERD, COW_IN_LOVE, COW_BUBBLES, COW_GREED, COW_BORED)

COW_WISDOM = [
    "",
    "two can play the quiet game...",
    "moo, etc ",
    "my eyes are up here! ",
    "tell me a joke ",
    "cowsay is for people who haven't said enough",
    "whats your credit card number? ",
    "cowsay it ain't so",
    "you got any games on your phone?",
    ";)"
]

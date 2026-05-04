# Serial Killer 2.0 - A killer serial terminal 

As if there weren't enough serial terminals out there... 

`As you can tell, this readme is a work in progress.`


## Features: 

- CLI-Like and GUI interfaces
    - "Send" textbox doubles as a command-line interface
- Scripting 
    - Create your own scripts to automate serial interfaces and configure features.
- Logging
    - Log incoming, outgoing and informational messages to a file automatically 
    - Configurable log formatting, file naming, and logic 
- Keyboard Control 
    - Create a custom device interface using single key-presses (for example, controlling an RC car using your keyboard arrow keys)
- Plotting 
    - Plot incoming data in real-time in the "Plot" tab
    - Pick between a variety of plot types (Key-Value, Index-Value, Key-Array, Single-Array)
    - Customizable data parsing, filtering and scaling
    - Export data to CSV, or image files 
- User Extensions 
    - Write your own "Extensions" in python to interact with serial input and generate serial output
    - Extensions are driven by the main window, and loaded "on-the-fly" 
    - The user only needs to write logic for string input and output, and the rest is handled by the main window 
- Auto-Reconnect and Auto-Rescan features 
    - Reconnect to a lost port, or rescan for new ports 
- Saveable serial port configurations and aliases 
- Auto-Saved settings and preferences 
- Cross-Platform Compatable

## Built Using: 
- [pyqt6](https://pypi.org/project/PyQt6/)
- [pyserial](https://pypi.org/project/pyserial/)
- [pyqtGraph](https://pypi.org/project/pyqtgraph/)



![Serial Killer](./img/SK-GIF.gif)



# Install:
Prerequisites: 
- Python 3.10+
- pip


To install: 
1. Clone this repository, and take note of the path to the repository. 
2. Install the requirements: 
    ```
    pip install -r requirements.txt
    ```

Linux users will also need to add themselves to the "dialout" group if they aren't already. 


## (Optional) Create a desktop shortcut: 

### Ubuntu Linux: 

You will find a 'SK.desktop' file in this repository. 

Move the file to your "/usr/share/applications/" directory.   

Edit the file, replacing the `<PATH_TO_PYTHON>` and `<PATH_TO_SERIAL_KILLER>` with the actual path to your python executable and the path to the serial killer repository, respectively. 

```bash
sudo mv SK.desktop /usr/share/applications/
sudo chmod +x /usr/share/applications/SK.desktop    
sudo nano /usr/share/applications/SK.desktop
```

### Windows:

TODO 



# Run: 

Run Serial Killer by running the `SK.py` file. Optionally, include any useful arguments. 

```
Useage: 
python3 SK.py [OPTIONS] [-c OPEN_COMMANDS ...]

All arguments passed after '-c' will be executed as commands in serial killer when the program starts.

OPTIONS:
    -h, --help                          Show help and exit 
    -d, --debug [level]                 Set debug level to [level] if no [level] is provided, it is 1
    -v, --verbose                       Set debug level to 2
    -x, --xsize <size>                  Set the window width (default 700)
    -y, --ysize <size>                  Set the window height (default 800)
    -c, --commands <cmd> ...            Open commands 
    -q, --quit                          Quit the program (often used when updating UI files)
    -u, --update                        Update UI files
    --update-debug                      Update UI files in debug mode
    --reset                             Reset to default settings
```




# USER'S GUIDE 
## Table of Contents 
1. [General Usage](#general-usage)
2. [Commands](#commands)   
    - [con](#con) 
    - [dcon](#dcon) 
    - [settings](#settings) 
    - [plot](#plot) 
    - [ports](#ports) 
    - [log](#log) 
    - [script](#script) 
    - [key](#key) 
3. [Scripting](#scripting)
4. [Plotting](#plotting)
5. [Keyboard Control](#keyboard-control)
6. [Logging](#logging)
7. [Extensions](#extensions)

# General Usage 

# Commands 

## con 
Useage: 
```
con [port] [-b baud] [-]
```
## dcon 

## settings 

## plot 

## ports 

## log 

## script 

## key 
Useage: 
```
key <key> <value>
```
# Scripting 
Scripts are simple ways to automate serial communication. 
The loaded script exists in the "script" tab. 

## Script Syntax 

Each line of the script is executed, just like you had typed it in the command line. 
Each serial send is executed with a delay.

Because each line of text is executed as if it were typed in the command line, you can inject python expressions into the text by nesing them between `${}`. 

For example, 
```
${math.pi}
```


Empty lines are ignored. 

Comments are prefaced with a "#" symbol. Comments can occur in-line with other commands, or on their own line. 



When a line is prefaced with a "@" symbol, it is considered a command for serial killer. The delay is ignored and it is executed immediately. This can be a normal serial killer command, like `@con 0 -b 115200` or it can be a command specific for scripts (see below). 

When a line is prefaced with a ">" symbol, it is interpreted as an "explicit" send. The ">" is stripped and the rest of the line is sent to the serial port.
This may be useful if we want to send a command with a "#" or "@" symbol in it. 
Sending a newline alone can be done just by using ">". 


## Script Commands 
These are the script-specific commands that are currently implemented: 
```
@args=<arg0> [arg1] ...           Default cli arguments if no arguments are passed to the script
@delay=<millis>                   Set the delay between sends to <millis> 
@wait=<millis>                    One-time wait for <int> milliseconds 
@exitcmd=<cmd>                    Upon exiting, this command will be run 
@info=[string]                    Print text to the terminal as "info" 
@error=[string]                   Print text to the terminal as "error" 
@end                              End the script at this point. 

@loop                             Start of infinite loop 
@loop=<iterations>                Start of a loop with a fixed number of iterations 
@loop=<start>,<stop>              Start of a loop from <start> until <stop> is reached
@loop=<start>,<stop>,<incr>
@endloop                          Signals the end of a loop


$ARG                    All arguments passed to the script 
$ARG0, $ARG1, etc...    Specific argument passed to the script 
$LOOP                   All active loop indexes 
$LOOP0                  Reference a specific loop index, if nested loops are used. 

```

### @args=ARG0 ARG1 ...
`script <arg0> <arg1> ...`

This is the best way to implement a variables in a script. 
The script has access to the arguments passed to it from the command line when it is run. If they are NOT passed, the script can use default arguments in their place. These are set with the `@args=` command. 

example: 
```
# The first arguement will be the number of times to send the next argument 
@args=2 hello-world
@loop=$ARG0 
>sending $ARG1 
@endloop 
```
This will send "sending hello-world" twice. 



### @delay=[milliseconds]
This will set the delay between serial sends to the specified number of milliseconds. 
It will be applied to all serial sends in the script, until it is changed again. It has no effect on commands prefaced with an "@" symbol.


### @wait=[milliseconds]
This is a one-time wait for a specified number of milliseconds before advancing to the next line of the script. 


### @exitcmd=[CMD]

This sets a command that will be called when the script is terminated. It can be used several times, and each command will be called in the order they were set. 

example: 
```
@exitcmd=@plot export data.csv
@exitcmd=@dcon 
```



### @info 

### @error 

### @args 



### @loop 

Loops are often used for repeating sends. 

Loops start with `@loop` and end with `@endloop`. 
`@loop` without any arguments will loop forever. 
If this is not desired, you can specify a number of iterations with `@loop=<iterations>`.
Inside the loop, you can access the loop index with `$LOOP`  
For example, 

```
@loop=3
>Hello $LOOP
@endloop
```
This will send "Hello 0", then "Hello 1", then "Hello 2", then stop.  
We can also use the loop index in python expressions. 
```
@loop=3
>Hello ${math.pi * $LOOP}
@endloop
```
This will send "Hello 0", then "Hello 3.14", then "Hello 6.28", then stop.  


Loops can also be nested, and the loop index can be used to access the specific loop index:
```
@loop=3
    @loop=3
        >Hello $LOOP0 $LOOP1
    @endloop
@endloop
```











--------
# Plotting



```
plot <cmd> [options]

plot clear
plot key-value --keys "A,B,C,D" --refs "-10,0,10" 
```

## Tokenizing
When plotting is active, each line is processed at the same time. Each line is split into tokens by a list of any separators you have set. Empty tokens (from multiple separators) are ignored. Numerical tokens are converted to floats. 

Assuming your list of separators is " ,|;:=" than the line:
```
A: 123.4 , B=5.231 C;3.14 5.123
```
would be split into the tokens:
```
["A", 123.4, "B", 5.231, "C", 3.14, 5.123]
```


## Key-Value Plots:
Incoming data is expected to be in the format of key-value pairs. 
For example, if we have incoming data like this: 
```
GYRO_X = 10.11, GYRO_Y = 1.3435, GYRO_Z = 1.22
TEMP=1.32, PRESSURE=3.21,
GYRO_X = 11.33, GYRO_Y = 1.377, GYRO_Z = 7.22 
GYRO_X = 12.5, GYRO_Y = 1.35, GYRO_Z = 3.32 
TEMP=1.32, PRESSURE=3.21,
GYRO_X = 1.23, GYRO_Y = 1.32, GYRO_Z = 3.21 
```
Then a key-value plot will generate a plot that tracks "GYRO_X", "GYRO_Y", "GYRO_Z", "TEMP", and "PRESSURE" each time one of these key-value pairs is received. 

We can also filter the specific keys we are interested in by populating the "keys" textbox (or command argument). The keys you want to select must be separated by any "separators" you have set. For the example, if we only wanted to plot the Gyro values, we could set the keys to "GYRO_X,GYRO_Y,GYRO_Z" and all other key-value pairs would be ignored. 

## Index-Value Plots  

Index-Value plots are similar to key-value plots, but they don't expect a key-value pair. Instead, they expect a list of numerical values. 

For example, if we have incoming data like this: 
```
33.1, 11.2, 55.3, 123.4
21.5, 555.3, 111.9, 5.1, 33.1 
```

## Key-Array: 

## Single-Array: 

## Exporting Data

# Keyboard Control 

# Logging 

# Extensions 

Extensions allow you to write your own python interfaces for serial devices with minimal hassle. An extension is a python class that inherits from a common `SK_Extension` class. The derived class overrides functions that are called when certain events occur in the main window, such as incoming serial data, a port is connected, the extension is terminated, etc. 

Example uses for extensions: 
- Forwarding incoming serial data to a server
- Custom parsing and analysis of incoming serial data 
- Automated sensor testing and logging 
- Controlling a device 
- Automating device configuration 
- Flashing binary files to a device 

## Writing an Extension 

A new extension can be created by using the serial killer command 
```
ext new <name>
```

This will create a new extension in the `extensions` folder, and populate the file with the Extension Class Template. 

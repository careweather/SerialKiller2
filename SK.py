import subprocess
import sys 
import os 
from SK_common import BASE_DIR, DEFAULT_SETTINGS_FILE
import glob 
import termcolor 

def update_ui_files(debug = False):
    print(termcolor.colored("Updating UI files", "yellow"))

    ui_files = glob.glob(os.path.join(BASE_DIR, "ui_files", "*.ui"))
    for file in ui_files:
        output_file = os.path.join(BASE_DIR, "GUI_" + os.path.basename(file).removesuffix(".ui").upper() + ".py")
        print(termcolor.colored(f"Updating {file} -> {output_file}", "white"))
        if debug: 
            cmd = f"pyuic6 --output {output_file} --debug {file}"
        else:
            cmd = f"pyuic6 --output {output_file} {file}"
        error = subprocess.call([cmd], shell=True)
        if error != 0:
            print(termcolor.colored(f"Error {error} compiling {file} to {output_file}", "red"))
    print(termcolor.colored("UI files updated sucessfully!", "green"))
    if __name__ != "__main__":
        print(termcolor.colored(f"---WARNING---\nTerminating after update!\n\tThe program was not run starting from the source {__file__}\n\tUpdating from .ui files and THEN starting the program can only be done from SK.py.\n\tTo run serial killer, rerun from SK.py or remove the -u flag", color = "yellow"))
        exit(0)
        
    #exit(0)


CLI_HELP = """\
USEAGE :
sk
sk [OPTIONS] [-c OPEN_COMMANDS ...]

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
    --dark                              Force dark mode (ignore system theme)
""" 

def run():
    input_args = sys.argv[1:]
    open_commands = []
    x_size = 700
    y_size = 800
    force_dark = False
    has_open_cmds = False 
    while input_args:
        arg = input_args.pop(0)
        if has_open_cmds:
            open_commands.append(arg)
            continue 
        elif arg in ['-h', '--help']:
            print(CLI_HELP)
            exit(0)
        elif arg in ["--update", "-u"]:
            update_ui_files()
        elif arg in ["--update-debug"]:
            update_ui_files(debug = True)
        elif arg in ['-q', '--quit']:
            exit(0)
        elif arg in ['-v', '--verbose']:
            import SK_common
            SK_common.DEBUG_LEVEL = SK_common.DEBUG_LEVEL_VERBOSE
            SK_common.vprint(f"Debug level set to {SK_common.DEBUG_LEVEL}", color = "green")
        elif arg in ['-d', '--debug']:
            import SK_common
            lvl = SK_common.DEBUG_LEVEL_DEBUG
            if input_args:      
                try: 
                    lvl = int(input_args[0])
                    input_args.pop(0)
                except Exception as e:
                    print(e)
                    #print("Using default debug level 1")
            SK_common.DEBUG_LEVEL = lvl
            termcolor.cprint(f"Debug level set to {lvl}", color ="yellow")
        elif arg in ['-x', '--xsize']:
            x_size = int(input_args.pop(0))
        elif arg in ['-y', '--ysize']:
            y_size = int(input_args.pop(0))
        elif arg in ['-c', '--commands']:
            has_open_cmds = True 
        elif arg in ['--dark']:
            force_dark = True
            termcolor.cprint("Forcing dark mode", color="cyan")
        elif arg in ['--reset']:
            print("Reverting to default settings")
            from SK_common import DEFAULT_SETTINGS_FILE, DEFAULT_SCRIPT_PATH, DEFAULT_LOG_PATH, DEFAULT_EXTENSION_PATH, DEFAULT_RESOURCES_PATH, DEFAULT_SETTINGS_PATH
            import shutil
            if not os.path.exists(DEFAULT_SCRIPT_PATH):
                os.makedirs(DEFAULT_SCRIPT_PATH)
            if not os.path.exists(DEFAULT_LOG_PATH):
                os.makedirs(DEFAULT_LOG_PATH)
            if not os.path.exists(DEFAULT_EXTENSION_PATH):
                os.makedirs(DEFAULT_EXTENSION_PATH)
            if not os.path.exists(DEFAULT_SETTINGS_PATH):
                os.makedirs(DEFAULT_SETTINGS_PATH)

            for file in os.listdir(DEFAULT_RESOURCES_PATH):
                if file.endswith(".py"):
                    print(f"Copying {file} to {DEFAULT_EXTENSION_PATH}")
                    shutil.copy2(os.path.join(DEFAULT_RESOURCES_PATH, file), os.path.join(DEFAULT_EXTENSION_PATH, file))
                elif file.endswith(".txt"):
                    print(f"Copying {file} to {DEFAULT_SCRIPT_PATH}")
                    shutil.copy2(os.path.join(DEFAULT_RESOURCES_PATH, file), os.path.join(DEFAULT_SCRIPT_PATH, file))
            
            shutil.copy2(DEFAULT_SETTINGS_FILE, os.path.join(DEFAULT_SETTINGS_PATH, "default_backup.json"))
            os.remove(DEFAULT_SETTINGS_FILE)
        else:
            print(f"ERROR: Invalid cli argument: {arg}")
            print(CLI_HELP)
            exit(0)
    
    import SK_main_window
    SK_main_window.run_app(x_size, y_size, open_commands, force_dark=force_dark)

if __name__ == "__main__":
    run()
#!/usr/bin/env python3
"""
Synchronized SerialKiller2 Script Launcher
This script launches two SerialKiller2 instances and starts their scripts simultaneously
"""

import subprocess
import time
import sys
import os
from threading import Thread

def launch_sk2_instance(port, script_file, position_x=0, position_y=0):
    """Launch a SerialKiller2 instance with specific script and port"""
    # You may need to adjust these commands based on your specific setup
    cmd = [
        "python", "SK.py",
        "-c", 
        f"con {port}",  # Connect to specific port
        f"script -o {script_file}",  # Open specific script file
        "script"  # Run the script
    ]
    
    print(f"Launching SK2 instance for port {port} with script {script_file}")
    return subprocess.Popen(cmd, cwd=os.getcwd())

def main():
    # Configuration - adjust these values for your setup
    HELMHOLTZ_PORT = "COM3"  # Replace with your Helmholtz port
    SATELLITE_PORT = "COM4"  # Replace with your satellite port
    HELMHOLTZ_SCRIPT = "scripts/helmholtz_script.txt"  # Path to your Helmholtz script
    SATELLITE_SCRIPT = "scripts/satellite_script.txt"  # Path to your satellite script
    
    if len(sys.argv) > 1:
        if sys.argv[1] in ["-h", "--help"]:
            print("Usage: python sync_scripts.py")
            print("Make sure to edit the script to set your COM ports and script file paths")
            return
    
    print("SerialKiller2 Synchronized Script Launcher")
    print("==========================================")
    print(f"Helmholtz Port: {HELMHOLTZ_PORT}")
    print(f"Satellite Port: {SATELLITE_PORT}")
    print(f"Helmholtz Script: {HELMHOLTZ_SCRIPT}")
    print(f"Satellite Script: {SATELLITE_SCRIPT}")
    print()
    
    # Verify script files exist
    if not os.path.exists(HELMHOLTZ_SCRIPT):
        print(f"ERROR: Helmholtz script not found: {HELMHOLTZ_SCRIPT}")
        return
    if not os.path.exists(SATELLITE_SCRIPT):
        print(f"ERROR: Satellite script not found: {SATELLITE_SCRIPT}")
        return
    
    print("Launching instances in 3 seconds...")
    for i in range(3, 0, -1):
        print(f"{i}...")
        time.sleep(1)
    
    print("LAUNCHING NOW!")
    
    # Launch both instances simultaneously using threads for minimal delay
    def launch_helmholtz():
        return launch_sk2_instance(HELMHOLTZ_PORT, HELMHOLTZ_SCRIPT, 0, 0)
    
    def launch_satellite():
        return launch_sk2_instance(SATELLITE_PORT, SATELLITE_SCRIPT, 800, 0)
    
    thread1 = Thread(target=launch_helmholtz)
    thread2 = Thread(target=launch_satellite)
    
    # Start both threads at the same time
    start_time = time.time()
    thread1.start()
    thread2.start()
    
    # Wait for both to complete
    thread1.join()
    thread2.join()
    
    end_time = time.time()
    print(f"Both instances launched in {(end_time - start_time)*1000:.2f}ms")
    print("Scripts should now be running on both instances!")

if __name__ == "__main__":
    main() 
#!/bin/bash

# This script will be used to give me audio cues for when the test starts and when the timer is done, 
# It will also be used to start recording video and audio data using guvcview and recording that data to a video file.
# then once the test is completed, it will stop the recording and upload the video file to google drive via rclone.

# THis script must take a command line argument that is the name of the test, this will be used to save the video file with the correct name.

# If the command line argument is not provided, print an error message and exit
if [ -z "$1" ]; then
    echo "Error: No test name provided"
    exit 1
fi

# Set the test name
test_name=$1
echo "Test Timer and Recording Script started"
echo "Provided test name: $test_name"

# Function to display countdown
countdown() {
    local duration=$1
    local message=$2
    
    echo "$message"
    for ((i=duration; i>0; i--)); do
        printf "\rTime remaining: %02d:%02d" $((i/60)) $((i%60))
        sleep 1
    done
    printf "\rTime remaining: 00:00\n"
}

# Countdown to test start (60 seconds)
countdown 60 "Starting countdown to test..."

# Play sound and announce test start
paplay /usr/share/sounds/freedesktop/stereo/complete.oga && echo "Time is up, BeagleBone is booting!"

# Countdown for beaglebone booting (13 seconds)
countdown 13 "Test about to start, beaglebone booting!"

# begin recording video and audio data to the ~/Videos/veery_tests directory
ffmpeg -f v4l2 -framerate 30 -video_size 1280x720 -i /dev/video0 -f pulse -i alsa_input.usb-Arducam_Arducam_IMX179_8MP_Camera_YLAF20221208V0-02.analog-stereo -t 210 -c:v libx264 -c:a aac ~/Videos/veery_tests/$test_name.mp4 & 

# Play sound and announce test start
paplay /usr/share/sounds/freedesktop/stereo/complete.oga && echo "Test has started!"

# Countdown to test end (200 seconds)
countdown 200 "Test in progress - countdown to end..."

# Play sound and announce test end
paplay /usr/share/sounds/freedesktop/stereo/complete.oga && echo "Test has ended!"

# The recording should have already ended, but may take another few seconds to finish, just wait for a few seconds to be sure
countdown 10 "Waiting for recording to finish..."

# Now upload the video file to google drive via rclone
rclone copy ~/Videos/veery_tests/$test_name.mp4 gdrive:Veery_adcs_tests/

# Print a message to the terminal that the video file has been uploaded
echo "Video file has been uploaded to google drive"

# Print a message to the terminal that the script has completed
echo "Script has completed"

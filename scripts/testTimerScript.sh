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

# begin recording video and audio data to the ~/Videos/veery_tests directory
ffmpeg -y -f v4l2 -input_format mjpeg -framerate 30 -video_size 1280x720 -i /dev/video4 -f pulse -i alsa_input.usb-Arducam_Arducam_IMX179_8MP_Camera_YLAF20221208V0-02.analog-stereo -t 215 -c:v libx264 -profile:v main -pix_fmt yuv420p -c:a aac -thread_queue_size 1024 ~/Videos/veery_tests/$test_name.mp4 &

# Wait 13 seconds silently, then play ding sound
sleep 13
paplay /usr/share/sounds/freedesktop/stereo/complete.oga && echo "Test has started!"

# Wait for the recording to finish (215 seconds total - 13 seconds already waited = 202 seconds)
sleep 202

# Play sound and announce test end
paplay /usr/share/sounds/freedesktop/stereo/complete.oga && echo "Test has ended!"

# Now upload the video file to google drive via rclone
rclone -P copy ~/Videos/veery_tests/$test_name.mp4 gdrive:Veery_adcs_tests/

# Print a message to the terminal that the video file has been uploaded
echo "Video file has been uploaded to google drive"

# Print a message to the terminal that the script has completed
echo "Script has completed"
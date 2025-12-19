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

test_name="$1"

# Ensure output directory exists
mkdir -p "$HOME/Videos/veery_tests"

# Play sound and announce test start
paplay /usr/share/sounds/freedesktop/stereo/complete.oga && echo "Test has started!"

# Begin recording video and audio data to the ~/Videos/veery_tests directory
# Run until user presses a key, then stop gracefully and continue

# Start ffmpeg without a fixed duration; run in background
ffmpeg -y -thread_queue_size 1024 \
    -f v4l2 -input_format mjpeg -framerate 30 -video_size 1280x720 -thread_queue_size 1024 -i /dev/video4 \
    -f pulse -i alsa_input.usb-Arducam_Arducam_IMX179_8MP_Camera_YLAF20221208V0-02.analog-stereo \
    -c:v libx264 -profile:v main -pix_fmt yuv420p -c:a aac \
    "$HOME/Videos/veery_tests/${test_name}.mp4" &

ffmpeg_pid=$!

# Ensure we stop ffmpeg on script exit (e.g., Ctrl+C)
cleanup() {
    if kill -0 "$ffmpeg_pid" 2>/dev/null; then
        kill -INT "$ffmpeg_pid" 2>/dev/null
        wait "$ffmpeg_pid" 2>/dev/null
    fi
}
trap cleanup EXIT

echo "Recording... Press any key to stop."
# Wait for a single keypress silently
read -n1 -s _

# Stop recording gracefully (SIGINT lets ffmpeg finalize the file)
kill -INT "$ffmpeg_pid" 2>/dev/null
wait "$ffmpeg_pid" 2>/dev/null

# Play sound and announce test end
paplay /usr/share/sounds/freedesktop/stereo/complete.oga && echo "Test has ended!".

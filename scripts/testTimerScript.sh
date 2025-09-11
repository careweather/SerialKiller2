#!/bin/bash

# This script will be used to give me audio cues for when the test starts and when the timer is done.

echo "Test Timer Script started"

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

# Countdown for beaglebone booting (14 seconds)
countdown 14 "Test about to start, beaglebone booting!"

# Play sound and announce test start
paplay /usr/share/sounds/freedesktop/stereo/complete.oga && echo "Test has started!"

# Countdown to test end (200 seconds)
countdown 200 "Test in progress - countdown to end..."

# Play sound and announce test end
paplay /usr/share/sounds/freedesktop/stereo/complete.oga && echo "Test has ended!"
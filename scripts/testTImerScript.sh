#!/bin/bash

# This script will be used to give me audio cues for when the test starts and when the timer is done.

echo "Test Timer Script started"
sleep 60 && paplay /usr/share/sounds/freedesktop/stereo/complete.oga && echo "Test has started!"
sleep 200 && paplay /usr/share/sounds/freedesktop/stereo/complete.oga && echo "Test has ended!"
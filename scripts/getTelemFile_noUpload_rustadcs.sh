# THis script must take a command line argument that is the name of the test, this will be used to save the video file with the correct name.

# If the command line argument is not provided, print an error message and exit
if [ -z "$1" ]; then
    echo "Error: No test name provided"
    exit 1
fi

output_file_name=$1
echo "Getting telem file from the satellite and naming it: $output_file_name.csv"

# Get the telem file from the satellite
sshpass -p 'veery' ssh -o StrictHostKeyChecking=no root@192.168.0.2 "cat /etc/telem.csv" > ~/careweather/operations/Data_reading/raw_data_files/$output_file_name.csv

# Print a message to the terminal that the telem file has been downloaded
echo "Telem file has been saved to the ~/careweather/operations/Data_reading/raw_data_files directory "

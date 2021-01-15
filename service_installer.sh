#!/bin/bash

echo "NOTE: There is no error checking, make sure you're inputs are correct"

# Get necessary paths
cmd='which python3'
path_to_python=$($cmd)
cmd='pwd'
current_working_directory=$($cmd)
path_to_manage="$current_working_directory/TvShuffleForPlex/manage.py"
cmd='which pip3'
path_to_pip=$($cmd)


# Get hostname and port from user
echo 'Enter the IP to run the app on: '
read host_name
echo 'Enter the PORT to run the app on: '
read port_number

# Generate the service file
service_file="[Install]
WantedBy=multi-user.target

[Unit]
Description=TV Shuffle For Plex
After=network.target
StartLimitIntervalSec=0

[Service]
WorkingDirectory=$current_working_directory
Type=simple
Restart=always
RestartSec=1
ExecStart=$path_to_python $path_to_manage runserver $host_name:$port_number
"
echo "$service_file" > TvShuffleForPlex.service

# Install pip requirements
cmd="path_to_pip install -r requirements.txt"
output=$($cmd)
echo $output

# Make DB migrations
cmd="$path_to_python $path_to_manage makemigrations"
output=$($cmd)
echo $output
cmd="$path_to_python $path_to_manage migrate"
output=$($cmd)
echo $output

# Link the service file
cmd="systemctl link ./TvShuffleForPlex.service"
output=$($cmd)
echo $output

# Reload the daemon
cmd="systemctl daemon-reload"
output=$($cmd)
echo $output

# Enable the service
cmd="systemctl enable TvShuffleForPlex.service"
output=$($cmd)
echo $output

# Start the service
cmd="systemctl start TvShuffleForPlex.service"
output=$($cmd)
echo $output

echo "App service installed, go to 'http://$host_name:$port_number/login' in your browser"

#!/bin/bash

echo "NOTE: Uninstall the TvShuffleForPlex service"

# Stop the service
cmd="systemctl stop TvShuffleForPlex.service"
output=$($cmd)
echo $output

# Disable the service
cmd="systemctl disable TvShuffleForPlex.service"
output=$($cmd)
echo $output

echo "The app service has been removed"
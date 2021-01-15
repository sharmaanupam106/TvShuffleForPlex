# TvShuffleForPlex
![](https://img.shields.io/badge/Python%20Versions-3.7%7C3.8%7C3.8-blue)
![](https://img.shields.io/github/issues/sharmaanupam106/TvShuffleForPlex)
![](https://img.shields.io/github/license/sharmaanupam106/TvShuffleForPlex)

## Description
The purpose of this application is to allow a chronological shuffling of tv shows.
The selected TV Shows maybe shuffled however the episodes will be selected based on next unwatched.

NOTE: This is not a secure site, keep it within your local network. (no port forwarding)

## How it works
- You select a series of TV shows you want to see
- You select the length of the queue you want generated. (default 20)
- You select shuffle.
    - Inclusive shuffle will only pick episodes from the selected tv shows
    - Exclusive shuffle will only pick episodes from all shows **_NOT_** selected.
- The app will randomly pick a show from your selected tv shows list, and find the next unwatched episode to put in the queue slot
    - It will move on to the next queue slot and pick a random show to do the same with.
    - If a show is selected for 2 or more slots and the next unwatched episode is already in the queue, the later slot will get the episode following the last episode in the list, keeping the order of episodes in the queue in order.
- Once the queue is generate, you select which active client you want the queue sent to for viewing.

## High level functionalities
- Allow users to select the plex server from which to source tv shows.
- Allow users to multi select tv shows from which shuffled (inclusive and exclusive) episodes will be selected.
- Allow users to save the selected tv shows as lists, making it easier to come back to the same list of shows.
- Allow users to set the max number of episodes that will be put in the plex queue.
- Allow users to push the generated episodes plex queue to a given client.

## Supported Systems
- Ubuntu 20.x - Manjaro 20.x
- Windows 10 (64bit)

## Installation

### **LINUX**

#### Auto Service Install
Does the same steps as the Manual Install

1. Download the [Git Repo](https://github.com/sharmaanupam106/TvShuffleForPlex)
    - [Main](https://github.com/sharmaanupam106/TvShuffleForPlex/tree/main)
2. Run the `service_install.sh` script _**This script required elevated privileges to run**_
    - Use `sudo service_install.sh` to prevent having to put your password multiple times, or erring out 
    - Uninstall using `service_uninstall.sh` script _**This script required elevated privileges to run**_

#### Manual install

1. Download the [Git Repo](https://github.com/sharmaanupam106/TvShuffleForPlex)
    - [Main](https://github.com/sharmaanupam106/TvShuffleForPlex/tree/main)
2. Install the requirements
    `pip3 install -r requirements.txt`
3. Make migrations
    ```
    python3 manage.py makemigrations
    python3 manage.py migrate
    ```
4. Start the application
    `python3 manage.py runserver {IP}:{PORT}`

##### Optional
- Create and Enable a service.
    - Create service file `touch TvShuffleForPlex.service`
    - Edit the file with the following _(Make sure you update all {} with the correct info)_
    ```
    [Install]
    WantedBy=multi-user.target
    
    [Unit]
    Description=TV Shuffle For Plex
    After=network.target
    StartLimitIntervalSec=0
    
    [Service]
    WorkingDirectory={INSTALL PATH}
    Type=simple
    Restart=always
    RestartSec=1
    ExecStart={FULL PATH TO PYTHON3} {INSTALL PATH}/TvShuffleForPlex/manage.py runserver {IP}:{PORT}
    ```
    - Link the to service controller `systemctl link ./TvShuffleForPlex.service`
    - Reload daemon `systemctl daemon-reload`
    - Enable the service `systemctl enable TvShuffleForPlex.service`
        - Will automatically start the service on boot.
    - Start the service `systemctl start TvShuffleForPlex.service`
        - Check to make sure the service started normally without errors `systemctl status PlexTvStation.service`
- Starting and Stopping the service
    - Start service `systemctl start TvShuffleForPlex.service`
    - Stop service `systemctl stop TvShuffleForPlex.service`
#### Troubleshooting
- Read the log files at `{INSTALL PATH}/TvShuffleForPlex/_tvshuffleforplex/logs`
- Read console outputs `journalctl -u TvShuffleForPlex.service`
- Google errors that might occur.

### **Windows**

_Thank you to [NSSM - Non-sucking Service Manager](https://nssm.cc/) for making Windows service creation simple_

#### Auto Service Install
Does the same steps as the Manual Install

1. Download the [Git Repo](https://github.com/sharmaanupam106/TvShuffleForPlex)
    - [Main](https://github.com/sharmaanupam106/TvShuffleForPlex/tree/main)
2. Run the `service_install.bat` script _**This script required elevated privileges to run**_
    - Uninstall using `service_uninstall.bat` script _**This script required elevated privileges to run**_

#### Manual install

1. Download the [Git Repo](https://github.com/sharmaanupam106/TvShuffleForPlex)
    - [Main](https://github.com/sharmaanupam106/TvShuffleForPlex/tree/main)
2. Install the requirements
    `pip3 install -r requirements.txt`
3. Make migrations
    ```
    python3 manage.py makemigrations
    python3 manage.py migrate
    ```
4. Start the application
    `python3 manage.py runserver {IP}:{PORT}`
   
##### Optional
- Create and Enable a service.
    Using [NSSM - Non-sucking Service Manager](https://nssm.cc/) located in {INSTALL PATH}\nssm-2.24\win64\nssm.exe
  
    _(Make sure you update all {} with the correct info)_
    - Create a service from an admin cmd `nssm.exe install TvShuffleForPlex {FULL PATH TO PYTHON} {INSTALL PATH}/TvShuffleForPlex/manage.py runserver {IP}:{PORT}`
    - Start the service `nssm.exe start TvShuffleForPlex`
    - Check the status of the service `nssm.exe status TvShuffleForPlex`
    
## Usage
- Login with your plex account
    ```
    http://{IP}:{PORT}/login
    ```
    
    ![Login](https://user-images.githubusercontent.com/50554850/103911884-97807880-50d4-11eb-99d7-dee320f46cb7.gif)
- Select a plex server
    
    ![ServerSelect](https://user-images.githubusercontent.com/50554850/103912591-79ffde80-50d5-11eb-97b7-4d3a850283b7.gif)
- Select TV Shows
    
    ![ShowSelect](https://user-images.githubusercontent.com/50554850/103912593-7a987500-50d5-11eb-91ee-f2dc50db36dc.gif)
- Shuffle the Shows
    - Inclusive/Exclusive select
    - Max episodes in generate queue
    
    ![Shuffle](https://user-images.githubusercontent.com/50554850/103912594-7a987500-50d5-11eb-8ee9-8a1d88e5e7db.gif)
- Shuffle the list
- Select a client to push the queue to
    
    ![ClientPush](https://user-images.githubusercontent.com/50554850/103912584-78ceb180-50d5-11eb-910f-2d689eaf6c61.gif)
- Save the selected list
    
    ![SaveList](https://user-images.githubusercontent.com/50554850/103912586-79674800-50d5-11eb-8f4a-35a8d4f86920.gif)
- Select saved List
    
    ![SelectList](https://user-images.githubusercontent.com/50554850/103912589-79ffde80-50d5-11eb-8967-2df0f4d9c77e.gif)

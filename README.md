# TvShuffleForPlex
![Python Version](https://img.shields.io/badge/Python-3.8-blue)
![Open Issues](https://img.shields.io/github/issues/sharmaanupam106/PlexTvStation)

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
**Currently only tested on LINUX systems.** - Ubuntu 20.x - Manjaro 20.x

## Installation **(LINUX)**

1. Download the git repo
2. Install the requirements
    `pip3 install -r requirements.txt`
3. Generate and record a secret key. `python manage.py shell -c 'from django.core.management import utils; print(utils.get_random_secret_key())'`
    - Keep this handy for the next step
4. Update the following parameters in `settings.py`
   ```
   SECRET_KEY = "{KEY FROM STEP 3}"
   DEBUG = False
   ```
5. Make migrations
    ```
    python3 manage.py makemigrations
    python3 manage.py migrate
    ```
6. Start the application
    `python3 manage.py runserver <IP>:<PORT>`

### Optional
- Create and Enable a service. _(**NOTE**: Done under the `root` user, if you wish to use a different user, please use sudo when running systemctl commands)_
    - Create service file `touch TvShuffleForPlex.service`
    - Edit the file with the following _(Make sure you update all {} with the correct info)_
    ```
    [Unit]
    Description=TV Shuffle For Plex
    User={USER}
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
## Troubleshooting
- Read the log files at `{INSTALL PATH}/TvShuffleForPlex/_tvshuffleforplex/logs`
- Read console outputs `journalctl -u TvShuffleForPlex.service`
- Google errors that might occur.

## Usage
- Login with your plex account
    ```
    http://<IP>:<PORT>/login
    ```
    ![LogIn](https://imgur.com/ac6nWyq)
- Select a plex server
    ![Server Select](https://imgur.com/afGCCoX)
- Select TV Shows
    ![Show Select](https://imgur.com/Td1wZgG)
- Shuffle the Shows
    - Inclusive/Exclusive select
    - Max episodes in generate queue
    ![Shuffle](https://imgur.com/6Y7EeIY)
- Shuffle the list
- Select a client to push the queue to
    ![Client Push](https://imgur.com/Dy3qLvT)
- Save the selected list
    ![Save List](https://imgur.com/AMEQB83)
- Select saved List
    ![Select List](https://imgur.com/na0sQy7)

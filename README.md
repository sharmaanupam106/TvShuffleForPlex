# PlexTvStation

## Description
The purpose of this application is to allow a chronological shuffling of tv shows.
The selected TV Shows maybe shuffled however the episodes will be selected based on next unwatched, giving a network style tv guide.

NOTE: This is not a secure site, keep it within your local network. (no port forwarding)

## High level functionalities
- Allow users to select the plex server from which to source tv shows.
- Allow users to multi select tv shows from which shuffled (inclusive and exclusive) episodes will be selected.
- Allow users to save the selected tv shows as lists, making it easier to come back to the same list of shows.
- Allow users to set the max number of episodes that will be put in the plex queue.
- Allow users to push the generated episodes plex queue to a given client.

## Installation (LINUX)
1. Download the git repo
2. Install the requirements
    `pip3 install -r requirements.txt`
3. Make migrations
    ```
    python3 manage.py makemigrations
    python3 manage.py migrate
    ```
4. Start the application
    `python3 manage.py runserver <IP>:<PORT>`

### Optional
- Create and Enable a service. _(**NOTE**: Done under the `root` account, if you wish to use a different user, please use sudo when running systemctl commands)_
    - Create service file `touch PlexTvStation.service`
    - Edit the file with the following (Make sure you update all {} with the correct info)
    ```
    [Unit]
    Description=Plex TV Station
    User={USER}
    After=network.target
    StartLimitIntervalSec=0
    [Service]
    WorkingDirectory={INSTALL PATH}
    Type=simple
    Restart=always
    RestartSec=1
    ExecStart={FULL PATH TO PYTHON3} {INSTALL PATH}/manage.py runserver {IP}:{PORT}
    ```
    - Link the to service controller `systemctl link PlexTvStation.service`
    - Reload daemon `systemctl daemon-reload`
    - Enable the service `systemctl enable PlexTvStation.service`
    - Start the service `systemctl start PlexTvStation.service`
        - Check to make sure the service started normally without errors `systemctl status PlexTvStation.service`
- The service will automatically be started on boot
    - Start service `systemctl start PlexTvStation.service`
    - Stop service `systemctl stop PlexTvStation.service`
## Troubleshooting
- You may have to add the IP into the settings file.
```
<INSTALL PATH>/PlexTvStation/setting.py
Update line:
    ALLOWED_HOSTS = ["<IP>"]
``` 
- Read the log files at
```
<INSTALL PATH>/PlexTvStation/plextvstation/logs
```
- Read console outputs
- Google errors that might occur.

## Usage
- Login with your plex account
```
http://<IP>:<PORT>/login
```
![Login](UsageSamples/login.mp4?raw=true)
- Select a plex server
- Select TV Shows
- Shuffle the Shows
    - Inclusive/Exclusive select
    - Max episodes in generate queue
- Shuffle the list
- Select a client to push the queue to
- Save the selected list
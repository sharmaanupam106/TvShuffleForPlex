# PlexTvStation

## Description
The purpose of this application is to allow a chronological shuffling of tv shows.
The selected TV Shows maybe shuffled however the episodes will be selected based on next unwatched, giving a network style tv guide.

NOTE: This is not a secure site, keep it within your local network. (no port forwarding)

## High level functionalities
- Allow users to select the plex server from which to source tv shows.
- Allow users to multi select tv shows from which shuffled (inclusive and exclusive) episodes will be selected.
- Allow users to save the selected tv shows as lists, making it easier to come back to the same list.
- Allow users to set the max number of episodes that will be put in the plex queue.
- Allow users to push the generated episodes plex queue to a given client.

## Installation (LINUX)
1. Download the git repo
2. Install the requirements
    `pip3 install -r requirements.txt`
3. Start the application
    `python3 manage.py runserver <IP>:<PORT>`

### Optional steps
1. Create a service.
2. Enable the service.

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

## Usage
- Login with your plex account
```
http://<IP>:<PORT>/login
```
- Select a plex server
- Select TV Shows
- Shuffle the Shows
    - Inclusive/Exclusive select
    - Max episodes in generate queue
- Shuffle the list
- Select a client to push the queue to
- Save the selected list
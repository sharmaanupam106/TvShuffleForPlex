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

## Note
**Currently only tested on LINUX systems.** - Ubuntu 20.x - Manjaro 20.x

## Installation **(LINUX)**
#### REQUIREMENTS
- Python3.8 or grater
- All packages in requirements.txt 
1. Download the git repo
2. Install the requirements
    `pip3 install -r requirements.txt`
3. Generate and record a secret key. `python manage.py shell -c 'from django.core.management import utils; print(utils.get_random_secret_key())'`
    - Keep this handy for the next step
4. Update the following parameters in `{INSTALL PATH}/PlexTvStation/settings.py`
   ```
   SECRET_KEY = "{KEY FROM STEP 3}"
   DEBUG = False
   ```
   - This is done for application security
5. Make migrations
    ```
    python3 manage.py makemigrations
    python3 manage.py migrate
    ```
6. Start the application
    `python3 manage.py runserver <IP>:<PORT>`

### Optional
- Create and Enable a service. _(**NOTE**: Done under the `root` account, if you wish to use a different user, please use sudo when running systemctl commands)_
    - Create service file `touch {INSTALL PATH}/PlexTvStation.service`
    - Edit the file with the following _(Make sure you update all {} with the correct info)_
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
    ExecStart={FULL PATH TO PYTHON3} {INSTALL PATH}/PlexTvStation/manage.py runserver {IP}:{PORT}
    ```
    - Link the to service controller `systemctl link {INSTALL PATH}/PlexTvStation.service`
    - Reload daemon `systemctl daemon-reload`
    - Enable the service `systemctl enable PlexTvStation.service`
        - Will automatically start the service on boot.
    - Start the service `systemctl start PlexTvStation.service`
        - Check to make sure the service started normally without errors `systemctl status PlexTvStation.service`
- Starting and Stopping the service
    - Start service `systemctl start PlexTvStation.service`
    - Stop service `systemctl stop PlexTvStation.service`
## Troubleshooting
- Read the log files at `{INSTALL PATH}/PlexTvStation/plextvstation/logs`
- Read console outputs `journalctl -u PlexTvStation.service`
- Google errors that might occur.

## Usage
- Login with your plex account
    ```
    http://<IP>:<PORT>/login
    ```
    ![LogIn](https://user-images.githubusercontent.com/50554850/103680804-b22be380-4f54-11eb-805e-be88c33bcd7b.mp4)
- Select a plex server
    ![Server Select](https://user-images.githubusercontent.com/50554850/103681439-77767b00-4f55-11eb-9c7b-366908e8d761.mp4)
- Select TV Shows
    ![Show Select](https://user-images.githubusercontent.com/50554850/103681471-82c9a680-4f55-11eb-91fc-cd2fab8fcbc9.mp4)
- Shuffle the Shows
    - Inclusive/Exclusive select
    - Max episodes in generate queue
    ![Shuffle](https://user-images.githubusercontent.com/50554850/103681522-9117c280-4f55-11eb-98a9-920b1a1b1fa4.mp4)
- Shuffle the list
- Select a client to push the queue to
    ![Client Push](https://user-images.githubusercontent.com/50554850/103681137-19e22e80-4f55-11eb-85b7-a96af9669d10.mp4)
- Save the selected list
    ![Save List](https://user-images.githubusercontent.com/50554850/103681290-45fdaf80-4f55-11eb-8d61-c5dcbd626cab.mp4)
- Select saved List
    ![Select List](https://user-images.githubusercontent.com/50554850/103681380-62015100-4f55-11eb-9623-e6d0d1163b1c.mp4)

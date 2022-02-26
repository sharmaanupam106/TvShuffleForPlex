# Imports
import random
import os
from pathlib import Path
from typing import Union, List

# Plex imports
from plexapi.myplex import MyPlexAccount, MyPlexResource
from plexapi.server import PlexServer
from plexapi.client import PlexClient
from plexapi.playqueue import PlayQueue
from plexapi.video import Show, Movie, Episode, Season
from plexapi.exceptions import Unauthorized, NotFound, BadRequest

from .LIB import LIB


# Plex class to assist with plex api interaction
class Plex:
    """
    The PLEX object used to communicate with the plex server.

    :param str username: Your PLEX username
    :param str password: Your PLEX password
    :param LIB lib: A lib instance to be used for logging.

    :ivar PlexServer plex: The PLEX server object
    :ivar PlexClient client: A PLEX client
    :ivar str message: A message string used to pass messages back to django
    """
    def __init__(self, username: str = None, password: str = None, lib: LIB = None):
        self.message = None
        self.logged_in = False
        self.play_queue = None
        self.selected_shows = []
        self.connected_to_server = False
        # Try to connect to the users plex account
        try:
            self.my_account: MyPlexAccount = MyPlexAccount(username=username, password=password)
            self.logged_in = True

        # Error logging in
        except Unauthorized as e:
            self.message = "Incorrect username or password"

        # Unknown error
        except Exception as e:
            self.message = "Something went wrong"

        # Set the plex server and client to None for later definition
        self.plex: PlexServer = None
        self.client: PlexClient = None
        if lib is not None:
            self.lib = lib
        else:
            self.lib = LIB(home=str(Path(os.path.dirname(os.path.realpath(__file__)))))

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return str(self.__dict__)

    # Get all the moves on the plex server
    def get_movies(self) -> [Movie]:
        """
        Get movies on the PLEX server

        :return [Movie]: List of Movies
        """
        all_entries = []
        try:
            all_entries = self.plex.library.search(titile="", libtype="movie")
        except Exception as e:
            self.lib.write_error(f"Error getting movies {e=}")
        return all_entries

    # Get a plex movie given the name
    def get_movie(self, name: str) -> Movie:
        """
        Get a movie given the name

        :param str name: Name of the movie to get from PLEX
        :return Movie: The Movie
        """
        try:
            entry = self.plex.library.search(title=name, libtype='movie')[0]
        except Exception as e:
            self.lib.write_error(f"Error getting movie {e=}")
            entry = None
        return entry

    # Get all the shows on the plex server
    def get_shows(self) -> [Show]:
        """
        Get TV Shows from the PLEX server

        :return [Show]: List of TV Shows
        """
        all_entries = []
        try:
            all_entries = self.plex.library.search(titile="", libtype="show")
        except Exception as e:
            self.lib.write_error(f"Error getting shows {e=}")
        return all_entries

    # Get a plex show given the name
    def get_show(self, name: str) -> Show:
        """
        Get a tv show given the name

        :param str name: Name of the tv show to get
        :return Show: The TV Show
        """
        try:
            entry = self.plex.library.search(title=name, libtype='show')[0]
        except Exception as e:
            self.lib.write_error(f"Error getting show {e=}")
            entry = None
        return entry

    # Return the show on deck given the plex show
    @staticmethod
    def get_show_on_deck(show: Show) -> [Episode, None]:
        """
        Get the next unwatched episode for a given show

        :param Show show: Show from which to get the next unwatched episode
        :return [Episode, None]: Episode if found, None otherwise
        """
        try:
            entry = show.onDeck()
        except Exception as e:
            entry = None
        return entry

    # Get a specific plex episode given the show, season index, and episode index (read plex api doc)
    @staticmethod
    def get_episode_by_season_index(show: Show, season_index: int, episode_index: int) -> [Episode, None]:
        """
        Get and episode for a given show, given the season number, and episode number

        :param Show show: Show from which to get the episode
        :param int season_index: Season Number from which to get the episode
        :param int episode_index: Episode number
        :return [Episode, None]: Episode if found, None otherwise
        """
        try:
            e = show.episode(season=season_index, episode=episode_index)
            return e
        except Exception as e:
            return None

    # Get the plex episode after a given show for the given show
    def get_episode_after(self, show: Show, episode: Episode) -> [Episode, None]:
        """
        Return the episode after a given episode for a given show.

        :param Episode episode: Episode after this episode will be returned
        :param Show show: Show from which to get the episode
        :return [Episode, None]: Episode if found, None otherwise
        """
        season_number = episode.seasonNumber
        epi_number = episode.index
        next_episode = self.get_episode_by_season_index(show, season_number, epi_number + 1)
        if next_episode is None:
            next_episode = self.get_episode_by_season_index(show, season_number + 1, 1)
        return next_episode

    # Get all the episodes of a given show
    def get_episodes_for_show(self, show: Show) -> [Episode]:
        """
        Get all the episodes for a given show

        :param Show show: The show who's episodes are to be returned
        :return [Episode]: List of Episodes
        """
        shows = []
        try:
            shows = show.episodes()
        except Exception as e:
            self.lib.write_error(f"Error getting show episodes {e=}")
        return shows

    # Get duration of show (done by returning the duration of season 1 episode 1)
    def get_duration_of_show(self, show: Show) -> int:
        """
        Get the duration of a show. Done by getting the duration of season 1 episode 1

        :param Show show: Whose duration to get
        :return int: Duration of the show in milliseconds
        """
        return_value = 0
        try:
            episode: Episode = show.episode(season=1, episode=1)
            return_value: int = episode.duration
        except Exception as e:
            self.lib.write_error(f"Error getting show episodes {e=}")
        return return_value

    # TODO: This function can be optimized, and handle errors
    def get_shuffle_play_tv_queue(self, list: [str], include: bool = True, limit: int = 20) -> PlayQueue:
        """
        Shuffle function (the meat of this application)
        Get a list of episodes for a given show list. inclusive and exclusive shuffle is allowed

        :param [str] list: List of tv shows to shuffle
        :param bool include: Shuffle type.
        :param int limit: Max length of the queue that will be generated
        :return PlayQueue: Generated PLEX queue
        """
        episodes = []
        shows = self.get_shows()
        working_shows = []
        for show in shows:
            if include:
                if show.title in list:
                    working_shows.append(show)
            else:
                if show.title not in list:
                    working_shows.append(show)

        while len(episodes) != limit:
            n_episode = None
            while n_episode is None:
                if len(working_shows) == 0:
                    break
                working_show = random.choice(working_shows)
                working_show_epi_on_deck = self.get_show_on_deck(working_show)
                if working_show_epi_on_deck is not None:
                    if working_show_epi_on_deck not in episodes:
                        n_episode = working_show_epi_on_deck
                    else:
                        tmp_epi = working_show_epi_on_deck
                        while n_episode is None:
                            if tmp_epi not in episodes:
                                n_episode = tmp_epi
                            tmp_epi = self.get_episode_after(working_show, tmp_epi)
                            if tmp_epi is None:
                                working_shows.remove(working_show)
                                break
                else:
                    working_shows.remove(working_show)
                    break

            if len(working_shows) == 0:
                break
            episodes.append(n_episode)

        print(f"{episodes}")
        episodes = [i for i in episodes if i]

        queue = PlayQueue.create(self.plex, episodes)
        self.play_queue = queue
        return queue

    # Play given media on the client
    def client_play_media(self, media: [Movie, Episode, PlayQueue]) -> bool:
        """
        Play media on a connected client

        :param [Movie, Episode, PlayQueue] media: Media to be played on the client
        :return bool: Play status
        """
        try:
            self.client.playMedia(media)
            return True
        except Exception as e:
            self.lib.write_error(f"Error playing media on client {e=}")
            return False

    # Get a list of clients
    def get_clients(self) -> [PlexClient]:
        """
        Get all clients connected to the PLEX server

        :return [PlexClient]: List of PLEX clients
        """
        try:
            return self.plex.clients()
        except Exception as e:
            self.lib.write_error(f"Error getting server clients {e=}")

    # Get a client given the name
    def get_client(self, name: str) -> [PlexClient, None]:
        """
        Get a PLEX client given a client name

        :param str name: Name of the PLEX client to get
        :return [PlexClient, None]: PlexClient if one if found, None otherwise
        """
        try:
            for client in self.plex.clients():
                if client.title == name:
                    return client
        except Exception as e:
            self.lib.write_error(f"Error getting server client {e=}")
            return None

    # Set the client given the plex client
    def set_client(self, client: PlexClient) -> None:
        """
        Set a given PLEX client as the active client

        :param PlexClient client: Client to set as active
        :return:
        """
        self.client = client

    # Check client connection
    def is_connected_to_client(self) -> bool:
        """
        Check if there is a connection to the PLEX client

        :return bool: True if connected, False otherwise
        """
        if self.client is None:
            return False
        try:
            self.client.reload()
            return True
        except Exception as e:
            self.lib.write_error(f"Error lost client connection {e}")
            return False

    # Pause the media on the client
    def client_pause(self):
        """
        Pause the media playing on the active client

        :return:
        """
        try:
            self.client.pause()
        except Exception as e:
            self.lib.write_error(f"Error setting client to pause {e=}")

    # Play the media on the client
    def client_play(self):
        """
        Play the media on the active client

        :return:
        """
        try:
            self.client.play()
        except Exception as e:
            self.lib.write_error(f"Error setting client to play {e=}")

    # Check if the client media is playing
    def client_is_playing(self) -> bool:
        """
        Check is the active client is currently playing any media

        :return bool: True if something is playing, False otherwise
        """
        try:
            return self.client.isPlayingMedia(includePaused=True)
        except Exception as e:
            self.lib.write_error(f"Error getting client media playing status {e=}")
            return False

    # Get a list of servers for the plex account
    def get_servers(self) -> [MyPlexResource]:
        """
        Get a list of servers available on PLEX users account

        :return [MyPlexResource]: List of PLEX servers
        """
        r_list = []
        try:
            resources: [MyPlexResource] = self.my_account.resources()
            for resource in resources:
                if resource.product == "Plex Media Server":
                    r_list.append(resource)
        except Exception as e:
            self.lib.write_error(f"Error getting account resources {e=}")
        return r_list

    # Connect to a server given the name
    def connect_to_server(self, server: str) -> bool:
        """
        Connect to a PLEX server given the name

        :param str server: Name of the PLEX server
        :return bool: True if the connection is established, False otherwise
        """
        try:
            res = self.my_account.resource(server)
            self.plex: PlexServer = res.connect(ssl=True)
            self.connected_to_server = True
            return True
        except Exception as e:
            self.lib.write_error(f"Error connecting to server {e=}")
            return False

    # Check if the object is connected to a plex server
    def is_connected_to_server(self,) -> bool:
        """
        Check if there is a PLEX server connection

        :return bool: Status of the server connection
        """
        return self.connected_to_server

    def disconnect_from_server(self) -> bool:
        """
        Set the status of disconnect to true

        :return bool: Status of the server connection
        """
        self.connected_to_server = False
        return True

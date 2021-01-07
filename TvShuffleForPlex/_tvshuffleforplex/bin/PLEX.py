# Imports
import random
import os
from pathlib import Path

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
    def __init__(self, username: str = None, password: str = None, lib: LIB = None):
        self.message = None

        # Try to connect to the users plex account
        try:
            self.my_account: MyPlexAccount = MyPlexAccount(username=username, password=password)

        # Error loging in
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

    def __del__(self):
        pass

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return str(self.__dict__)

    # Get all the moves on the plex server
    def get_movies(self) -> [Movie]:
        all_entries = []
        try:
            all_entries = self.plex.library.search(titile="", libtype="movie")
        except Exception as e:
            self.lib.write_error(f"Error getting movies {e=}")
        return all_entries

    # Get a plex movie given the name
    def get_movie(self, name: str) -> [Movie]:
        try:
            entry = self.plex.library.search(title=name, libtype='movie')[0]
        except Exception as e:
            self.lib.write_error(f"Error getting movie {e=}")
            entry = None
        return entry

    # Get all the shows on the plex server
    def get_shows(self) -> [Show]:
        all_entries = []
        try:
            all_entries = self.plex.library.search(titile="", libtype="show")
        except Exception as e:
            self.lib.write_error(f"Error getting shows {e=}")
        return all_entries

    # Get a plex show given the name
    def get_show(self, name: str) -> [Show]:
        try:
            entry = self.plex.library.search(title=name, libtype='show')[0]
        except Exception as e:
            self.lib.write_error(f"Error getting show {e=}")
            entry = None
        return entry

    # Return the show on deck given the plex show
    @staticmethod
    def get_show_on_deck(show: Show) -> Episode:
        try:
            entry = show.onDeck()
        except Exception as e:
            entry = None
        return entry

    # Get a specific plex episode given the show, season index, and episode index (read plex api doc)
    @staticmethod
    def get_episode_by_season_index(show: Show, season_index: int, episode_index: int) -> [Episode, None]:
        try:
            e = show.episode(season=season_index, episode=episode_index)
            return e
        except Exception as e:
            return None

    # Get the plex episode after a given show for the given show
    def get_episode_after(self, show: Show, episode: Episode) -> Episode:
        season_number = episode.seasonNumber
        epi_number = episode.index
        next_episode = self.get_episode_by_season_index(show, season_number, epi_number + 1)
        if next_episode is None:
            next_episode = self.get_episode_by_season_index(show, season_number + 1, 1)
        return next_episode

    # Get a list of episodes for a given show list. inclusive and exclusive shuffle is allowed
    # TODO: This function can be optimized, and handle errors
    def get_shuffle_play_tv_queue(self, list: [str], include: bool = True, limit: int = 20) -> [Episode, PlayQueue]:
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
                                break

            episodes.append(n_episode)

        queue = PlayQueue.create(self.plex, episodes)
        return queue

    # Play given media on the client
    def client_play_media(self, media: [Movie, Episode, PlayQueue]):
        try:
            self.client.playMedia(media)
        except Exception as e:
            self.lib.write_error(f"Error playing media on client {e=}")

    # Get a list of clients
    def get_clients(self) -> [PlexClient]:
        try:
            return self.plex.clients()
        except Exception as e:
            self.lib.write_error(f"Error getting server clients {e=}")

    # Get a client given the name
    def get_client(self, name: str) -> [PlexClient, None]:
        try:
            for client in self.plex.clients():
                if client.title == name:
                    return client
        except Exception as e:
            self.lib.write_error(f"Error getting server client {e=}")
            return None

    # Set the client given the plex client
    def set_client(self, client: PlexClient) -> None:
        self.client = client

    # Pause the media on the client
    def client_pause(self):
        try:
            self.client.pause()
        except Exception as e:
            self.lib.write_error(f"Error setting client to pause {e=}")

    # Play the media on the client
    def client_play(self):
        try:
            self.client.play()
        except Exception as e:
            self.lib.write_error(f"Error setting client to play {e=}")

    # Check if the client media is playing
    def client_is_playing(self):
        try:
            self.client.isPlayingMedia(includePaused=True)
        except Exception as e:
            self.lib.write_error(f"Error getting client media playing status {e=}")

    # Get a list of servers for the plex account
    def get_servers(self) -> [MyPlexResource]:
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
        try:
            self.plex: PlexServer = self.my_account.resource(server).connect(ssl=True)
            return True
        except Exception as e:
            self.lib.write_error(f"Error connecting to server {e=}")
            return False

    # Check if the object is connected to a plex server
    def is_connected_to_server(self,) -> bool:
        try:
            self.plex.isLatest()
            return True
        except Exception as e:
            return False


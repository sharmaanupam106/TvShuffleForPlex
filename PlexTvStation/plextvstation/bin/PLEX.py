import requests
import random
from plexapi.myplex import MyPlexAccount, MyPlexResource
from plexapi.server import PlexServer
from plexapi.client import PlexClient
from plexapi.playqueue import PlayQueue
from plexapi.video import Show, Movie, Episode, Season
from plexapi.exceptions import Unauthorized, NotFound, BadRequest
import urllib3
import random

class Plex:
    def __init__(self, username: str = None, password: str = None):
        self.message = None
        try:
            self.my_account: MyPlexAccount = MyPlexAccount(username=username, password=password)
        except Unauthorized as e:
            self.message = "Incorrect username or password"
        except Exception as e:
            self.message = "Something went wrong"
        self.plex: PlexServer = None
        self.client: PlexClient = None

    def __del__(self):
        pass

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return str(self.__dict__)

    def get_movies(self) -> [Movie]:
        all_entries = self.plex.library.search(titile="", libtype="movie")
        return all_entries

    def get_movie(self, name: str) -> [Movie]:
        try:
            entry = self.plex.library.search(title=name, libtype='movie')[0]
        except Exception as e:
            entry = None
        return entry

    def get_shows(self) -> [Show]:
        all_entries = self.plex.library.search(titile="", libtype="show")
        return all_entries

    def get_show(self, name: str) -> [Show]:
        try:
            entry = self.plex.library.search(title=name, libtype='show')[0]
        except Exception as e:
            entry = None
        return entry

    @staticmethod
    def get_show_on_deck(show: Show) -> Episode:
        try:
            entry = show.onDeck()
        except Exception as e:
            entry = None
        return entry

    @staticmethod
    def get_episode_by_season_index(show: Show, season_index: int, episode_index: int) -> [Episode, None]:
        try:
            e = show.episode(season=season_index, episode=episode_index)
            return e
        except:
            return None

    def get_episode_after(self, show: Show, episode: Episode) -> Episode:
        season_number = episode.seasonNumber
        epi_number = episode.index
        next_episode = self.get_episode_by_season_index(show, season_number, epi_number + 1)
        if next_episode is None:
            next_episode = self.get_episode_by_season_index(show, season_number + 1, 1)
        return next_episode

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

    def client_play_media(self, media: [Movie, Episode, PlayQueue]):
        self.client.playMedia(media)

    def get_clients(self) -> [PlexClient]:
        return self.plex.clients()

    def get_client(self, name: str) -> PlexClient:
        for client in self.plex.clients():
            if client.title == name:
                return client

    def set_client(self, client: PlexClient) -> None:
        self.client = client

    def client_pause(self):
        self.client.pause()

    def client_play(self):
        self.client.play()

    def client_is_playing(self):
        self.client.isPlayingMedia(includePaused=True)

    def get_servers(self) -> [MyPlexResource]:
        r_list = []
        resources: [MyPlexResource] = self.my_account.resources()
        for resource in resources:
            if resource.product == "Plex Media Server":
                r_list.append(resource)
        return r_list

    def connect_to_server(self, server: str):
        self.plex: PlexServer = self.my_account.resource(server).connect(ssl=True)

    def is_connected_to_server(self,) -> bool:
        if self.plex is None:
            return False
        else:
            return True


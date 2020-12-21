import requests
import random
from plexapi.myplex import MyPlexAccount, MyPlexResource
from plexapi.server import PlexServer
from plexapi.client import PlexClient
from plexapi.playqueue import PlayQueue
from plexapi.video import Show, Movie, Episode, Season
from plexapi.exceptions import Unauthorized, NotFound, BadRequest
import urllib3


class Plex:
    def __init__(self, username: str = None, password: str = None):
        self.message = None
        try:
            self.my_account: MyPlexAccount = MyPlexAccount(username=username, password=password)
        except Unauthorized as e:
            self.message = "Incorrect username or password"
        except Exception as e:
            self.message = "Something went wrong"
        self.plex: PlexServer
        self.client: PlexClient

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

    def get_shuffle_play_queue(self, movie: bool = False, tv: bool = True, limit: int = 10) -> [Episode, Movie]:
        movies = []
        episodes = []
        if movie:
            movies = self.get_movies()
        if tv:
            shows = self.get_shows()
            for show in shows:
                on_deck = self.get_show_on_deck(show)
                if on_deck:
                    episodes.append(on_deck)
        new_list = episodes + movies
        random.shuffle(new_list)
        queue = PlayQueue.create(self.plex, new_list[:limit])
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
            if resources.product == "Plex Media Server":
                r_list.append(resource)
        return r_list

    def connect_to_server(self, server: MyPlexResource):
        self.plex: PlexServer = server.connect(ssl=True)




from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login, name="login"),
    path("logout", views.logout, name="logout"),
    path("connect_to_server", views.connect_to_server, name="connect_to_server"),
    path("get_server_list", views.get_server_list, name="get_server_list"),
    path("get_list_of_shows", views.get_list_of_shows, name="get_list_of_shows"),
    path("saved_lists", views.saved_lists, name="saved_lists"),
    path("update_selected_shows", views.update_selected_shows, name="update_selected_shows"),
    path("select_from_saved_list", views.select_from_saved_list, name="select_from_saved_list"),
    path("get_plex_queue", views.get_plex_queue, name="get_plex_queue"),
    path("plex_client", views.plex_client, name="plex_client"),
    path("shuffle", views.shuffle, name="shuffle"),
    path("remove_episode", views.remove_episode, name="remove_episode"),
]

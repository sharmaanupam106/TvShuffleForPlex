from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login, name="login"),
    path("logout", views.logout, name="logout"),
    path("shuffle", views.shuffled_view_and_client_select_push, name="shuffle"),
    path("push_client", views.client_push, name="push_client"),
    path("saved_list", views.saved_list, name="saved_list"),
    path("connect_to_server", views.connect_to_server, name="connect_to_server"),
    path("get_server_list", views.get_server_list, name="get_server_list"),
    path("get_saved_list", views.get_saved_list, name="get_saved_list"),

]

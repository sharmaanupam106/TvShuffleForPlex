from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login, name="login"),
    path("logout", views.logout, name="logout"),
    path("shuffle", views.shuffled_view_and_client_select_push, name="shuffle"),
    path("push_client", views.client_push, name="push_client")
]
import os
from pathlib import Path
from django.shortcuts import render, redirect, reverse
from django.http import HttpRequest
from .bin.LIB import LIB
from .bin.PLEX import Plex

lib = LIB(home=str(Path(os.path.dirname(os.path.realpath(__file__)))))
global plex_server
plex_server: Plex = None


def index(request):
    context = {}
    if request.session.get('message', None):
        message = request.session.get('message', None)
        lib.write_log(message)
        context['message'] = message
        request.session.pop("message")
    if not request.session.get("is_plex", None):
        request.session['message'] = 'Please log in'
        return redirect('login')
    elif plex_server is None:
        request.session.pop("is_plex")
        request.session['message'] = 'Please log in'
        return redirect('login')
    lib.write_log("Index call")
    servers = plex_server.get_servers()
    context['plex_servers'] = servers

    if request.session.get('plex_connected_server', None):
        plex_server_select = request.session.get('plex_connected_server', None)
    else:
        plex_server_select = request.GET.get("plex_server_select", None)

    if plex_server_select:
        plex_server.connect_to_server(plex_server_select)
        if plex_server.plex.friendlyName:
            context['plex_connected_server'] = plex_server.plex.friendlyName
            request.session['plex_connected_server'] = plex_server.plex.friendlyName
    print(context)
    return render(request, template_name="plextvstation/index.html", context=context)


def login(request):
    context = {}
    # Request for login
    if request.method == "POST":
        # Get messages from ession
        if request.session.get('message', None):
            message = request.session.get('message', None)
            lib.write_log(message)
            request.session.pop("message")

        # Get user entered username and pasword
        post_username = request.POST.get('username', None)
        post_password = request.POST.get('password', None)

        post_username = "drool.grewa0@gmail.com"
        post_password = 'fe#5eU!k&2bY'

        # Attempt a login
        global plex_server
        plex_server = Plex(username=post_username, password=post_password)
        # There was an error with plex login
        if plex_server.message:
            request.session['message'] = plex_server.message
            lib.write_log(plex_server.message)
            request.session['is_plex'] = False
            return redirect("login")
        # Plex login was successful
        else:
            request.session['is_plex'] = True
            request.session['username'] = post_username
            return redirect("index")
    else:
        if request.session.get('message', None):
            message = request.session.get('message', None)
            lib.write_log(message)
            context['message'] = message
            request.session.pop("message")
        if request.session.get("is_plex", None):
            request.session['message'] = 'Already logged in'
            return redirect('index')
        lib.write_log("login call")
        return render(request, template_name="plextvstation/login.html", context=context)


def logout(request):
    if request.session.get('message', None):
        message = request.session.get('message', None)
        lib.write_log(message)
        request.session.pop("message")
    request.session.clear()
    global plex_server
    plex_server = None
    request.session['message'] = 'Log out successful'
    return redirect("login")


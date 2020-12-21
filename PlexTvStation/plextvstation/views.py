import os
from pathlib import Path
from django.shortcuts import render, redirect, reverse
from .bin.LIB import LIB
from .bin.PLEX import Plex

lib = LIB(home=str(Path(os.path.dirname(os.path.realpath(__file__)))))
global plex_server


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
    lib.write_log("Index call")
    global plex_server
    return render(request, template_name="plextvstation/index.html", context=context)


def login(request):
    context = {}
    if request.method == "POST":
        if request.session.get('message', None):
            message = request.session.get('message', None)
            lib.write_log(message)
            request.session.pop("message")

        post_username = request.POST.get('username', None)
        post_password = request.POST.get('password', None)

        global plex_server
        plex_server = Plex(username=post_username, password=post_password)

        if plex_server.message:
            request.session['message'] = plex_server.message
            lib.write_log(plex_server.message)
            request.session['is_plex'] = False
            return redirect("login")
        else:
            request.session['is_plex'] = True
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
    request.session.pop("is_plex")
    global plex_server
    plex_server = None
    request.session['message'] = 'Log out successful'
    return redirect("login")


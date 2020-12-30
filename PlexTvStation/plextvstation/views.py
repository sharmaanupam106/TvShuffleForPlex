import os
from pathlib import Path
from django.shortcuts import render, redirect, reverse
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .bin.LIB import LIB
from .bin.PLEX import Plex

lib = LIB(home=str(Path(os.path.dirname(os.path.realpath(__file__)))))
global plex_server
plex_server: Plex = None
global play_queue


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

    if request.session.get('selected_shows', None):
        selected_shows = request.session.get('selected_shows', None)
        working_show_list = []
        for item in selected_shows:
            working_show_list.append(plex_server.get_show(item))
        context['selected_shows'] = working_show_list

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
            context['tv_shows'] = plex_server.get_shows()
    return render(request, template_name="plextvstation/index.html", context=context)


@csrf_exempt
def shuffled_view_and_client_select_push(request):
    context = {}
    if not request.session.get("is_plex", None):
        request.session['message'] = 'Please log in'
        return redirect('login')
    elif plex_server is None:
        request.session.pop("is_plex")
        request.session['message'] = 'Please log in'
        return redirect('login')

    if request.method == "POST":
        post_data = dict(request.POST)
        print(post_data)
        list = post_data.get("list[]")
        request.session['selected_shows'] = list
        if len(post_data.get("shuffle_style")) >= 1:
            if post_data.get("shuffle_style")[0] == "exclusive":
                shuffle_style = False
            else:
                shuffle_style = True
        else:
            shuffle_style= True
        working_show_list = []
        for item in list:
            show = plex_server.get_show(item)
            working_show_list.append(show)
        context['selected_shows'] = working_show_list
        context['shuffle_style'] = shuffle_style
        shuffled_episodes = plex_server.get_shuffle_play_tv_queue(list, include=shuffle_style)
        context['shuffled_episodes'] = shuffled_episodes
        global play_queue
        play_queue = shuffled_episodes
        clients = plex_server.get_clients()
        context['plex_clients'] = clients
        print(context)
        return render(request, template_name="plextvstation/shuffled_view_and_client_select_push.html", context=context)

    if request.method == "GET":
        request.session['message'] = 'Method Not Allowed'
        return redirect('index')


def client_push(request):
    if not request.session.get("is_plex", None):
        request.session['message'] = 'Please log in'
        return redirect('login')
    elif plex_server is None:
        request.session.pop("is_plex")
        request.session['message'] = 'Please log in'
        return redirect('login')
    if request.method == "POST":
        request.session['message'] = 'Method Not Allowed'
        return redirect('index')
    else:
        if request.session.get('client_select', None):
            client_select = request.session.get('client_select', None)
        else:
            client_select = request.GET.get("client_select", None)
        if client_select is not None:
            client = plex_server.get_client(client_select)
            plex_server.set_client(client)
            global play_queue
            plex_server.client_play_media(play_queue)
            request.session['message'] = 'Queue Sent'
            return redirect('index')
        else:
            request.session['message'] = 'No Client'
            return redirect('index')


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


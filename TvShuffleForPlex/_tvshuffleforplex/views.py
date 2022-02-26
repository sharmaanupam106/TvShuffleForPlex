# Imports
import os
from pathlib import Path

from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render, redirect, reverse
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import SavedLists

# App imports
from .bin.LIB import LIB
from .bin.PLEX import Plex

# Create a lib instance (used for logging, and config file reading)
lib = LIB(home=str(Path(os.path.dirname(os.path.realpath(__file__)))))

# Create a plex_server instance (not logged in)
global plex_server
plex_server: Plex = Plex(lib=lib)


@csrf_exempt
def index(request):
    # Rotate the log files
    # out_log_file = os.path.join(lib.LOGS_PATH, lib.OUT_LOG)
    # error_log_file = os.path.join(lib.LOGS_PATH, lib.ERR_LOG)
    # lib.file_rotation(out_log_file)
    # lib.file_rotation(error_log_file)

    context = {}
    lib.write_log("index")

    # Display any messages that might be passed to the session
    if request.session.get('message', None):
        message = request.session.get('message', None)
        lib.write_log(message)
        context['message'] = message
        request.session.pop("message")

    login_status = check_login_status(request)
    if login_status != True:  # this is an explicit test for True since another return value can be a render
        try:
            request.session.pop('plex_connected_server')
        except KeyError:
            pass
        return login_status

    context['username'] = plex_server.my_account.email

    if plex_server.is_connected_to_server():
        # Get user saved lists of shows
        if plex_server.plex.friendlyName:
            request.session['plex_connected_server'] = plex_server.plex.friendlyName

    lib.write_log(f"{context=}")
    return render(request, template_name="_tvshuffleforplex/index.html", context=context)


def login(request):
    global plex_server
    context = {}
    lib.write_log("login")

    # Request for login
    if request.method == "POST":
        # Get messages from session
        if request.session.get('message', None):
            message = request.session.get('message', None)
            lib.write_log(message)
            request.session.pop("message")

        # Get user entered username and password
        post_username = request.POST.get('username', None)
        post_password = request.POST.get('password', None)

        post_username = "drool.grewa0@gmail.com"
        post_password = "fe#5eU!k&2bY"

        plex_server = Plex(username=post_username, password=post_password, lib=lib)

        # There was an error with plex login
        if not plex_server.logged_in:
            request.session['message'] = plex_server.message
            lib.write_log(plex_server.message)
            request.session['logged_in'] = False
            request.method = "GET"
            response = login(request)
            response.status_code = 307
            return response

        # Plex login was successful
        else:
            request.session['username'] = post_username
            request.session['logged_in'] = True
            response = index(request)
            response.status_code = 307
            return response

    # Check if the user is logged in
    if request.method == "GET":

        # Get messages from session
        if request.session.get('message', None):
            message = request.session.get('message', None)
            lib.write_log(message)
            context['message'] = message
            request.session.pop("message")

        # Check if a plex session already exists (user is already logged in)
        if plex_server.logged_in:
            request.session['message'] = 'Already logged in'
            response = index(request)
            response.status_code = 307
            return response
        lib.write_log(f"{context=}")
        return render(request, template_name="_tvshuffleforplex/login.html", context=context)


def logout(request):
    lib.write_log("logout")

    # Get messages from session
    if request.session.get('message', None):
        message = request.session.get('message', None)
        lib.write_log(message)
        request.session.pop("message")

    # Clear the session
    request.session.clear()
    # Remove the global plex object
    global plex_server
    plex_server = Plex(lib=lib)
    request.session['message'] = 'Log out successful'
    lib.write_log('Log out successful')
    request.method = "GET"
    response = login(request)
    response.status_code = 307
    return response


def connect_to_server(request):
    lib.write_log("connect_to_server")

    login_status = check_login_status(request)
    if not login_status:
        return login_status

    if request.method == "GET":
        plex_server_select = request.GET.get("plex_server_select", None)
        # Connect to a server
        if plex_server_select:
            if plex_server_select != "None":
                lib.write_log("Connecting to server -- New Connection")
                if not plex_server.connect_to_server(plex_server_select):
                    request.session.pop('plex_connected_server', None)
                    message = f'Unable to connect to server {plex_server_select}'
                    request.session['message'] = message
                lib.write_log("Connecting to server -- New Connection -- Done")
            else:
                disconnect_server(request)
        lib.write_log("connect_to_server -- Done")

        response = index(request)
        response.status_code = 307
        return response
    # POST method for this URL is not allowed
    if request.method == "POST":
        request.session['message'] = 'Method Not Allowed'
        lib.write_log("connect_to_server -- Done")
        response = index(request)
        response.status_code = 307
        return response


def disconnect_server(request):
    lib.write_log("disconnect_server")
    server = request.session.get('plex_connected_server', None)
    lib.write_log(f'Disconnecting from server {server}')
    request.session.pop('plex_connected_server', None)
    plex_server.disconnect_from_server()
    message = f'Disconnected from server {server}'
    request.session['message'] = message
    lib.write_log("disconnect_server -- Done")


def check_login_status(request):
    # Check if a plex session already exists (user is already logged in)
    if not plex_server.logged_in:
        request.session['logged_in'] = False
        request.session['message'] = 'Please log in'
        lib.write_log("Invalid login")
        response = login(request)
        response.status_code = 307
        return response
    else:
        request.session['logged_in'] = True
        return True


def get_server_list(request):
    if request.method == "GET":
        context = {
            'plex_servers': plex_server.get_servers()
        }
        return render(request, template_name='_tvshuffleforplex/server_ul.html', context=context)


def get_list_of_shows(request):
    if request.method == "GET":
        context = {
            'shows': plex_server.get_shows()
        }
        return render(request, template_name='_tvshuffleforplex/tv_show_selection_list.html', context=context)


@csrf_exempt
def saved_lists(request):
    if request.method == "GET":
        context = {
            'saved_list': SavedLists.objects.filter(
                user=plex_server.my_account.username,
                server=plex_server.plex.friendlyName
            ).all()
        }
        return render(request, template_name='_tvshuffleforplex/save_list_ul.html', context=context)
    if request.method == "POST":
        post_data = dict(request.POST)
        selected_shows = post_data.get('selected_shows[]', None)
        list_name = post_data.get('list_name', None)[0]
        if list_name == "None":
            data = {
                "None": True
            }
            return JsonResponse(data)
        user = plex_server.my_account.username
        server = plex_server.plex.friendlyName
        try:
            obj = SavedLists.objects.get(
                user=user,
                server=server,
                name=list_name
            )
            obj.set_list(selected_shows)
            obj.save()
        except ObjectDoesNotExist:
            obj = SavedLists(
                user=user,
                server=server,
                name=list_name
            )
            obj.set_list(selected_shows)
            obj.save()
        plex_server.selected_shows = selected_shows
        data = {
            "message": f"List {list_name} Saved"
        }
        return JsonResponse(data)


@csrf_exempt
def update_selected_shows(request):
    if request.method == "GET":
        data = {
            'selected_shows': plex_server.selected_shows if len(plex_server.selected_shows) >= 1 else []
        }
        return JsonResponse(data)

    if request.method == "POST":
        post_data = dict(request.POST)
        selected_shows = post_data.get('selected_shows[]', None)
        plex_server.selected_shows = selected_shows
        return JsonResponse({})


def select_from_saved_list(request):
    if request.method == "GET":
        get_data = dict(request.GET)
        list_name = get_data.get('list_name')[0]

        if list_name == "None":
            plex_server.selected_shows = []
            return JsonResponse({})

        user = plex_server.my_account.username
        server = plex_server.plex.friendlyName
        saved_list = SavedLists.objects.get(
            user=user,
            server=server,
            name=list_name
        )
        plex_server.selected_shows = saved_list.get_list()
        return JsonResponse({})


def get_plex_queue(request):
    if request.method == "GET":
        return_queue = plex_server.play_queue
        if return_queue:
            context = {
                'play_queue': return_queue
            }
            return render(request, template_name="_tvshuffleforplex/shuffled_list_ul.html", context=context)
        else:
            context = {
                'no_play_queue': True
            }
            return render(request, template_name="_tvshuffleforplex/shuffled_list_ul.html", context=context)


@csrf_exempt
def plex_client(request):
    if request.method == "GET":
        plex_clients = plex_server.get_clients()
        context = {
            'plex_clients': plex_clients
        }
        return render(request, template_name="_tvshuffleforplex/client_ul.html", context=context)

    if request.method == "POST":
        post_data = dict(request.POST)
        client_name = post_data.get('client', [None])[0]
        if client_name:
            print(f"{client_name=}")
            client = plex_server.get_client(client_name)
            print(f"{client=}")
            plex_server.set_client(client)
            if plex_server.client_play_media(plex_server.play_queue):
                return JsonResponse({'message': f"Queue sent to {client_name}"})
            else:
                return JsonResponse({'message': f"Unable to send queue to {client_name}"})
        else:
            return JsonResponse({'message': f"No such client {client_name}"})


def shuffle(request):
    if request.method == "GET":
        get_data = dict(request.GET)
        if plex_server.selected_shows:
            limit = get_data.get('limit', [10])[0]
            play_queue = plex_server.get_shuffle_play_tv_queue(list=plex_server.selected_shows, limit=int(limit))
            plex_server.play_queue = play_queue
            return JsonResponse({'shuffle': True})
        else:
            return JsonResponse({'shuffle': False, 'message': 'No shows selected'})


def remove_episode(request):
    if request.method == "GET":
        get_data = dict(request.GET)
        if plex_server.play_queue:
            rating_key = get_data.get('ratingKey', [None])[0]
            if rating_key:
                plex_server.play_queue = [episode for episode in plex_server.play_queue if episode.ratingKey != int(rating_key)]
                return JsonResponse({'remove': True})
            else:
                return JsonResponse({'remove': False, 'message': 'Episode not found in queue'})
        else:
            return JsonResponse({'remove': False, 'message': 'There is no queue'})


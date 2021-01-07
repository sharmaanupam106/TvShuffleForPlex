# Imports
import os
from pathlib import Path
from django.shortcuts import render, redirect, reverse
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import SavedLists

# App imports
from .bin.LIB import LIB
from .bin.PLEX import Plex

# Create a lib instance (used for logging, and config file reading)
lib = LIB(home=str(Path(os.path.dirname(os.path.realpath(__file__)))))
global plex_server
plex_server: Plex = None
global play_queue


# Index page
@csrf_exempt
def index(request):

    # Rotate the log files
    out_log_file = os.path.join(lib.LOG, lib.OUT_LOG)
    error_log_file = os.path.join(lib.LOG, lib.ERR_LOG)
    lib.file_rotation(out_log_file)
    lib.file_rotation(error_log_file)

    context = {}
    lib.write_log("index")

    # Display any messages that might be passed to the session
    if request.session.get('message', None):
        message = request.session.get('message', None)
        lib.write_log(message)
        context['message'] = message
        request.session.pop("message")

    # Check if a plex session already exists (user is already logged in)
    if not request.session.get("is_plex", None):
        request.session['message'] = 'Please log in'
        lib.write_log("Invalid login")
        response = login(request)
        response.status_code = 307
        return response
    elif plex_server is None:
        request.session.pop("is_plex")
        request.session['message'] = 'Please log in'
        lib.write_log("Invalid login")
        response = login(request)
        response.status_code = 307
        return response

    # Get a list of plex servers available to the user
    lib.write_log("Getting Servers")
    servers = plex_server.get_servers()
    lib.write_log("Getting Servers -- Done")
    context['plex_servers'] = servers

    if plex_server.is_connected_to_server():
        # List of user selected shows given though the session
        if request.session.get('selected_shows', None):
            selected_shows = request.session.get('selected_shows', None)
            working_show_list = []
            lib.write_log("Getting Show by items")
            for item in selected_shows:
                working_show_list.append(plex_server.get_show(item))
            lib.write_log("Getting Show by items -- Done")
            context['selected_shows'] = working_show_list

        # Get user saved lists of shows
        lib.write_log("Getting saved list")
        saved_list = SavedLists.objects.filter(user=request.session['username'])
        context['saved_list'] = saved_list
        lib.write_log("Getting saved list -- Done")
        if plex_server.plex.friendlyName:
            context['plex_connected_server'] = plex_server.plex.friendlyName
            request.session['plex_connected_server'] = plex_server.plex.friendlyName
            lib.write_log("Getting Shows")
            context['tv_shows'] = plex_server.get_shows()
            lib.write_log("Getting Shows -- Done")

    lib.write_log(f"{context=}")
    return render(request, template_name="_tvshuffleforplex/index.html", context=context)


# Generate a shuffled episode list from selected shows, and allow the user to push the list to an available plex client
@csrf_exempt
def shuffled_view_and_client_select_push(request):
    context = {}
    lib.write_log("shuffled_view_and_client_select_push")

    # Validate server connection
    if not plex_server.is_connected_to_server():
        lib.write_log(f"Connection to {plex_server.plex.friendlyName} was lost.")
        disconnect_server(request)
        response = index(request)
        response.status_code = 307
        return response

    # Check if a plex session already exists (user is already logged in)
    if not request.session.get("is_plex", None):
        request.session['message'] = 'Please log in'
        lib.write_log("Invalid login")
        response = login(request)
        response.status_code = 307
        return response
    elif plex_server is None:
        request.session.pop("is_plex")
        request.session['message'] = 'Please log in'
        lib.write_log("Invalid login")
        response = login(request)
        response.status_code = 307
        return response

    # Make sure the call method is post
    if request.method == "POST":

        # Convert the post data into a dict
        post_data = dict(request.POST)
        lib.write_log(f"{post_data=}")

        # Get the list of user selected shows
        list = post_data.get("list[]")

        # Get the user selected shuffle style
        request.session['selected_shows'] = list
        if len(post_data.get("shuffle_style")) >= 1:
            if post_data.get("shuffle_style")[0] == "exclusive":
                shuffle_style = False
            else:
                shuffle_style = True
        else:
            shuffle_style = True

        # Get the user selected max episodes
        max_length = post_data.get("max_episode_count", None)
        if max_length is None:
            max_length = 20
        elif len(max_length) == 1:
            if max_length[0] != '':
                max_length = int(max_length[0])
            else:
                max_length = 20
        else:
            max_length = 20

        # Get all the plex show objects for the selected shows
        working_show_list = []
        lib.write_log("Getting Shows by item")
        for item in list:
            show = plex_server.get_show(item)
            working_show_list.append(show)
        lib.write_log("Getting Shows by item -- Done")
        context['selected_shows'] = working_show_list
        context['shuffle_style'] = shuffle_style

        # Generate a shuffled list of episodes
        lib.write_log("Getting Shuffled list")
        shuffled_episodes = plex_server.get_shuffle_play_tv_queue(list, include=shuffle_style, limit=max_length)
        lib.write_log("Getting Shuffled list -- Done")
        context['shuffled_episodes'] = shuffled_episodes
        global play_queue
        play_queue = shuffled_episodes

        # Get all available clients
        lib.write_log("Getting Clients")
        clients = plex_server.get_clients()
        lib.write_log("Getting Clients -- Done")
        context['plex_clients'] = clients
        lib.write_log(f"{context=}")
        return render(request, template_name="_tvshuffleforplex/shuffled_view_and_client_select_push.html", context=context)

    # Get method for this URL is not allowed
    if request.method == "GET":
        request.session['message'] = 'Method Not Allowed'
        response = index(request)
        response.status_code = 307
        return response


# Manage the user saves shows in list
@csrf_exempt
def saved_list(request):
    lib.write_log("select_list")

    # Check if a plex session already exists (user is already logged in)
    if not request.session.get("is_plex", None):
        request.session['message'] = 'Please log in'
        lib.write_log("Invalid login")
        response = login(request)
        response.status_code = 307
        return response
    elif plex_server is None:
        request.session.pop("is_plex")
        request.session['message'] = 'Please log in'
        lib.write_log("Invalid login")
        response = login(request)
        response.status_code = 307
        return response

    # Get the lists of saves shows for the user
    if request.method == "GET":
        lib.write_log(f"{request.GET=}")
        # Get the name of the list to retrieve
        name = request.GET.get("saved_list_name", None)
        if name is None:
            lib.write_log('Missing name');
            request.session['message'] = 'Missing name'
            response = index(request)
            response.status_code = 307
            return response
        # Get the shows list given the name for the given user
        obj = SavedLists.objects.get(name=name, user=request.session['username'])
        request.session['selected_shows'] = obj.get_list()
        response = index(request)
        response.status_code = 307
        return response

    # POST a list to be saved.
    if request.method == "POST":

        # Convert the post data into a dict
        post_data = dict(request.POST)
        lib.write_log(f"{post_data=}")

        # Get the list of shows from post data
        list = post_data.get("list[]")

        # Get the given name of the list from post data
        name = post_data.get("save_name")[0]
        if (name == "") or (len(list) == 0):
            lib.write_log('Name or List is empty')
            request.session['message'] = 'Name or List is empty'
            response = index(request)
            response.status_code = 307
            return response

        # Search the DB for a pre-existing list
        lib.write_log('Getting Objects')
        try:
            obj = SavedLists.objects.get(name=name, user=request.session['username'])
        except Exception as e:

            # Create a new list
            lib.write_log('Object not found -- creating new')
            obj = SavedLists(name=name, user=request.session['username'])

        # Update the existing list with the new selection
        lib.write_log('Updating object')
        obj.set_list(list)
        obj.save()

        # Set the new selected shows
        request.session['selected_shows'] = list
        response = index(request)
        response.status_code = 307
        return response


# Push a plex queue to the user selected client
def client_push(request):
    lib.write_log("client_push")

    # Validate server connection
    if not plex_server.is_connected_to_server():
        lib.write_log(f"Connection to {plex_server.plex.friendlyName} was lost.")
        disconnect_server(request)
        response = index(request)
        response.status_code = 307
        return response

    # TODO: Validate Client connection

    # Check if a plex session already exists (user is already logged in)
    if not request.session.get("is_plex", None):
        request.session['message'] = 'Please log in'
        lib.write_log("Invalid login")
        response = login(request)
        response.status_code = 307
        return response
    elif plex_server is None:
        request.session.pop("is_plex")
        request.session['message'] = 'Please log in'
        lib.write_log("Invalid login")
        response = login(request)
        response.status_code = 307
        return response

    # POST method for this URL is not allowed
    if request.method == "POST":
        request.session['message'] = 'Method Not Allowed'
        response = index(request)
        response.status_code = 307
        return response

    # Get the selected client and push queue to it
    if request.method == "GET":

        # Get the selected client from the session
        if request.session.get('client_select', None):
            client_select = request.session.get('client_select', None)
        else:
            client_select = request.GET.get("client_select", None)

        # There is a client selected
        if client_select is not None:

            # Set the client in the plex object
            lib.write_log("Getting and setting client")
            client = plex_server.get_client(client_select)
            plex_server.set_client(client)
            lib.write_log("Getting and setting client -- Done")

            # Push the generated queue to the client
            global play_queue
            lib.write_log("Queue sending")
            plex_server.client_play_media(play_queue)
            request.session['message'] = 'Queue Sent'
            lib.write_log("Queue sending -- Done")
            response = index(request)
            response.status_code = 307
            return response
        else:

            # There was no client selected
            request.session['message'] = 'No Client'
            lib.write_log("No Client")
            response = index(request)
            response.status_code = 307
            return response


# Log in to the app using your plex account
def login(request):
    context = {}
    lib.write_log("login")

    # Request for login
    if request.method == "POST":

        # Get messages from session
        if request.session.get('message', None):
            message = request.session.get('message', None)
            lib.write_log(message)
            request.session.pop("message")

        # Get user entered username and pasword
        post_username = request.POST.get('username', None)
        post_password = request.POST.get('password', None)

        # Attempt a login
        global plex_server
        plex_server = Plex(username=post_username, password=post_password, lib=lib)

        # There was an error with plex login
        if plex_server.message:
            request.session['message'] = plex_server.message
            lib.write_log(plex_server.message)
            request.session['is_plex'] = False
            response = login(request)
            response.status_code = 307
            return response

        # Plex login was successful
        else:
            request.session['is_plex'] = True
            request.session['username'] = post_username
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
        if request.session.get("is_plex", None):
            request.session['message'] = 'Already logged in'
            response = index(request)
            response.status_code = 307
            return response
        lib.write_log(f"{context=}")
        return render(request, template_name="_tvshuffleforplex/login.html", context=context)


# Log out of the app
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
    plex_server = None
    request.session['message'] = 'Log out successful'
    lib.write_log('Log out successful')
    response = login(request)
    response.status_code = 307
    return response


def connect_to_server(request):
    lib.write_log("connect_to_server")

    # Check if a plex session already exists (user is already logged in)
    if not request.session.get("is_plex", None):
        request.session['message'] = 'Please log in'
        lib.write_log("Invalid login")
        response = login(request)
        response.status_code = 307
        return response
    elif plex_server is None:
        request.session.pop("is_plex")
        request.session['message'] = 'Please log in'
        lib.write_log("Invalid login")
        response = login(request)
        response.status_code = 307
        return response

    if request.method == "GET":
        if plex_server.is_connected_to_server():
            disconnect_server(request)
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
    plex_server.plex = None
    message = f'Disconnected from server {server}'
    request.session['message'] = message
    lib.write_log("disconnect_server -- Done")

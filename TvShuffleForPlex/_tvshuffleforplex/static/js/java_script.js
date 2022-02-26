waiting = '<div class="container waiting pt-5 pb-10 text-center"><div class="spinner-border" role="status"><h2 class="pl-2 text-center"></h2></div></div>'

$(document).ready(function(){
    if (document.body.contains(document.getElementById('tv_shows_listing'))){
        get_list_of_shows()
        get_plex_queue()
    }
});

$('.client-select-list-button').click(function (e){
    m_html = "<li class='dropdown-item'><a href='#'>Loading...</a></li>"
    document.getElementById("client-selection-list").innerHTML = m_html
    get_plex_clients()
})

$('.server-select-button').click(function (e){
    m_html = "<li class='dropdown-item'><a href='#'>Loading...</a></li>"
    document.getElementById("server-selection-list").innerHTML = m_html
    get_servers_list()
})

$('.saved-select-list-button').click(function (e){
    m_html  = "<li class='dropdown-item'><a href='#'>Loading...</a></li>"
    document.getElementById("server-selection-list").innerHTML = m_html
    get_saved_lists()
})

function hide_messages(){
    document.getElementById('messages').hidden = true
}

function show_messages(msg){
    if (typeof msg === 'undefined') {
        document.getElementById('messages').hidden = true
    }
    else{
        var mHTML = "<a href='#' onclick='hide_messages()' class='remove-notification'>X</a>" + msg
        document.getElementById('messages').innerHTML = mHTML
        document.getElementById('messages').hidden = false
    }

}

function get_servers_list(){
     $.ajax({
        type: "GET",
        url: "/get_server_list",
        complete: function(return_data){
            let m_html = return_data.responseText
            let response_code = return_data.status
            if (response_code != 200) {
                document.open()
                document.write(m_html)
                document.close()
            }
            else{
                document.getElementById("server-selection-list").innerHTML = m_html
            }
        }
    });
}

function loading_function(div_id){
    document.getElementById(div_id).innerHTML = waiting
}

function get_list_of_shows(){
    document.getElementById("show_list").innerHTML = waiting
    $.ajax({
        type: "GET",
        url: "/get_list_of_shows",
        complete: function(return_data){
            let m_html = return_data.responseText
            let response_code = return_data.status
            if (response_code != 200) {
                show_messages("Unable to get shows")
            }
            else{
                document.getElementById("show_list").innerHTML = m_html
                update_selected_shows()
                update_count()
            }
        }
    });
}

function get_saved_lists(){
    $.ajax({
        type: "GET",
        url: "/saved_lists",
        complete: function(return_data){
            let m_html = return_data.responseText
            let response_code = return_data.status
            if (response_code != 200) {
                document.open()
                document.write(m_html)
                document.close()
            }
            else{
                document.getElementById("saved-list-selection").innerHTML = m_html
            }
        }
    });
}

function de_select_all_selections(){
    var show_listing = get_show_listing()
    for (const [key, value] of Object.entries(show_listing)){
        var element = document.getElementById(value)
        element.classList.remove('selected_show')
    }
    update_count()
}

function toggle_selection(id){
    var element = document.getElementById(id)
    if (element.classList.contains('selected_show')){
        element.classList.remove('selected_show')
    }
    else{
        element.classList.add('selected_show')
    }
    update_count()
    tell_selected_shows_updated()
    return false
}

function update_count(){
    var elms = document.getElementsByClassName('selected_show')
    var count = elms.length
    document.getElementById('selected-count').innerHTML = count
}

function save_selected_shows(){
    var selected_shows = get_selected_shows()
    var list_name = document.getElementById('save-select-name-input').value
    if (list_name.length > 0){
        let data = {}
        data['list_name'] = list_name
        data['selected_shows'] = selected_shows
        $.ajax({
            type: "POST",
            url: "/saved_lists",
            data: data,
            success: function(data){
                if (data.None === true){

                }
                else{
                show_messages(data.message)
                }
            },
            error: function(d){
                show_messages("Unable to save " + list_name)
            }
        })
    }
    else{
        show_messages("List name required")
    }
}

function get_selected_shows(){
    var elms = document.getElementsByClassName('selected_show')
    var selected_shows = []
    for (var i = 0; i < elms.length; ++i){
        var elm = elms[i]
        selected_shows.push(elm.textContent.trim())
    }
    return selected_shows
}

function get_show_listing(){
    var elms = document.getElementsByClassName('show_list_item')
    var show_listing = {}
    for (var i = 0; i < elms.length; ++i){
        var elm = elms[i]
        show_listing[elm.textContent.trim()] = elm.id
    }
    return show_listing
}

function update_selected_shows(){
    $.ajax({
        type: "GET",
        url: "/update_selected_shows",
        complete: function(return_data){
            let data = return_data.responseJSON;
            let response_code = return_data.status
            if (response_code == 200) {
                var show_listing = get_show_listing()
                var show_listing_keys = Object.keys(show_listing)
                data.selected_shows.forEach(function(show){
                    if(show_listing_keys.includes(show)){
                        toggle_selection(show_listing[show])
                    }
                })
            }
            else{
                show_messages("Unable to pre-select shows")
            }
        }
    });
}

function tell_selected_shows_updated(){
    var data = {
        "selected_shows": get_selected_shows()
    }
    $.ajax({
            type: "POST",
            url: "/update_selected_shows",
            data: data,
            success: function(data){

            },
            error: function(d){
                console.log("Unable to tell select change: " + d)
            }
        })
}

function select_from_saved_list(list_name){
    var data = {
        "list_name": list_name
    }
     $.ajax({
        type: "GET",
        url: "/select_from_saved_list",
        data: data,
        complete: function(return_data){
            let response_code = return_data.status
            if (response_code == 200) {
                update_selected_shows()
                de_select_all_selections()
                document.getElementById('save-select-name-input').value = list_name
            }
            else{
                show_messages("Unable to load saved selections from " + list_name)
            }
        }
    });
}

function toggle_show_listing(){
    var state = document.getElementById('collapse_show_listing').innerHTML
    if (state === "+"){
        document.getElementById('collapse_show_listing').innerHTML = "-"
        document.getElementById('tv_shows_listing').hidden = true
    }
    else{
        document.getElementById('collapse_show_listing').innerHTML = "+"
        document.getElementById('tv_shows_listing').hidden = false
    }
}

function toggle_shuffled_listing(){
    var state = document.getElementById('collapse_shuffled_listing').innerHTML
    if (state === "+"){
        document.getElementById('collapse_shuffled_listing').innerHTML = "-"
        document.getElementById('episodes_listing').hidden = true
    }
    else{
        document.getElementById('collapse_shuffled_listing').innerHTML = "+"
        document.getElementById('episodes_listing').hidden = false
    }
}

function update_shuffled_view_title(){
    var title = document.getElementById('shuffled_view_title')
    var episodes = document.getElementsByClassName('episode_in_queue')
    var count = 0
    for (var i = 0; i < episodes.length; ++i){
        var episode = episodes[i]
        if (episode.hidden === false){
            ++count
        }
    }
    title.innerHTML = "Plex Queue (" + count + ")"
    return
}

function get_plex_queue(){
    document.getElementById("episode_list").innerHTML = waiting
    $.ajax({
        type: "GET",
        url: "/get_plex_queue",
        complete: function(return_data){
            let m_html = return_data.responseText
            let response_code = return_data.status
            if (response_code != 200) {
                show_messages("Unable to get plex queue from server")
                document.getElementById("episode_list").innerHTML = "Unable to get plex queue from server"
            }
            else{
                document.getElementById("episode_list").innerHTML = m_html
                update_shuffled_view_title()
            }
        }
    });
}

function get_plex_clients(){
    $.ajax({
        type: "GET",
        url: "/plex_client",
        complete: function(return_data){
            let m_html = return_data.responseText
            let response_code = return_data.status
            if (response_code != 200) {
                show_messages("Unable to get clients from server")
            }
            else{
                document.getElementById("client-selection-list").innerHTML = m_html
            }
        }
    });
}

function shuffle_shows(){
    var limit = document.getElementById('max-episode-input').value
    if (limit === ''){
        limit = 10
    }
    document.getElementById("episode_list").innerHTML = waiting
    data = {
        'limit': limit,
    }
    $.ajax({
        type: "GET",
        data: data,
        url: "/shuffle",
        complete: function(return_data){
            let response_data = return_data.responseJSON
            let response_code = return_data.status
            if (response_code != 200) {
                show_messages("Unable to get plex queue from server")
                document.getElementById("episode_list").innerHTML = "Unable to get plex queue from server"
            }
            else{
                if (response_data.shuffle){
                    get_plex_queue()
                }
                else{
                    show_messages(response_data.message)
                    get_plex_queue()
                }
            }
        }
    });
}

function remove_episode(ratingKey){
    data = {
        'ratingKey': ratingKey
    }
    $.ajax({
        type: "GET",
        data: data,
        url: "/remove_episode",
        complete: function(return_data){
            let response_data = return_data.responseJSON
            let response_code = return_data.status
            if (response_code != 200) {
                show_messages("Unable remove episode from queue")
            }
            else{
                if (response_data.remove){
                    document.getElementById(ratingKey).hidden = true
                    update_shuffled_view_title()
                }
                else{
                    show_messages(response_data.message)
                }
            }
        }
    });
    return false;
}

function play_queue(client_name){
     data = {
        'client': client_name
     }
     $.ajax({
        type: "POST",
        url: "/plex_client",
        data: data,
        complete: function(return_data){
            let response_data = return_data.responseJSON
            let response_code = return_data.status
            if (response_code != 200) {
                show_messages("Unable to play queue on client")
            }
            else{
                show_messages(response_data.message)
            }
        }
    });
    return false
}
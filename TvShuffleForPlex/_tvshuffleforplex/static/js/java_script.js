let waiting = '<div class="container waiting pt-5 pb-10 text-center"><div class="spinner-border" role="status"><h2 class="pl-2 text-center">Loading...</h2></div></div>'

$(document).ready(function(){
    if (document.getElementById("show_list")){
        document.getElementById("show_list").innerHTML = waiting;
        $.ajax({
            type: "GET",
            url: "/get_tv_show_list",
            complete: function(return_data){
                let m_html = return_data.responseText;
                let responce_code = return_data.status
                if (responce_code != 200) {
                    document.open()
                    document.write(m_html)
                    document.close()
                }
                else{
                    document.getElementById("show_list").innerHTML = m_html;
                }
            }
        });
    }
});

function test_click(class_name){
    $("." + class_name).toggleClass('selected');
    counter();
}

$('.select-button').click(function (e) {
  if ($('.show_list_item.selected').length == 0) {
    $('.show_list_item').addClass('selected');
  }
  else {
    $('.show_list_item').removeClass('selected');
  }
  counter();
});

$('.save-selected-button').click(function(){
    console.log("test");
});

$('.shuffle-submit-button').click(function (e){
    let data = {}
    data['list'] = getSelectedShows();
    data['shuffle_style'] = getShuffleType();
    data['max_episode_count'] = getMaxEpisodeCount();
    $('.waiting').show();
    document.getElementById("shuffled_view").innerHTML = "";
    $.ajax({
        type: "POST",
        url: "{% url 'shuffle' %}",
        data: data,
        complete: function(return_data){
            let m_html = return_data.responseText;
            let responce_code = return_data.status
            if (responce_code != 200) {
                document.open()
                document.write(m_html)
                document.close()
                $('.waiting').hide();
            }
            else{
                document.getElementById("shuffled_view").innerHTML = m_html;
                $('.waiting').hide();
            }
        }
    });
});

$('.server-select-button').click(function (e){
    m_html = "<li class='dropdown-item'><a href='#'>Loading...</a></li>"
    document.getElementById("server-selection-list").innerHTML = m_html;
    get_servers_list();
})

$('.save-select-list-button').click(function (e){
    m_html = "<li class='dropdown-item'><a href='#'>Loading...</a></li>"
    document.getElementById("save-list-selection").innerHTML = m_html;
    get_saved_list();
})

function get_servers_list(){
     $.ajax({
        type: "GET",
        url: "/get_server_list",
        complete: function(return_data){
            let m_html = return_data.responseText;
            let responce_code = return_data.status
            if (responce_code != 200) {
                document.open()
                document.write(m_html)
                document.close()
            }
            else{
                document.getElementById("server-selection-list").innerHTML = m_html;
            }
        }
    });
}

function get_saved_list(){
    $.ajax({
        type: "GET",
        url: "/get_saved_list",
        complete: function(return_data){
            let m_html = return_data.responseText;
            let responce_code = return_data.status
            if (responce_code != 200) {
                document.open()
                document.write(m_html)
                document.close()
            }
            else{
                document.getElementById("save-list-selection").innerHTML = m_html;
            }
        }
    });
}

function getMaxEpisodeCount(){
    return document.getElementById("max-episode-input").value;
}

function getSelectedSaveName(){
    return document.getElementById("save-select-name-input").value;
}

function getSelectedShows(){
    const send_list = []
    if ($('.show_list_item.selected').length != 0) {
        for (i=0;i<$('.show_list_item.selected').length;i++){
            const item = $('.show_list_item.selected')[i];
            title = item.innerText;
            send_list.push(title);
        }
    }
    return send_list;
}

function getShuffleType(){
    shuffle_style = "inclusive";
    var radios = document.getElementsByName("optradio");
    for (var i = 0; i<radios.length; i++){
        if (radios[i].checked){
            shuffle_style = radios[i].value;
        }
    }
    return shuffle_style
}

function counter() {
  display=document.getElementById('selected-count');
  display.innerHTML=$('.show_list_item.selected').length;
}

$(function () {
  $('[data-toggle="tooltip"]').tooltip()
})


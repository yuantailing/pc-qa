$(document).ready(function() {
    $.post(api_query, {
        csrfmiddlewaretoken: $.cookie('csrftoken'),
    }, function(data) {
        console.log(data);
    });
    $.post(api_tips, {
        csrfmiddlewaretoken: $.cookie('csrftoken'),
    }, function(data) {
        console.log(data);
    });
});

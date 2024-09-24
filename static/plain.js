// JavaScript File to add event-handlers to "rate" a movie

function processAverage(resp) {
    // I didn't ask you to do this error reporting
    if(resp.error) {
        // inserting into an error section would 
        // probably be better than an alert
        alert('Error: '+resp.error);
    }
    var tt = resp.tt;
    var avg = resp.avg;
    console.log("New average for movie "+tt+" is "+avg);
    $("[data-tt="+tt+"]").find(".avgrating").text(avg);
}

/* global url_to_rate progressive_on uid */
/* The preceding globals are defined in the movie-list.html template */

$("#movies-list").on('click',
                     '.movie-rating',
    function (event) {
        if(!progressive_on) return;

        if( event.target != this) return;
        $(this).closest("td").find("label").css("font-weight","normal");
        $(this).css("font-weight","bold");
        var tt = $(this).closest("[data-tt]").attr("data-tt");
        var stars = $(this).find("[name=stars]").val();
        // references the uid variable set by the template
        console.log("user "+uid+" rates movie "+tt+" as "+stars);
        $.post(url_to_rate,{'tt': tt, 'stars': stars},processAverage,'json');
    });

function showResponse(resp) {
    console.log('response is: ', resp);
}

function rateMovie(url, tt, stars) {
    $.post(url, {'tt': tt, 'stars': stars}, showResponse, 'json');
}

function rateMovieUpdate(url, tt, stars) {
    $.post(url, {'tt': tt, 'stars': stars}, processAverage, 'json');
}

// Could change the callback to processAverage to update the page

function getRating(url, tt) {
    $.ajax(url+tt, {method: 'GET',
                    success: showResponse});
}

function putRating(url, tt, stars) {
    $.ajax(url+tt, {method: 'PUT',
                    data: {stars: stars},
                    success: showResponse});
}

// same as putRating
function postRating(url, tt, stars) {
    $.ajax(url+tt, {method: 'POST',
                    data: {stars: stars},
                    success: showResponse});
}

function deleteRating(url, tt) {
    $.ajax(url+tt, {method: 'DELETE',
                    success: showResponse});
}

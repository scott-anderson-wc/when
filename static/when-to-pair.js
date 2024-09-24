/*
  Code for the UI for the when to pair app. Much of this implementation is inspired by
  whenisgood.net, which was kind enough not to obfuscate their code. I particularly looked
  at https://whenisgood.net/static/scripts/create.js

  Design:

  Time slots will be 30 minutes long, from 9am to 12pm, so 30 slots
  per day. Interestingly, that means the choices for each day can be
  represented by a 30-bit integer.
  
  The set of chosen time slots is represented as a JS set
  object. (This is different from whenisgood, which uses an array.)
  The values will be strings of the form day-hour, like "Mon-900" or
  "Tue-930". We'll use 24hour time internally. Since time slots on
  different days actually can't overlap, we'll also represent this
  with 7 sets, one for each day of the week, and each representing
  just the time slot. 

  (Ideally, we'd represent the data in the database with 7 ints, but
  I'll leave that for another time.)

  The DOM element will have attributes: data-slot='Mon-900'
  data-day='Mon' data-time='900'

  The UI sets handlers for mousedown, mousemove and mouseup.

  The mousedown will indicate that the mouse is down by toggling a
  global. If the cell that the mouse is in when the mouse goes down is
  selected, then the mode is to de-select cells. Otherwise, it is to
  select cells. It also selects/deselects that cell.

  The mousemove will select/deselect the current cell. It would
  probably be more efficient just to trigger on mouse enter but it
  works for whenisgood.net

  The mouseup will toggle the global about whether the mouse is down.

  August 9, 20204

  Scott D. Anderson

*/

"use strict";

var students = null;            // a list of dictionaries: {name, email}

/*
$(document).ready(function () {
    let pathname = window.location.pathname;
    let components = pathname.split('/');
    courseId = components[components.length-1];
    alert('setting courseId to ${courseId}');
});
*/

var setting = true;             // mode is to select the slot; false to deselect
var isDown = false;             // true iff the mouse is down. We could also test this in the object

var selectedSlots = new Set();
const daysOfTheWeek = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

function emptyDaySlots() {
    let dic = {};
    for (let day of daysOfTheWeek) {
        dic[day] = new Set();
    }
    return dic;
}    

// 
var daySlots = emptyDaySlots();

function updateSlot(setSlot, elt) {
    const slot = elt.attr('data-slot');
    const day = elt.attr('data-day');
    const time = elt.attr('data-time');
    if(! day in daySlots) {
        throw new Error(`not a valid day: ${day}`);
    }
    console.log('day', day);
    if(setSlot) {
        selectedSlots.add(slot);
        daySlots[day].add(time);
        elt.addClass('chosen');
    } else {
        selectedSlots.delete(slot);
        daySlots[day].delete(time);
        elt.removeClass('chosen');
    }
}

function processMouseDown(elt) {
    elt = $(elt);
    let slot = elt.attr('data-slot');
    let isSet = selectedSlots.has(slot);
    setting = ! isSet;          // we are setting slots if this one isn't set
    updateSlot(setting, elt);
}

function processMouseMove(elt) {
    elt = $(elt);
    if(! isDown) return;
    updateSlot(setting, elt);
}

var sched_a = null, sched_b = null;

$("#when").on('mousedown', 'td', (evt) => { isDown = true; processMouseDown(evt.target) });
$("#when").on('mousemove', 'td', (evt) => { processMouseMove(evt.target) });
$("#when").on('mouseup', 'td', (evt) => { isDown = false; });
$("#clear").click(function () {
    selectedSlots = new Set();
    daySlots = emptyDaySlots();
    $(".chosen").removeClass("chosen");
});
$("#save").click(submitSettings);
$("#show_both").click(showBoth);

// ================================================================
// table generation

// returns a list suitable for creating a MySQL set
// like allSlots.map(s => `'${s}'`).join(',');

var allSlots = (function () {
    let slots = [];
    for( let hour = 9; hour < 24; hour++ ) {
        for (let min of ['00', '30']) {
            let slot = `${hour}${min}`;
            slots.push(slot);
        }
    }
    return slots;
})();
    

// This function assumes the current #when table, and replaces the
// example elements with the full week's worth.

function makeSlotTable() {
    let head = $("#when thead tr");
    head.empty();
    daysOfTheWeek.forEach(dayName => $("<th scope=col>").text(dayName).appendTo(head));
    let body = $("#when tbody");
    body.empty();
    // outer loop is hour
    for( let hour = 9; hour < 24; hour++ ) {
        let hourStr;
        if( hour < 12 ) {
            hourStr = `${hour}am`;
        } else if (hour == 12) {
            hourStr = `${hour}pm`;
        } else {
            hourStr = `${hour-12}pm`;
        }
        // outer loop is minutes (00 or 30)
        // inner loop is day of the week
        // result is this TR
        for (let min of ['00', '30']) {
            let tr = $('<tr>');
            hourStr = (min == '00' ? hourStr : min);
            for (let day of daysOfTheWeek) {
                $('<td>')
                    .attr('data-slot', `${day}-${hour}${min}`)
                    .attr('data-day', day)
                    .attr('data-time', `${hour}${min}`)
                    .text(hourStr)
                    .appendTo(tr);
            }
            tr.appendTo(body);
        }
    }
}

$(document).ready(makeSlotTable);

// ================================================================
// Sending data to the server. Required data is classid (like
// cs304-fa24), user (an email address, like ww123), and 7 sets. The
// database table will have the same columns.

/* Utility function, to use form submission and the Fetch API. The
 * following works and can be processed by Flask in the request.form
 * object. The representation in the dev tools looks weird compared to
 * jQuery's .post method, but the size of the request is nearly
 * identical. */

function postFormUsingFetch(url, data) {
    let fd = new FormData();
    for( let key in data ) {
        fd.set(key, data[key]);
    }
    let req = new Request(url, {method: 'POST', body: fd});
    fetch(req)
        .then((response) => {
            if (response.status === 200) {
                return response.json();
            } else {
                throw new Error("Something went wrong on API server!");
            }
        })
        .then((response) => {
            console.debug('server response', response);
        })
        .catch((error) => {
            console.error(error);
        });
}

/* JQuery makes it easier. It automatically parses the response (if it's valid JSON).
   */

function postFormUsingJQ(url, data) {
    $.post(url, data)
        .then((response) => {
            console.debug('server response', response);
        })
        .catch((resp) => {
            console.log('response status ', resp.status);
            console.error(resp);
        });
}


// ================================================================
// turn a list of values into an integer using the same rules as for MySQL.

function encodeSlotSet(slotSet) {
    let setValue = 0;
    for( let bit=0; bit < allSlots.length; bit++ ) {
        let value = 1 << bit;
        let slot = allSlots[bit];
        if (slotSet.has(slot)) {
            setValue |= value;
            // console.log('setValue', setValue);
        }
    }
    return setValue;
}

// returns a list of strings for the contents of the 

function decodeSlotSet(setAsInt) {
    let setValue = 0;
    let slots = []
    for( let bit=0; bit < allSlots.length; bit++ ) {
        let value = 1 << bit;
        let slot = allSlots[bit];
        if ( (setAsInt & value) != 0) {
            slots.push(slot);
            // console.log('adding to set', slot);
        }
    }
    return slots;
}

function testEncodeDecode(n) {
    let elts = decodeSlotSet(n);
    let set = new Set(elts);
    let y = encodeSlotSet(set);
    console.log(n, y, n==y ? 'worked!' : 'FAILED!');
}


// ================================================================

function getStudent() {
    let student = $("[name=student]").val();
    if( student === '' ) {
        alert("Please select your name from the drop-down menu.");
        throw new Error('no student');
    }
    return student;
}

function getCourseId() {
    if( ! courseId ) {
        alert("No course seems to be selected.");
        throw new Error('no courseId');
    }
    return courseId;
}

// submit the current settings. The course id will be in the URL, and
// the student name/email will be chosen from a menu, which we also have to get

function makePayload() {
    let student = getStudent();
    let courseId = getCourseId();
    let payload = {student, courseId};
    for( let day of daysOfTheWeek ) {
        payload[day] = encodeSlotSet(daySlots[day]);
    }
    return payload;
}


function submitSettings() {
    let p = makePayload();
    globalThis.payload = p;
    postFormUsingJQ(urlToSave, p);
}

// ================================================================
// showing two schedules with overlap

async function showBoth(a_or_b) {
    clearColors();
    let studentA = $("[name=studentA]").val();
    let studentB = $("[name=studentB]").val();
    if ( studentA == '' ) {
        alert('StudentA missing');
    }
    if ( studentB == '' ) {
        alert('StudentB missing');
    }
    let courseId = getCourseId();
    let respA = await $.get(urlToGetSchedule, {student: studentA, courseId})
        .catch((resp) => { if(resp.error) { alert(resp.error)} });
    console.log(respA);
    displaySchedule('a', respA.row);

    let respB = await $.get(urlToGetSchedule, {student: studentB, courseId})
        .catch((resp) => { if(resp.error) { alert(resp.error)} });
    console.log(respB);
    displaySchedule('b', respB.row);
}

function clearColors() {
    $("td").attr('style','');
}

function displayScheduleColor(sched, color) {
    // sched is an array of ints
    for( let i = 0; i < 7; i++) {
        let day = daysOfTheWeek[i];
        let slots = decodeSlotSet(sched[i]);
        console.log('day', day, 'slots', slots);
        for (let slot of slots) {
            let sel = `[data-slot='${day}-${slot}']`;
            console.log('sel', sel);
            $(sel).one().css({'background-color': color});
        }
    }
}
    

const color_a = 'rgb(255,255,100)'; // yellow
const color_b = 'rgb(173,240,255)'; // light blue
const color_c = 'rgb(0,255,0)'; // lime green

function displaySchedule(a_or_b, row) {
    let color = (a_or_b === 'a')  ? color_a : color_b;
    // sched is an array of 7 ints
    let sched = row.slice(3);
    console.log('sched', sched);
    if( a_or_b == 'a' ) {
        sched_a = sched;
    } else {
        sched_b = sched;
    }
    displayScheduleColor(sched, color);
    // now the intersection
    if( sched_a && sched_b ) {
        let both = [];
        for( let i = 0; i < 7; i++ ) {
            both[i] = sched_a[i] & sched_b[i];
        }
        console.log('both', both);
        displayScheduleColor(both, color_c);
    }
}

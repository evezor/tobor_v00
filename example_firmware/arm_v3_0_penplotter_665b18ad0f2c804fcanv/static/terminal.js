
var this_history
let _hist = JSON.parse(localStorage.getItem('this_history'))
if (_hist == null) {
    this_history = [];
} else {
    this_history = _hist.slice(0, 50)
}

var this_history_idx = 0;

function init() {
    var host_type = document.getElementById('host_type').innerHTML;
    if (host_type === 'pyscript'){
        return
    }

    var nwkId = document.getElementById("nwk_id").value;
    var token = document.getElementById("token").value;
    var canvas_id = getElmById("canvas_id").value;

    var wsUri;


    if (host_type == 'cpython') {
        if (window.location.protocol == 'https:') {
            wsUri = "wss://" + window.location.hostname + "/sockets/" + nwkId + "/ws?token=" + token + "|" + Date.now() + "&canvas_id=" + canvas_id;
        }
        else {
            wsUri = "ws://" + window.location.host + "/sockets/" + nwkId + "/ws?token=" + token + "|" + Date.now() + "&canvas_id=" + canvas_id;
        }
    }
    else if (host_type == 'esp32') {
        if (window.location.protocol == 'https:')
            wsUri = 'wss://' + window.location.hostname + '/wschat'
        else
            wsUri = 'ws://' + window.location.hostname + '/wschat';
    }
    else if (host_type == 'esp32_test') {
        if (window.location.protocol == 'https:')
            wsUri = 'wss://' + window.location.hostname + '/wschat'
        else
        var host_location = document.getElementById('host_location').innerHTML;
            wsUri = 'ws://' + host_location + '/wschat';
    }
    console.log(wsUri);

    writeLineToChat("Connection to " + wsUri + "...")
    websocket = new WebSocket(wsUri);
    websocket.onopen = function (evt) { onOpen(evt) };
    websocket.onclose = function (evt) { onClose(evt) };
    websocket.onmessage = function (evt) { onMessage(evt) };
    websocket.onerror = function (evt) { onError(evt) };
    getElmById("input-chat").addEventListener("keydown", onChatLine);
    getElmById("input-chat").addEventListener("keyup", clearChatLine);
    getElmById("input-chat").focus();

    hermes.websocket = websocket;
    console.log(hermes);
    document.getElementById('connect_button').style.visibility = 'hidden'
}

function getElmById(id) {
    return document.getElementById(id);
}

function writeLineToChat(line) {
    var elm = getElmById('chat');
    if (elm) {
        var lineElm = document.createElement('div');
        if (line) {
            var time = new Date().toLocaleTimeString();
            let text = line.replace('\n', '<br>');
            lineElm.innerHTML = `<span style="font-size: 10px; color: lightgrey;">${time}:</span> ${text}`
        }
        else
            lineElm.innerHTML = '&nbsp;';
        elm.appendChild(lineElm);
        elm.scrollTop = elm.scrollHeight;
    }
}


function onOpen(evt) {
    writeLineToChat("[CONNECTED]")
    hermes.websocket.send('get_webstuff');
}

function onClose(evt) {
    writeLineToChat("[CONNECTION CLOSED]")
}

function onError(evt) {
    writeLineToChat("[CONNECTION ERROR]")
}

function onMessage(evt) {
    doMessage(evt.data)
}

function doMessage(msg) {
    // separating out so pyscript has a hook
    // console.log('msg', msg);

    function parse(string) {
        const comma_index = string.indexOf(',');
        if (comma_index !== -1) {
            const pid = string.substring(0, comma_index);
            const data = string.substring(comma_index + 1);
            return { pid, data };
        } else {
            return null; // Comma not found in the string.
        }
    }

    
    
    var msg = parse(msg)
    if (msg == null) {
        writeLineToChat('unknown event: ' + msg);
        return
    }

    if (msg.pid == 'term') {
        writeLineToChat(msg.data);
    }
    else if (msg.pid == 'compose_page') {
        hermes.compose_page(msg.data);
    }
    else if (msg.pid == 'listdir') {
        hermes.listdir(msg.data);
    }
    else if (msg.pid == 'to_file_editor') {
        hermes.to_file_editor(msg.data);
        return
    }
    else if (msg.pid == 'send_next_chunk') {
        hermes.send_chunk();
        return
    }

    else {
        try {
            // console.log('pid: ' + msg.pid + ' data: ' + msg.data)
            hermes.p[msg.pid](msg.pid, msg.data);    
        } catch (error) {
            console.log(error)
            console.log(msg)
        }
    }
}

function clearChatLine(e) {
    key = (e.key || e.keyCode);
    // console.log(key);
    if ((key === 13 || key.toUpperCase() === "ENTER") && !event.shiftKey) {
        input = getElmById("input-chat");
        input.innerHTML = "";
    }
}


function onChatLine(e) {
    key = (e.key || e.keyCode);
    // console.log(key);
    var index = 0;

    if (key == "ArrowUp") {
        // console.log(this_history[this_history_idx]);
        var chat = getElmById("input-chat");
        _history = this_history[this_history_idx];
        chat.innerHTML = _history;
        chat.focus(chat);
        this_history_idx += 1;
        if (this_history_idx > this_history.length) {
            this_history_idx = this_history_idx;
        }
    }

    else if (key == "ArrowDown") {
        console.log(this_history[this_history_idx]);
        var chat = getElmById("input-chat")
        chat.focus(chat)
        chat.innerHTML = this_history[this_history_idx]
        this_history_idx -= 1
        if (this_history_idx < 0) {
            this_history_idx = 0;
        }
    }
    else if ((key === 13 || key == "Enter") && !event.shiftKey) {
        input = getElmById("input-chat");
        line = input.innerHTML.trim();
        if (line != this_history[0]){
            this_history.unshift(line) // do not add multiples of the same command
        }
        
        line = line.replace(/<br ?\/?>/g, "\n")
        line = line.replace(/&nbsp;/g, ' ')
        cleanText = line.replace(/<\/?[^>]+(>|$)/g, "");
        // console.log(cleanText)
        
        localStorage.setItem('this_history', JSON.stringify(this_history))
        // writeLineToChat(">>> " + cleanText)
        this_history_idx = 0
        input.innerHTML = "";

        if (line.length > 0)
            websocket.send(`term,${line}`);
    }
}


window.addEventListener("load", init, false);





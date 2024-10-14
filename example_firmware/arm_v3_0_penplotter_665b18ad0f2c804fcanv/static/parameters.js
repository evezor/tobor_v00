
function gid(pid) {
  return document.getElementById(pid);
}

let parameters = document.getElementById('parameters');
var constructors = {}
var hermes = { 
  p:{}, 
  send: function(pid, data) {
    var msg = `${pid},${data}`;
    // console.log(msg);
    this.websocket.send(msg);
  },
  send_json: function(pid, data) {
    const json = JSON.stringify(data);
    var msg = `${pid},${json}`;
    // console.log(msg);
    this.websocket.send(msg);    
  },
  compose_page: function(data) {
    const json = JSON.parse(data);
    build_params(json);
  }
}

var Zorg = {
  call: function (_pid, cmd) {
    let type;
    let msg;
    let load;
    if (cmd == 'send'){
      if (gid(`${_pid}_radio_string`).checked){
        type = 'string';
        msg =  gid(`${_pid}_string`).value;
      }
      else {
        type = 'bytes';
        msg = [
          gid(`${_pid}_bytes_0`).value,
          gid(`${_pid}_bytes_1`).value,
          gid(`${_pid}_bytes_2`).value,
          gid(`${_pid}_bytes_3`).value,
          gid(`${_pid}_bytes_4`).value,
          gid(`${_pid}_bytes_5`).value,
          gid(`${_pid}_bytes_6`).value,
          gid(`${_pid}_bytes_7`).value,
        ]
      }
      load = {
        cmd: cmd,
        adr: gid(`${_pid}_adr`).value, 
        pid: gid(`${_pid}_pid`).value,
        type: type,
        msg: msg,
        write: gid(`${_pid}_read`).checked
      }
    }
    else if (cmd == 'create_sub') {
      load = {
        cmd: cmd,
        sender: {
          adr: gid(`${_pid}_sub_s_adr`).value,
          pid: gid(`${_pid}_sub_s_pid`).value,
        },
        recvr: {
          adr: gid(`${_pid}_sub_adr`).value,
          pid: gid(`${_pid}_sub_pid`).value,
        },
        struct: gid(`${_pid}_struct`).value,
      }
    }
    else if (cmd == 'ide_subs') {
      load = {
        cmd: cmd,
        subs: gid(`${_pid}_ide_subs`).value,
      }
    }
    else if (cmd == 'save_subs') {
      load = {
        cmd: cmd
      }
    }
    else if (cmd == 'clear_subs') {
      load = {
        cmd: cmd
      }
    }
    console.log(load);
    hermes.send_json(_pid, load)
  },
  getHTML: function(param) {
    return `<div class="parameter">
    <span style="font-size:1.2em; color: white">${param.name} </span>
    <button onclick="toggleCollapsible(this)">-</button>
    <div>
      <span style="font-size:.7em; color: white">Subs List</span><button onclick="toggleCollapsible(this)">-</button>
      <br>    
      <div id="${param.pid}_subs_list">
      </div>
    </div><br>
    <div id="${param.pid}_msg_sender">
      <span style="font-size:.7em; color: white">Message Sender </span><button onclick="toggleCollapsible(this)">-</button>
      <table>
        <td>write: </td>
        <td><input type="checkbox" id="${param.pid}_read" checked></td>
        <td>unchecked is event</td>
      </table>
      <div>
      <table style="width: 100%">
        <tr>
          <td>adr: </td>
          <td><input id="${param.pid}_adr"></td>
        </tr>
        <tr>
          <td>pid: </td>
          <td><input id="${param.pid}_pid"></td>
        </tr>
        <tr>
          <td>msg: </td>
          <td> 
            <input type="radio" id="${param.pid}_radio_string" name="zorg_radio" checked>
            <label for="${param.pid}_radio_string">string: </label>
            <input type="text" id="${param.pid}_string" style="max-width: 500px"><br>
            <input type="radio" id="${param.pid}_radio_bytes" name="zorg_radio">
            <label for="${param.pid}_radio_bytes">bytes: </label>
            <input type="number" id="${param.pid}_bytes_0" style="width: 55px;">
            <input type="number" id="${param.pid}_bytes_1" style="width: 55px;">
            <input type="number" id="${param.pid}_bytes_2" style="width: 55px;">
            <input type="number" id="${param.pid}_bytes_3" style="width: 55px;">
            <input type="number" id="${param.pid}_bytes_4" style="width: 55px;">
            <input type="number" id="${param.pid}_bytes_5" style="width: 55px;">
            <input type="number" id="${param.pid}_bytes_6" style="width: 55px;">
            <input type="number" id="${param.pid}_bytes_7" style="width: 55px;">
          </td>
        </tr>
      </table>
      </div>
    
      <button id="${param.pid}_send" class="xsm_button green" onclick="Zorg.call(${param.pid}, 'send')">send</button>
    </div>
    <div id="${param.pid}_sub_sender">
      <span style="font-size:.7em; color: white">Create Subscription </span><button onclick="toggleCollapsible(this)">-</button>
      <br>    
      send adr: <input type="number" id="${param.pid}_sub_s_adr" style="width: 50%"><br>
      send pid: <input type="number" id="${param.pid}_sub_s_pid" style="width: 50%"><br>
      recv adr: <input type="number" id="${param.pid}_sub_adr" style="width: 50%"><br>
      recv pid: <input type="number" id="${param.pid}_sub_pid" style="width: 50%"><br>
      struct: <input type="text" id="${param.pid}_struct" style="width: 100px"><br>
  
      <button id="${param.pid}_send_sub" class="xsm_button green" onclick="Zorg.call(${param.pid}, 'create_sub')">send</button>
    </div>
    <div id="${param.pid}_create_subs">
      <span style="font-size:.7em; color: white">Create Subs From IDE</span><button onclick="toggleCollapsible(this)">-</button>
      <br>    
      subs: <input type="text" id="${param.pid}_ide_subs" style="width: 50%"><br>
      <button id="${param.pid}_ide_sub" class="xsm_button green" onclick="Zorg.call(${param.pid}, 'ide_subs')">send</button>
    </div>
  </div>`
    },
  init: function (param) {
    hermes.p[param.pid] = function (pid, data) {
      console.log(data)
      let subs = gid(`${pid}_subs_list`);
      subs.innerHTML = subs.innerHTML + '<br>' + data
    }
  }

}
constructors["Zorg"] = Zorg

var Terminal = {
  write : function (terminal, line) {
    var lineElm = document.createElement('div');
      if (line) {
          var time = new Date().toLocaleTimeString();
          lineElm.innerText = "[" + time + "] " + line;
      }
      else
          lineElm.innerHTML = '&nbsp;';
      terminal.appendChild(lineElm);
      terminal.scrollTop = terminal.scrollHeight;
  },
  clear_input: function (e) {
    key = (e.key || e.keyCode);
    // console.log(key);
    if ((key === 13 || key.toUpperCase() === "ENTER") && !e.shiftKey) {
      this.innerHTML = "";
    }
  },
  on_input: function (e) {
    key = (e.key || e.keyCode);
    // console.log(key);
    var index = 0;

    if ((key === 13 || key.toUpperCase() === "ENTER") && !e.shiftKey) {
      // input = getElmById("input-chat");
      line = this.innerHTML.trim();
      line = line.replaceAll('<br>', '\n');
      cleanText = line.replace(/<\/?[^>]+(>|$)/g, "");
      // console.log(cleanText)
      Terminal.write(this.terminal, ">>> " + cleanText);
      index = 0
      // input.innerHTML = "";
      // This is a HACK and should probably do something else, like call a function owned by the terminal owner and they can send to hermes however they see fit
      json = {"cmd": "term", "msg": cleanText}
      hermes.send_json(this.terminal.pid, json);
      console.log(json);
    }
  },
  init: function(param) {
    var term_input = gid(`${param.pid}_input`);
      term_input.terminal = gid(`${param.pid}_terminal`);
      term_input.terminal.pid = param.pid;
      term_input.addEventListener('keydown', Terminal.on_input);
      term_input.addEventListener('keyup', Terminal.clear_input);
    return term_input.terminal
  }
}
constructors["Terminal"] = Terminal

var GuiCmdAggregator = {
  assets: {},
  getHTML: function(param) {
    return `
    <div class="parameter">
    <h3>${param.name}</h3>
    <div id="${param.pid}_editor"  style="border: 2px solid black;">
  <!-- Create a textarea for the CodeMirror editor -->
  <textarea id="${param.pid}_code" name="${param.pid}_code">{"x":11, "y": 11}</textarea>
  <!-- Create a draggable bar for resizing -->
  <div id="${param.pid}_resize-bar" style="cursor: row-resize; height: 6px; background-color: #ccc; position: relative; bottom: -6px; width: 100%;"></div>
  </div>
  <div style="height: 7px;"></div>
  <span style="color: red; padding-top:50px; font-size:10px;" id="${param.pid}_editor_error" ></span><br>
  <button onclick='GuiCmdAggregator.add_element(${param.pid}, null)'>add element</button>
  <button onclick="GuiCmdAggregator.send(${param.pid})">create event</button>
  <button onclick="GuiCmdAggregator.verify(${param.pid})">verify</button>
  <button onclick="GuiCmdAggregator.copy2clip(${param.pid})">copy as json list</button>
`
  },
  init: function(param) {
    hermes.p[param.pid] = function (pid, data) {
      let editor = GuiCmdAggregator.assets[`${pid}_editor`];
      editor.setValue(editor.getValue() + '\n' + data);
    }
    // Initialize CodeMirror
    this.assets[`${param.pid}_editor`] = CodeMirror.fromTextArea(document.getElementById(`${param.pid}_code`), {
        lineNumbers: true, // Display line numbers
        mode: "python", // Set mode to Python
        theme: "dracula" // Set theme (you can change it)
    });

    let editor = this.assets[`${param.pid}_editor`]

    // Set initial and maximum height
    var initialHeight = 100; // Initial height in pixels
    var maxHeight = 800; // Maximum height in pixels

    // Set initial height
    document.getElementById(`${param.pid}_editor`).style.height = initialHeight + 'px';

    // Make editor resizable
    editor.setSize(null, initialHeight);

    // Get the resize bar element
    this.assets[`${param.pid}_resizeBar`] = document.getElementById(`${param.pid}_resize-bar`);

    // Function to handle mouse down on the resize bar
    this.assets[`${param.pid}_resizeBar`].addEventListener('mousedown', function(event) {
        event.preventDefault(); // Prevent text selection
        var startY = event.clientY;
        var startHeight = editor.getWrapperElement().clientHeight;

        // Function to handle mouse move while dragging
        function onMouseMove(event) {
            var delta = event.clientY - startY;
            var newHeight = startHeight + delta;
            newHeight = Math.min(Math.max(newHeight, initialHeight), maxHeight);
            document.getElementById(`${param.pid}_editor`).style.height = newHeight + 'px';
            editor.setSize(null, newHeight);
        }

        // Function to handle mouse up after dragging
        function onMouseUp() {
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
        }

        document.addEventListener('mousemove', onMouseMove);
        document.addEventListener('mouseup', onMouseUp);
    });
  },
  add_element: function(pid, arg) {
    if (arg == null) {
      arg = '{"x":11, "y": 11}'
    }
    let editor = this.assets[`${pid}_editor`]; 
    editor.setValue(editor.getValue() + '\n' + arg);
  },
  send: function (pid) {
    let list = this.verify(pid, false);
    if (list !== null) {
      // console.log(list);
      hermes.send(pid, list)
    }
    
  },
  verify: function(pid, json) {
    let editor = this.assets[`${pid}_editor`]; 
    let raw = editor.getValue().split('\n')
    for (e in raw) {
      // console.log(raw[e]);
      try {
        if (JSON.parse(raw[e]) == "<empty string>") {
          console.log('empty string')
        }
      }
      catch {
        document.getElementById(`${pid}_editor_error`).innerHTML = `error on line ${parseInt(e)+1} - no action was taken`
        return null
      }
    }
    document.getElementById(`${pid}_editor_error`).innerHTML = ""
    if (json == true) {
      return list = `[${raw}]`;
    }
    return editor.getValue()
  },
  copy2clip: function(pid) {
    let clip = this.verify(pid, true)
    if (clip != null) {
      navigator.clipboard.writeText(clip);
    }
  }
}
constructors["GuiCmdAggregator"] = GuiCmdAggregator

var GuiCodeEditor = {
  getHTML: function(param) {
    return `
    <div class="parameter">
    <h3>${param.name}</h3>
    <input type="file" id="${param.pid}_file_input">
<pre ><code  id="${param.pid}_editor" style="resize: vertical; overflow: scroll; min-height: 100px; max-height: 700px; padding:0px;" class="atom-one-dark-reasonable python" spellcheck="false" contenteditable="true">${param.state}</code></pre>
    <button class="xsm_button green" onclick="GuiCodeEditor.send(${param.pid})">submit</button>
    <button class="xsm_button pink" onclick="GuiCodeEditor.highlight('${param.pid}')">highlight</button>
    <button class="xsm_button coral" onclick="GuiCodeEditor.save_file('${param.pid}_editor')">save file</button>
    `
  },
  highlight: function(pid) {
    gid(`${pid}_editor`).innerHTML = gid(`${pid}_editor`).innerHTML.replace(/<br>/g, '\n');
    hljs.highlightAll()
  },

  send: function(pid) {
    const text = gid(`${pid}_editor`).innerText;
    hermes.send(pid, text);
  },
  init: function(param) {
    hermes.p[param.pid] = function (pid, data) {
      gid(`${pid}_editor`).innerHTML = data;
      hljs.highlightAll();
    }
    hljs.highlightAll();
    document.getElementById(`${param.pid}_file_input`).addEventListener('change', function (event) {
      const fileInput = event.target;
      
      if (fileInput.files.length > 0) {
        const selectedFile = fileInput.files[0];
        // Read the file content
        const reader = new FileReader();
        reader.onload = function (e) {
          const fileContent = e.target.result;
          document.getElementById(`${param.pid}_editor`).innerHTML = fileContent;
          hljs.highlightAll();
        };
        reader.readAsText(selectedFile);
      }
    });
  },
  save_file: function(target) {
    // Prompt for a filename
    const fileName = prompt('Enter a filename: extension already ".evzr"');
    
    if (fileName) {
      const fileContent = document.getElementById(target).innerText;

      const blob = new Blob([fileContent], { type: 'text/plain' });
      const blobUrl = URL.createObjectURL(blob);

      const a = document.createElement('a');
      a.href = blobUrl;

      a.download = fileName + '.evzr';

      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);

      URL.revokeObjectURL(blobUrl);
    }
  },
}
constructors["GuiCodeEditor"] = GuiCodeEditor

var Gui3dViewer = {
  getHTML: function(param) {
    return `
    <div class="parameter">
    <h3>${param.name}</h3>
    <input type="file" id="${param.pid}_file_input">
<pre><code  id="${param.pid}_editor" style="resize: vertical; overflow: scroll; min-height: 100px; max-height: 700px; padding:0px;" class="atom-one-dark-reasonable python" spellcheck="false" contenteditable="true">${param.state}</code></pre>
    <button class="xsm_button green" onclick="Gui3dViewer.send(${param.pid})">submit</button>
    <button class="xsm_button pink" onclick="Gui3dViewer.highlight('${param.pid}')">highlight</button>
    <button class="xsm_button blue" onclick="Gui3dViewer.save_file('${param.pid}_editor')">save file</button>
    <button class="xsm_button coral" onclick="Gui3dViewer.recalculate('${param.pid}_editor')">recalculate</button>
    `
  },
  highlight: function(pid) {
    gid(`${pid}_editor`).innerHTML = gid(`${pid}_editor`).innerHTML.replace(/<br>/g, '\n');
    hljs.highlightAll()
  },

  send: function(pid) {
    const text = gid(`${pid}_editor`).innerText;
    hermes.send(pid, text);
  },
  init: function(param) {
    hermes.p[param.pid] = function (pid, data) {
      gid(`${pid}_editor`).innerHTML = data;
      hljs.highlightAll();
      Gui3dViewer.recalculate(`${pid}_editor`);
    }
    hljs.highlightAll();
    DDD_viewer.recalculate(gid(`${param.pid}_editor`).innerText);

    document.getElementById(`${param.pid}_file_input`).addEventListener('change', function (event) {
      const fileInput = event.target;
      
      if (fileInput.files.length > 0) {
        const selectedFile = fileInput.files[0];
        // Read the file content
        const reader = new FileReader();
        reader.onload = function (e) {
          const fileContent = e.target.result;
          document.getElementById(`${param.pid}_editor`).innerHTML = fileContent;
          hljs.highlightAll();
        };
        reader.readAsText(selectedFile);
      }
    });
  },
  save_file: function(target) {
    // Prompt for a filename
    const fileName = prompt('Enter a filename: extension already ".evzr"');
    
    if (fileName) {
      const fileContent = document.getElementById(target).innerText;

      const blob = new Blob([fileContent], { type: 'text/plain' });
      const blobUrl = URL.createObjectURL(blob);

      const a = document.createElement('a');
      a.href = blobUrl;

      a.download = fileName + '.evzr';

      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);

      URL.revokeObjectURL(blobUrl);
    }
  },
  recalculate: function (target) {
    DDD_viewer.recalculate(gid(target).innerText)
  },
}
constructors["Gui3dViewer"] = Gui3dViewer

var GuiRotatableCamera = {
  getHTML: function(param){
    return `
<div class="parameter" style="width:500px; height:675px">
  <h3>${param.name}</h3>
  <button class="xsm_button green" onclick="GuiRotatableCamera.show_crosshair(${param.pid}, 'visible')">show crosshair</button>
  <button class="xsm_button red" onclick="GuiRotatableCamera.show_crosshair(${param.pid}, 'hidden')">hide crosshair</button>
  <button class="xsm_button pink" onclick="reload_cam('${param.pid}')">reload camera</button>
  <table><tr><td>current rotation: </td><td id="${param.pid}_deg" style="width:40px">0</td><td>camera location</td><td id="cam_loc">${param.url}</td></tr></table>
  <div style="width: 95%;" class="slide_container parameter">deg offset<input type="range" min="0" max="359" value="0" class="slider" oninput="GuiRotatableCamera.rotate_cam(${param.pid}, this)" id="${param.pid}_slider"></div>
  <img id="${param.pid}" src="${param.url}" height="480" width="480" title="Iframe Example" style="transform:rotate(0deg); object-fit:none; border-radius:50%;">
  <img id="${param.pid}_crosshair" src="crosshair.png" style="position:relative; left: 140px; bottom: 347px; height:200px; width:200px">
</div>
`
  },
  rotate_cam: function (pid, slider){
    // hermes.send(pid, slider.value)
    document.getElementById(`${pid}_deg`).innerText = slider.value;
    document.getElementById(`${pid}`).style.transform = `rotate(${slider.value}deg)`;
  },
  reload_cam: function (){
    console.log('reloading cam');
    document.getElementById(`${pid}`).src = "http://10.203.136.47/video";
  },
  show_crosshair: function (pid, show){
    document.getElementById(`${pid}_crosshair`).style.visibility = show;  
  }
  
}
constructors["GuiRotatableCamera"] = GuiRotatableCamera

var GuiPnpFeeder = {
  getHTML: function(param) {

return `
<div style="max-width: 750px;" class="parameter">
  <h3>${param.name}</h3>
<table style="width: 100%;" id="${param.pid}_table">
<tr>
<td>feeder_num</td>
<td>Component Name</td>
<td>theta pos</td>
<td>phi pos</td>
<td>z pos</td>
<td>a pos</td>
<td>set pos</td>
</tr>
${this.create_feeder_table(param)}
</table>
<button class="xsm_button green" onclick="GuiPnpFeeder.send(${param.pid}, 'save_rack', null)">save</button>
</div>
`
  },
  create_feeder_table: function(param) {
    let rows = [];
    for (let i=0; i < param.num_feeders; i++) {
      rows.push(`
        <tr>
          <td>feeder: ${i}</td>
          <td><input type="text" style="width: 100%;" id="${param.pid}_val" value="${i}_bbb"></td>
          <td><input type="number" style="width: 100%;" id="${param.pid}_tpos"></td>
          <td><input type="number" style="width: 100%;" id="${param.pid}_ppos"></td>
          <td><input type="number" style="width: 100%;" id="${param.pid}_zpos"></td>
          <td><input type="number" style="width: 100%;" id="${param.pid}_apos"></td>
          <td><button class="xsm_button blue" onclick="GuiPnpFeeder.send(${param.pid}, 'set', ${i})">set</button></td>
          <td><button class="xsm_button green" onclick="GuiPnpFeeder.send(${param.pid}, 'feed', ${i})">feed</button></td>
        </tr>`)
    }
    return rows.join('');
  },
  get_data: function(pid) {
    let table = gid(`${pid}_table`)
    let data = {};
    for (let i = 0; i < table.rows.length; i++) {
      if (i == 0) {continue};
      const row = table.rows[i];
      const val = row.cells[1].querySelector('input').value;
      data[val] = {
        "id": i-1,
        "x": row.cells[2].querySelector('input').value,
        "y": row.cells[3].querySelector('input').value,
        "z": row.cells[4].querySelector('input').value,
        "a": row.cells[5].querySelector('input').value,
      }
    }
    console.log(data);
    return data
  },
  set_all: function(pid, data) {
    let table = gid(`${pid}_table`)
    for (component in data) {
      const comp = data[component]
      const row = table.rows[comp.id + 1]
      row.cells[1].querySelector('input').value = component
      row.cells[2].querySelector('input').value = comp.x
      row.cells[3].querySelector('input').value = comp.y
      row.cells[4].querySelector('input').value = comp.z
      row.cells[5].querySelector('input').value = comp.a
    }
  },
  send: function(pid, action, payload) {
    data = {};
    if (action == 'feed') {
      data['feed'] = payload;
    }
    else if (action == 'save_rack') {
      data['save_rack'] = this.get_data(pid);
    }
    else if (action == 'set') {
      data['set'] = payload;
    }
    hermes.send_json(pid, data);
  },
  set_feeder: function(pid, data) {
    let table = gid(`${pid}_table`)
    for (component in data) {
      const row = table.rows[data.feeder + 1]
      row.cells[2].querySelector('input').value = data.x
      row.cells[3].querySelector('input').value = data.y
      row.cells[4].querySelector('input').value = data.z
      row.cells[5].querySelector('input').value = data.a
    }
  },

  init: function(param) {
    this.set_all(param.pid, param.rack)
    hermes.p[param.pid] = function (pid, data) {
      data = JSON.parse(data);
      if (data['cmd'] == 'set_feeder') {
        console.log(data)
        GuiPnpFeeder.set_feeder(pid, data)
      }
    }
  },
}
constructors["GuiPnpFeeder"] = GuiPnpFeeder

var GRBLScara = {
  getHTML: function(param) {
    return `
    <div style="max-width: 750px;" class="parameter">
    <h3>${param.name}</h3>
    <div id="${param.pid}_tabs">
      <button class="xsm_button green" onclick="GRBLScara.tabs(event, ${param.pid}, 'machine')">Machine</button>
      <button class="xsm_button blue" onclick="GRBLScara.tabs(event, ${param.pid}, 'work_offsets')">Work Offsets</button>
      <button class="xsm_button blue" onclick="GRBLScara.tabs(event, ${param.pid}, 'tool_offsets')">Tool Offsets</button>
      <button class="xsm_button blue" onclick="GRBLScara.tabs(event, ${param.pid}, 'term_tab')">Terminal</button>
    </div>
    <div id="${param.pid}_term_tab" style="display: none">
      <div><label class="checkbox_container">show status messages<input id="${param.pid}_show_status" type="checkbox"><span
            class="checkmark"></span></label></div>
      <div id="${param.pid}_terminal" class="terminal"></div>
      <div id="${param.pid}_input" class="term_input" contenteditable="true"></div>
      <span style="font-size: 12px; color: grey;">please note this terminal is a direct line to GRBL. It is NOT for python
        code input. please use regular terminal for that. </span><br><br>
    </div>
    <div id="${param.pid}_machine" style="display: block">
      <div style="width: 95%;">
        <table style="width: 100%;">
          <tr>
            <td colspan="2">Move Machine:</td>
            <td>Position</td>
            <td>Offset</td>
            <td>Absolute Pos</td>
            <td colspan="2">Encoders</td>
          </tr>
          <tr>
            <td style="width: 5px;"><strong>x: </strong></td>
            <td><input type="number" style="width: 100%;" id="${param.pid}move_x"></td>
            <td>
              <div id="${param.pid}_xpos">None</div>
            </td>
            <td>
              <div id="${param.pid}_xoffset">None</div>
            </td>
            <td>
              <div id="${param.pid}_xabs">None</div>
            </td>
            <td style="width: 5px;">Theta:</td>
            <td>
              <div id="${param.pid}_theta_enc">None</div>
            </td>
          </tr>
          <tr>
            <td><strong>y: </strong></td>
            <td><input type="number" style="width: 100%;" id="${param.pid}move_y"></td>
            <td>
              <div id="${param.pid}_ypos">None</div>
            </td>
            <td>
              <div id="${param.pid}_yoffset">None</div>
            </td>
            <td>
              <div id="${param.pid}_yabs">None</div>
            </td>
            <td>Phi:</td>
            <td>
              <div id="${param.pid}_phi_enc">None</div>
            </td>
          </tr>
          <tr>
            <td><strong>z: </strong></td>
            <td><input type="number" style="width: 100%;" id="${param.pid}move_z"></td>
            <td>
              <div id="${param.pid}_zpos">None</div>
            </td>
            <td>
              <div id="${param.pid}_zoffset">None</div>
            </td>
            <td>
              <div id="${param.pid}_zabs">None</div>
            </td>
          </tr>
          <tr>
            <td style="width: 5px;"><strong>a: </strong></td>
            <td><input type="number" style="width: 100%;" id="${param.pid}move_a"></td>
            <td>
              <div id="${param.pid}_apos">None</div>
            </td>
            <td>
              <div id="${param.pid}_aoffset">None</div>
            </td>
            <td>
              <div id="${param.pid}_aabs">None</div>
            </td>
          </tr>
          <tr>
            <td><strong>b: </strong></td>
            <td><input type="number" style="width: 100%;" id="${param.pid}move_b"></td>
            <td>
              <div id="${param.pid}_bpos">None</div>
            </td>
            <td>
              <div id="${param.pid}_boffset">None</div>
            </td>
            <td>
              <div id="${param.pid}_babs">None</div>
            </td>
          </tr>
          <tr>
            <td><strong>c: </strong></td>
            <td><input type="number" style="width: 100%;" id="${param.pid}move_c"></td>
            <td>
              <div id="${param.pid}_cpos">None</div>
            </td>
            <td>
              <div id="${param.pid}_coffset">None</div>
            </td>
            <td>
              <div id="${param.pid}_cabs">None</div>
            </td>
          </tr>
          <tr>
            <td><strong>feed: </strong></td>
            <td><input type="number" style="width: 100%;" id="${param.pid}move_f" value="500"></td>
            <td>
              <div id="${param.pid}_state">Status: None</div>
            </td>
            <td>
              <div id="${param.pid}_offset_name">Name: None</div>
            </td>
            <td>
              <div id="${param.pid}_blinker"
                style="height:15px; width:15px; background-color: rgb(11, 111, 93); border: 1px solid black; border-radius: 8px;">
                &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsphbt</div>
            </td>
          </tr>
        </table>
      </div>
      <button id="${param.pid}move_submit"
      onclick="hermes.send_json(${param.pid}, {'cmd': 'move.linear', 'x': gid('${param.pid}move_x').value, 'y': gid('${param.pid}move_y').value, 'z': gid('${param.pid}move_z').value, 'a': gid('${param.pid}move_a').value, 'b': gid('${param.pid}move_b').value, 'c': gid('${param.pid}move_c').value, 'feed':gid('${param.pid}move_f').value})"
      class="sm_button green">Move</button><br>
    </div>
    
    <div id="${param.pid}_work_offsets" style="display: none">
      <div style="width: 95%;">
        <table id="${param.pid}_work_offsets_table" style="width: 100%;">
          <tr>
            <td>offset:</td>
            <td>Name</td>
            <td>X</td>
            <td>Y</td>
            <td>Z</td>
            <td>rot</td>
          </tr>
          <tr>
            <td>0</td>
            <td><input type="text"></td>
            <td style="min-width:55px;"></td>
            <td style="min-width:55px;"></td>
            <td style="min-width:55px;"></td>
            <td style="min-width:55px;"></td>
            <td><button class="xsm_button blue" onclick="GRBLScara.send(${param.pid}, 'req_w_offset', 0)">set</button></td>
          </tr>
          <tr>
            <td>1</td>
            <td><input type="text"></td>
            <td style="min-width:55px;"></td>
            <td style="min-width:55px;"></td>
            <td style="min-width:55px;"></td>
            <td style="min-width:55px;"></td>
            <td><button class="xsm_button blue" onclick="GRBLScara.send(${param.pid}, 'req_w_offset', 1)">set</button></td>
          </tr>
          <tr>
            <td>2</td>
            <td><input type="text"></td>
            <td style="min-width:55px;"></td>
            <td style="min-width:55px;"></td>
            <td style="min-width:55px;"></td>
            <td style="min-width:55px;"></td>
            <td><button class="xsm_button blue" onclick="GRBLScara.send(${param.pid}, 'req_w_offset', 2)">set</button></td>
          </tr>
          <tr>
            <td>3</td>
            <td><input type="text"></td>
            <td style="min-width:55px;"></td>
            <td style="min-width:55px;"></td>
            <td style="min-width:55px;"></td>
            <td style="min-width:55px;"></td>
            <td><button class="xsm_button blue" onclick="GRBLScara.send(${param.pid}, 'req_w_offset', 3)">set</button></td>
          </tr>
          <tr>
            <td>4</td>
            <td><input type="text"></td>
            <td style="min-width:55px;"></td>
            <td style="min-width:55px;"></td>
            <td style="min-width:55px;"></td>
            <td style="min-width:55px;"></td>
            <td><button class="xsm_button blue" onclick="GRBLScara.send(${param.pid}, 'req_w_offset', 4)">set</button></td>
          </tr>
          <tr>
            <td>5</td>
            <td><input type="text"></td>
            <td style="min-width:55px;"></td>
            <td style="min-width:55px;"></td>
            <td style="min-width:55px;"></td>
            <td style="min-width:55px;"></td>
            <td><button class="xsm_button blue" onclick="GRBLScara.send(${param.pid}, 'req_w_offset', 5)">set</button></td>
          </tr>
            
        </table>
      </div>
    </div>
  
    <div id="${param.pid}_tool_offsets" style="display: none">
      <div style="width: 95%;">
        <h3>Coming Soon</h3>
      </div>
    </div>
  
    
    <hr>
  
    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'disable_motors'})"
      class="sm_button red">disable_motors</button>
    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'enable_motors'})"
      class="sm_button green">enable_motors</button>
    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'unlock'})" class="sm_button blue">unlock</button>
    <hr>
    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'home_x'})" class="sm_button blue">home_theta</button>
    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'home_y'})" class="sm_button blue">home_phi</button>
    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'home_z'})" class="sm_button blue">home_z</button>
    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'home_a'})" class="sm_button blue">home_a</button>
    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'home_b'})" class="sm_button blue">home_b</button>
    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'home_c'})" class="sm_button blue">home_c</button><br>
    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'reset_x'})" class="sm_button coral">reset_theta</button>
    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'reset_y'})" class="sm_button coral">reset_phi</button>
  
    <hr>
    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'listdir'})" class="sm_button coral">listdir</button>
    run script: <input style="width: 50%;" id="${param.pid}_script">
    <button onclick="hermes.send_json(${param.pid}, {'cmd': 'run', 'script': gid('${param.pid}_script').value})"
      class="sm_button blue">open file</button>
  </div>    `
  },
  init: function(param) {
    hermes.p[param.pid] = function (pid, data) {  // register functions with hermes
      const msg = JSON.parse(data);
      if (msg.cmd == 'post') {
        Terminal.write(gid(`${pid}_terminal`), msg.data);
      }
      else if (msg.cmd == 'status') {
        gid(`${param.pid}_xpos`).innerHTML = msg.x;
        gid(`${param.pid}_ypos`).innerHTML = msg.y;
        gid(`${param.pid}_zpos`).innerHTML = msg.z;
        gid(`${param.pid}_apos`).innerHTML = msg.a;
        gid(`${param.pid}_bpos`).innerHTML = msg.b;
        gid(`${param.pid}_cpos`).innerHTML = msg.c;
        gid(`${param.pid}_theta_enc`).innerHTML = msg.theta_enc;
        gid(`${param.pid}_phi_enc`).innerHTML = msg.phi_enc;
        gid(`${param.pid}_state`).innerHTML = `Status: ${msg.state}`;
        if (gid(`${param.pid}_blinker`).style.backgroundColor != "rgb(12, 19, 17)") {
          gid(`${param.pid}_blinker`).style.backgroundColor = "rgb(12, 19, 17)";
        }
        else {gid(`${param.pid}_blinker`).style.backgroundColor = "rgb(18, 48, 43)";}
        if (gid(`${param.pid}_show_status`).checked == true) {
          Terminal.write(gid(`${pid}_terminal`), JSON.stringify(msg));
        }
      }
      // else if (msg.cmd == 'set_offset') {
      //   gid(`${param.pid}_xoffset`).innerHTML = msg.x;
      //   gid(`${param.pid}_yoffset`).innerHTML = msg.y;
      //   gid(`${param.pid}_zoffset`).innerHTML = msg.z;
      //   gid(`${param.pid}_name`).innerHTML = `Name: ${msg.name}`;
      // }
      else if (msg.cmd == 'set_w_offset') {
        console.log(msg.data);
        let table = gid(`${param.pid}_work_offsets_table`)
        console.log(table.rows)
        console.log(msg.data.off_id)
        const row = table.rows[msg.data.off_id + 1];
        console.log(row)
        row.cells[2].innerHTML = msg.data.mpos.x
        row.cells[3].innerHTML = msg.data.mpos.y
        row.cells[4].innerHTML = msg.data.mpos.z
        row.cells[5].innerHTML = msg.data.mpos.a
      }
    };
    Terminal.init(param, true);  // initialize the terminal
  },
  send: function(pid, cmd, payload) {
    if (cmd == 'req_w_offset') {
      // this function will send a request to main to get machine position 
      // and return another value to actually 
      let table = gid(`${pid}_work_offsets_table`)
      let name = table.rows[payload + 1].cells[1].querySelector('input').value
      let data = {
        cmd: 'req_w_offset',
        off_id: payload,
        name: name
      }
      hermes.send_json(pid, data);
    }

    
  },
  tabs: function(event, pid, tab_name) {
    let buttons = document.getElementById(`${pid}_tabs`).children;
    for (var i=0; i<buttons.length; i++) {
      let button = buttons[i]; 
      if (button.classList.contains('green')) {
        console.log(button)
        button.classList.remove('green');
        button.classList.add('blue');
      }  
    }
    event.target.classList.remove('blue');
    event.target.classList.add('green');

    machine = gid(`${pid}_machine`);
    work_offsets = gid(`${pid}_work_offsets`);
    tool_offsets = gid(`${pid}_tool_offsets`);
    term_tab = gid(`${pid}_term_tab`);
    
    machine.style.display = "none";      
    work_offsets.style.display = "none";      
    tool_offsets.style.display = "none";      
    term_tab.style.display = "none";      
    
    if (tab_name == 'machine') {machine.style.display = "block";}
    else if (tab_name == 'work_offsets') {work_offsets.style.display = "block";}
    else if (tab_name == 'tool_offsets') {tool_offsets.style.display = "block";}
    else if (tab_name == 'term_tab') {term_tab.style.display = "block";}
  }
}
constructors["GRBLScara"] = GRBLScara

var GRBL = {
  getHTML: function(param) {
    return `
  <div style="max-width: 700px" class="parameter">
  <h3>${param.name}</h3>
  <div id="${param.pid}_terminal" class="terminal"></div>
  <div id="${param.pid}_input" class="term_input" contenteditable="true"></div>

  <div style="display: flex">
  <div style="width: 95%;">
    <table style="width: 100%;">
    <tr><td colspan="2">Move Machine:</td><td>Position</td><td>Offset</td><td>Absolute Pos</td></tr>
    <tr>
      <td style="width: 5px;"><strong>x: </strong></td>
      <td><input type="number" style="width: 100%;" id="${param.pid}move_x"></td>
      <td><div id="${param.pid}_xpos">None</div></td>
      <td><div id="${param.pid}_xoffset">None</div></td>
      <td><div id="${param.pid}_xabs">None</div></td>
    </tr>
    <tr>
      <td><strong>y: </strong></td>
      <td><input type="number" style="width: 100%;" id="${param.pid}move_y"></td>
      <td><div id="${param.pid}_ypos">None</div></td>
      <td><div id="${param.pid}_yoffset">None</div></td>
      <td><div id="${param.pid}_yabs">None</div></td>
    </tr>
    <tr>
      <td><strong>z: </strong></td>
      <td><input type="number" style="width: 100%;" id="${param.pid}move_z"></td>
      <td><div id="${param.pid}_zpos">None</div></td>
      <td><div id="${param.pid}_zoffset">None</div></td>
      <td><div id="${param.pid}_zabs">None</div></td>
    </tr>
    <tr>
      <td style="width: 5px;"><strong>a: </strong></td>
      <td><input type="number" style="width: 100%;" id="${param.pid}move_a"></td>
      <td><div id="${param.pid}_apos">None</div></td>
      <td><div id="${param.pid}_aoffset">None</div></td>
      <td><div id="${param.pid}_aabs">None</div></td>
    </tr>
    <tr>
      <td><strong>b: </strong></td>
      <td><input type="number" style="width: 100%;" id="${param.pid}move_b"></td>
      <td><div id="${param.pid}_bpos">None</div></td>
      <td><div id="${param.pid}_boffset">None</div></td>
      <td><div id="${param.pid}_babs">None</div></td>
    </tr>
    <tr>
      <td><strong>c: </strong></td>
      <td><input type="number" style="width: 100%;" id="${param.pid}move_c"></td>
      <td><div id="${param.pid}_cpos">None</div></td>
      <td><div id="${param.pid}_coffset">None</div></td>
      <td><div id="${param.pid}_cabs">None</div></td>
    </tr>
    <tr>
      <td><strong>feed: </strong></td>
      <td><input type="number" style="width: 100%;" id="${param.pid}move_f" value="500"></td>
      <td><div id="${param.pid}_state">Status: None</div></td>
      <td><div id="${param.pid}_offset_name">Name: None</div></td>
      <td><div id="${param.pid}_blinker" style="height:15px; width:15px; background-color: rgb(11, 111, 93); border: 1px solid black; border-radius: 8px;">&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsphbt</div></td>
    </tr>
    </table>
  </div>

  </div>

    <button id="${param.pid}move_submit" onclick="hermes.send_json(${param.pid}, {'cmd': 'move.linear', 'x': gid('${param.pid}move_x').value, 'y': gid('${param.pid}move_y').value, 'z': gid('${param.pid}move_z').value, 'feed':gid('${param.pid}move_f').value})" class="sm_button green">Move</button>
  <hr>
  
  <button onclick="hermes.send_json(${param.pid}, {'cmd': 'disable_motors'})" class="sm_button red">disable_motors</button>
  <button onclick="hermes.send_json(${param.pid}, {'cmd': 'enable_motors'})" class="sm_button green">enable_motors</button><br>
  <button onclick="hermes.send_json(${param.pid}, {'cmd': 'unlock'})" class="sm_button blue">unlock</button>
  <hr>
  <button onclick="hermes.send_json(${param.pid}, {'cmd': 'home_x'})" class="sm_button blue">home_x</button>
  <button onclick="hermes.send_json(${param.pid}, {'cmd': 'home_y'})" class="sm_button blue">home_y</button>
  <button onclick="hermes.send_json(${param.pid}, {'cmd': 'home_z'})" class="sm_button blue">home_z</button>
  <button onclick="hermes.send_json(${param.pid}, {'cmd': 'home_a'})" class="sm_button blue">home_a</button>
  <button onclick="hermes.send_json(${param.pid}, {'cmd': 'home_b'})" class="sm_button blue">home_b</button>
  <button onclick="hermes.send_json(${param.pid}, {'cmd': 'home_c'})" class="sm_button blue">home_c</button>
  <hr>
  <button onclick="hermes.send_json(${param.pid}, {'cmd': 'listdir'})" class="sm_button coral">listdir</button>
  run script: <input style="width: 50%;" id="${param.pid}_script">
  <button onclick="hermes.send_json(${param.pid}, {'cmd': 'run', 'script': gid('${param.pid}_script').value})" class="sm_button blue">open file</button>
  </div>`
  },
  init: function(param) {
    // on init we hand a function off to hermes, when our pid is found she will route the message to that function
    hermes.p[param.pid] = function (pid, data) {
      const msg = JSON.parse(data);
      if (msg.cmd == 'post') {
        Terminal.write(gid(`${pid}_terminal`), msg.data);
      }
      else if (msg.cmd == 'status') {
        gid(`${param.pid}_xpos`).innerHTML = msg.x;
        gid(`${param.pid}_ypos`).innerHTML = msg.y;
        gid(`${param.pid}_zpos`).innerHTML = msg.z;
        gid(`${param.pid}_state`).innerHTML = `Status: ${msg.state}`;
        if (gid(`${param.pid}_blinker`).style.backgroundColor != "rgb(12, 19, 17)") {
          gid(`${param.pid}_blinker`).style.backgroundColor = "rgb(12, 19, 17)";
        }
        else {gid(`${param.pid}_blinker`).style.backgroundColor = "rgb(18, 48, 43)";}
      }
      else if (msg.cmd == 'set_offset') {
        gid(`${param.pid}_xoffset`).innerHTML = msg.x;
        gid(`${param.pid}_yoffset`).innerHTML = msg.y;
        gid(`${param.pid}_zoffset`).innerHTML = msg.z;
        gid(`${param.pid}_name`).innerHTML = `Name: ${msg.name}`;
      }
    }
  }
}
constructors["GRBL"] = GRBL

var FileSender = {
  getHTML: function(param){
    return `
<div class="parameter" style="max-width: 500px">
  <h3>${param.name}</h3>
  <label for="${param.pid}_file">progress:</label>
  <progress id="${param.pid}_file" value="0" max="100">klsdjf;lsdkjfsd</progress><br>
  <label>local filename<label>
  <input type="text" style="width: 100%;" id="${param.pid}_local_filename" value="test.py">
  <label>remote adr<label>
  <input type="number" style="width: 100%;" id="${param.pid}_adr" value="10">
  <label>remote pid<label>
  <input type="number" style="width: 100%;" id="${param.pid}_pid" value="65000">
  <label>remote filename<label>
  <input type="text" style="width: 100%;" id="${param.pid}_remote_filename" value="testing.py">
  <button class="xsm_button green" onclick="hermes.send_json(${param.pid}, {'remote_adr': gid('${param.pid}_adr').value, 'remote_pid': gid('${param.pid}_pid').value, 'remote_filename': gid('${param.pid}_remote_filename').value, 'local_filename': gid('${param.pid}_local_filename').value})">Send</button>
</div>
`
  },
  init: function(param) {
    hermes.p[param.pid] = function (pid, data) {
      gid(`${pid}_file`).value = data;
    }
  }
}
constructors["FileSender"] = FileSender

var Pcf8563 = {
  getHTML: function(param){
    return `
    <div class="parameter">
    <h3>${param.name}</h3>
    <div id="Pcf8563_currentTime"></div><br>
    <div id="${param.pid}_ts"></div><br>
    alarm: <span id="${param.pid}_alarm"></span><br>
    state: <span id="${param.pid}_state"></span><br>
    current alarm: <span id="${param.pid}_current"></span><br>
    <div id="${param.pid}_error"></div>
    <label for="${param.pid}_callback">callback</label>
    <input style="width:50%" type="text" id="${param.pid}_callback" value="pass"><br>
    <label for="${param.pid}_datetimeInput">Select a date and time:</label>
    <input style="width:50%" type="datetime-local" id="${param.pid}_datetimeInput">
    
    <button onclick="Pcf8563.add_abs_alarm(${param.pid})">Absolute Alarm</button>
    <br><br>
    Add A Relative Alarm: Alarm Time will be added to Current Time<br>
    <form id="${param.pid}_timeForm" onsubmit="return Pcf8563.add_rel_alarm(${param.pid})">
        <label for="days">Days:</label>
        <input style="width:100px" type="number" id="days" min="0" value="0">
        <label for="hours">Hours:</label>
        <input style="width:100px" type="number" id="hours" min="0" value="0">
        <label for="minutes">Minutes:</label>
        <input style="width:100px" type="number" id="minutes" min="0" max="59" value="0">
        <button type="submit">Relative Alarm</button>
    </form>

    <h4>Current Alarms</h4>
    <div style="border: 2px solid black; border-radius:5px; padding: 5px; width:fit-content" id="${param.pid}_alarms"></div>
    <button onclick="Pcf8563.clear_alarms(${param.pid})">Clear All Alarms</button>
</div>    
`
  },
  pid: 0,
  init: function(param) {
    this.pid = param.pid;
    
    // Update current time every second
    setInterval(this.updateCurrentTime, 1000);
    
    Pcf8563.add_all_alarms(param.pid, param.alarms, param.current);

    hermes.p[param.pid] = function (pid, data) {
      const msg = JSON.parse(data);
      if (msg.cmd == 'status') {
        gid(`${pid}_ts`).innerHTML = msg.ts;
        if (msg.alarm){
          gid(`${pid}_alarm`).innerHTML = 'on';
        }
        else{
          gid(`${pid}_alarm`).innerHTML = 'off';
        }
        if (msg.state){
          gid(`${pid}_state`).innerHTML = 'on';
        }
        else{
          gid(`${pid}_state`).innerHTML = 'off';
        }
      }
      else if (msg.cmd == 'ts'){
        gid(`${pid}_ts`).innerHTML = msg.ts;
      }
      else if (msg.cmd == 'alarms'){
        Pcf8563.add_all_alarms(pid, msg.alarms, msg.current);
      }
    }
  },
  clear_alarms: function(pid){
    cmd = {cmd: 'clear_alarms'}
    hermes.send_json(pid, cmd)
  },
  add_all_alarms: function(pid, alarms, current){
    console.log('adding alarms');
    gid(`${pid}_current`).innerHTML = current;
    gid(`${pid}_alarms`).innerHTML = "";
    for (let alarm of alarms){
      Pcf8563.addAlarm(pid, alarm)
    }
  },
  // Function to format datetime as required by the input
  formatDatetimeForInput: function(datetime) {
    var year = datetime.getFullYear();
    var month = ('0' + (datetime.getMonth() + 1)).slice(-2); // Months are zero-based
    var day = ('0' + datetime.getDate()).slice(-2);
    var hours = ('0' + datetime.getHours()).slice(-2);
    var minutes = ('0' + datetime.getMinutes()).slice(-2);
    return year + month + day + hours + minutes;
  },
  // Function to update the current time continuously
  updateCurrentTime: function () {
    var currentTimeDiv = gid(`Pcf8563_currentTime`)
    var now = new Date();
    var month = ('0' + (now.getMonth() + 1)).slice(-2); // Months are zero-based
    var day = ('0' + now.getDate()).slice(-2);
    var year = now.getFullYear();
    var hours = ('0' + now.getHours()).slice(-2);
    var minutes = ('0' + now.getMinutes()).slice(-2);
    var seconds = ('0' + now.getSeconds()).slice(-2);
    var currentTimeString = 'Current Time: ' + month + '/' + day + '/' + year + ' ' + hours + ':' + minutes + ':' + seconds;
    currentTimeDiv.textContent = currentTimeString;
  },
  please_wait: function(pid){
    document.getElementById(`${pid}_alarms`).innerHTML = "Getting alarms<br> please wait";
  },
  timestamp2date: function(timestamp){
    var year = parseInt(timestamp.slice(0, 4), 10);
    var month = parseInt(timestamp.slice(4, 6), 10) - 1; // Months are zero-indexed
    var day = parseInt(timestamp.slice(6, 8), 10);
    var hour = parseInt(timestamp.slice(8, 10), 10);
    var minute = parseInt(timestamp.slice(10, 12), 10);
    return new Date(year, month, day, hour, minute);
  },
  date2timestamp: function(date){
    var year = date.getFullYear();
    var month = ('0' + (date.getMonth() + 1)).slice(-2); // Months are zero-indexed
    var day = ('0' + date.getDate()).slice(-2);
    var hour = ('0' + date.getHours()).slice(-2);
    var minute = ('0' + date.getMinutes()).slice(-2);
    return year + month + day + hour + minute;
  },
  add_rel_alarm: function(pid) {
    var days = parseInt(document.getElementById('days').value, 10);
    var hours = parseInt(document.getElementById('hours').value, 10);
    var minutes = parseInt(document.getElementById('minutes').value, 10);
    var date = document.getElementById(`${pid}_ts`).innerText;
    let now = this.timestamp2date(date)
    now.setDate(now.getDate() + days);
    now.setHours(now.getHours() + hours);
    now.setMinutes(now.getMinutes() + minutes);
    let timestamp = this.date2timestamp(now);
    let callback = document.getElementById(`${pid}_callback`).value;
    let alarm = timestamp+callback
    hermes.send_json(pid,{cmd: "add_alarm", alarm:alarm})
    return false;
  },

  add_abs_alarm: function(pid) {
    var date = document.getElementById(`${pid}_datetimeInput`).value;
    let callback = document.getElementById(`${pid}_callback`).value;
    const charactersToRemove = /[-:T]/g;
    let alarm = date.replace(charactersToRemove, "") + callback;
    hermes.send_json(pid,{cmd: "add_alarm", alarm:alarm})
  },
  delete: function(pid, button){
    let alarm = button.previousSibling.data;
    hermes.send_json(pid, {cmd: 'delete', alarm: alarm}) 
    this.please_wait(pid)
  },

  eval_change: function(pid, input){
    let timestamp = input.previousSibling.previousSibling;
    hermes.send_json(pid, {cmd: 'eval_change', timestamp: timestamp})
    this.please_wait(pid)
  },

  addAlarm: function(pid, alarm) {
    var alarmsDiv = document.getElementById(`${pid}_alarms`);
    console.log(alarm);
    // var alarmText = this.formatDatetimeForInput(date);

   
    var alarmElement = document.createElement('div');
    alarmElement.textContent = alarm;

    // Create delete button for the alarm
    var deleteButton = document.createElement('button');
    deleteButton.textContent = 'Delete';
    deleteButton.onclick = function() {
      Pcf8563.delete(pid, this)
    };
    alarmElement.appendChild(deleteButton);

    // var evalElement = document.createElement('input');
    // evalElement.style.width = "200px";
    // evalElement.value = alarm.slice(12);
    // evalElement.onchange = function() {
    //   Pcf8563.eval_change(pid, this)
    // }

    // alarmElement.appendChild(evalElement);

    // Add the new alarm to alarms div
    alarmsDiv.appendChild(alarmElement);

    
    // cmd = {cmd: 'set_alarms', alarms: dates}
    // hermes.send_json(pid, cmd)
  }
}
constructors["Pcf8563"] = Pcf8563

var GuiFloat = {
  getHTML: function(param){
    return `
<div class="parameter" style="max-width: 500px">
  ${param.name}
  <input type="number" id="${param.pid}" value="${param.initial_value}" onchange="GuiFloat.send(${param.pid})">
</div>
`
  },
  init: function(param) {
    hermes.p[param.pid] = function (pid, data) {
      gid(`${pid}`).value = data;
    }
  },
  send: function(pid) {
    const val = gid(pid).value
    hermes.send(pid, val)
  }
}
constructors["GuiFloat"] = GuiFloat

var GuiTextbox = {
  getHTML: function(param){
    return `<div class="text_input parameter">${param.name}
    <input type="text" id="${param.pid}" value="${param.initial_value}"  onchange="GuiTextbox.send('${param.pid}')"></div>`;
  },
  init: function(param) {
    hermes.p[param.pid] = function (pid, data) {
      gid(`${pid}`).value = data;
    }
  },
  send: function(pid) {
    const val = gid(pid).value
    hermes.send(pid, val)
  }
}
constructors["GuiTextbox"] = GuiTextbox
      
var GuiSlider = {
  getHTML: function(param){
    return `<div class="slide_container parameter">${param.name}
    <input type="range" min="${param.min}" max="${param.max}" value="${param.initial_value}" class="slider" oninput="hermes.send(${param.pid}, parseInt(this.value))" id="${param.pid}"></div>`
  },
  init: function(param) {
    hermes.p[param.pid] = function (pid, val) {
      var slider = document.getElementById(pid);
      if (slider.value != val) {
          slider.value = val;
          // console.log('slider  ' + slider.value)
      }
    }
  }
}
constructors["GuiSlider"] = GuiSlider

var GuiButton = {
  getHTML: function(param){
    return `<button class="sm_button ${param.color}" onclick="hermes.send(${param.pid}, true)" id="${param.pid}">${param.name}</button>`
  },
  init: function(param) {
    hermes.p[param.pid] = function (pid, val) {
      console.log(`button ${pid} clicked`);
    }
  }
}
constructors["GuiButton"] = GuiButton

var GuiCheckbox = {
  getHTML: function(param){
    var checked = "";
    if (param.initial_value) {
      checked = "checked";
    }
    return `<div class="parameter"><label class="checkbox_container">${param.name}<input id="${param.pid}" type="checkbox" onclick="hermes.send(${param.pid}, this.checked)"${checked}><span class="checkmark"></span></label></div>`
  },
  init: function(param) {
    hermes.p[param.pid] = function (pid, val) {
      let bool;
      // console.log(val)
      if (val == 'True'){bool = true;}
      else {bool = false;}  
      
      document.getElementById(pid).checked = bool;
    }
  }
}
constructors["GuiCheckbox"] = GuiCheckbox

function build_from_json(json){
  // function used by pyscript
  let _json = JSON.parse(json)
  build_params(_json)
}

function build_params(params) {
  parameters.innerHTML = "";
  // var these_params = none;
  for (var i = 0; i < params.length; i++) {
      console.log(params[i])
      build_param(params[i]);
  }
}

function build_param(param) {
  var new_param = document.createElement('div');
  new_param.innerHTML = constructors[param.type].getHTML(param);

  parameters.appendChild(new_param);

  constructors[param.type].init(param);
}
console.log(constructors)

// collapse child divs
function toggleCollapsible(button) {
  var content = button.nextElementSibling;
  // let display = '';
  contents = [];
  contents.push(button.nextElementSibling);
  let current_sib = button.nextElementSibling;
  while (true) {
      next_sib = current_sib.nextElementSibling;
      if (contents.includes(next_sib) || next_sib == null) {
          break;
      }
      else {
          contents.push(next_sib);
          current_sib = next_sib;
      }
  }
  if (content.style.display === 'block' || content.style.display == '') {
      // content.style.display = 'none';
      display = 'none';
      button.innerHTML = '+';
  } else {
      // content.style.display = 'block';
      display = 'block';
  }
  // console.log(contents)
  for (let i = 0; i < contents.length; i++) {
      contents[i].style.display = display;
  }
}

var colorPicker = new KellyColorPicker({
  place: "picker",
});

colorPicker.getWheel().width += 20; // wheel width
colorPicker.getSvFigCursor().radius += 10; // small ring width
colorPicker.getWheelCursor().height += 5; // slider size
colorPicker.resize(340); // overall wheel size

var Socket = new WebSocket("ws://" + window.location.hostname + ":81/");

var is_active = false; // pressed flag

try {
  document.createEvent("touchevent"); //check for touch support

  picker.addEventListener("touchstart", clickdown);
  picker.addEventListener("touchend", clickup);
  picker.addEventListener("touchmove", clickmove);
} catch (e) {
  picker.addEventListener("mousedown", clickdown);
  picker.addEventListener("mouseup", clickup);
  picker.addEventListener("mousemove", clickmove);
}

function clickdown() {
  is_active = true;
}

function clickup() {
  is_active = false;
  document.body.style.background = colorPicker.getCurColorHex();
  var send = colorPicker.getCurColorHex();

  console.log(send);
  Socket.send(send);
}

var lastSend = 0;

function clickmove() {
  if (is_active) {
    document.body.style.background = colorPicker.getCurColorHex();
    var send = colorPicker.getCurColorHex();

    var now = new Date().getTime();
    if (lastSend > now - 20) return; //send at most once every 20 ms
    lastSend = now;

    console.log(send);
    Socket.send(send);
  }
}

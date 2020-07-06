// const roomName = JSON.parse(document.getElementById('room-name').textContent);


function getChatDiv() {
    return document.getElementsByClassName('chat-log')[0];
}

const chatSocket = new WebSocket(
    'ws://'
    + window.location.host
    + '/ws/chat'
);

chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data);
    getChatDiv().innerHTML += ('<p>' + data.message + '</p>');
};

chatSocket.onclose = function(e) {
    console.error('Chat socket closed unexpectedly');
};

document.querySelector('#chat-message-input').focus();
document.querySelector('#chat-message-input').onkeyup = function(e) {
    if (e.keyCode === 13) {  // enter, return
        document.querySelector('#chat-message-submit').click();
    }
};

document.querySelector('#chat-message-submit').onclick = function(e) {
    const messageInputDom = document.querySelector('#chat-message-input');
    const message = messageInputDom.value;
    chatSocket.send(JSON.stringify({
        'message': message
    }));
    messageInputDom.value = '';
    dst = getChatDiv();
    dst.scrollTop = dst.scrollHeight;
};

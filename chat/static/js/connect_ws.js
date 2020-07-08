let onlineUsers = new Map()


function showOnlineUsers() {
    getOnlineDiv().innerHTML = ''
    for (const [user, html] of onlineUsers.entries()) {
        getOnlineDiv().innerHTML += html;
    }
}


function getChatDiv() {
    return document.getElementsByClassName('chat-log')[0]
}

function addMessage(data) {
    getChatDiv().innerHTML += wrapMessage(data)
}

function getOnlineDiv() {
    return document.getElementsByClassName('chat-online')[0]
}


function scrollDown() {
    let dst = getChatDiv()
    dst.scrollTop = dst.scrollHeight
}


function wrapMessage(data) {
    return `<div class="chat-message"><b>${data.author}</b>: ${data.message}</div>`
}


function initChatHistory(event) {
    event.data.forEach(msg => addMessage(msg))
    dst = getChatDiv()
    dst.scrollTop = dst.scrollHeight
}


function initOnlineUsers(event) {
    event.data.forEach(user => onlineUsers.set(user.user, wrapOnlineUser(user)))
    showOnlineUsers()
}


function onlineConnect(event) {
    onlineUsers.set(event.user, wrapOnlineUser(event))
    showOnlineUsers()
}

function onlineDisconnect(event) {
    onlineUsers.delete(event.user)
    showOnlineUsers()
}


function wrapOnlineUser(data) {
    return `<div class="user-online">${data.user}</div>`
}

const chatSocket = new WebSocket('ws://' + window.location.host + '/ws/chat')

chatSocket.onmessage = function(e) {
    const data = JSON.parse(e.data)
    console.log(e.data)

    let msg_type = data.type.split('.')

    if (data.type === 'chat.message') {
        addMessage(data)
        scrollDown()
    }

    else if (msg_type[0] === 'init') {
        if      (msg_type[1] === 'chat_history') initChatHistory(data)
        else if (msg_type[1] === 'online_users') initOnlineUsers(data)
    }

    else if (msg_type[0] === 'online') {
        if      (msg_type[1] === 'connect')     onlineConnect(data)
        else if (msg_type[1] === 'disconnect')  onlineDisconnect(data)
    }
};

chatSocket.onclose = function(e) {
    console.error('Chat socket closed unexpectedly')
};

document.querySelector('#chat-message-input').focus()
document.querySelector('#chat-message-input').onkeyup = function(e) {
    if (e.keyCode === 13) {  // enter, return
        document.querySelector('#chat-message-submit').click()
    }
};

document.querySelector('#chat-message-submit').onclick = function(e) {
    const messageInputDom = document.querySelector('#chat-message-input')
    const message = messageInputDom.value
    chatSocket.send(JSON.stringify({
        'message': message
    }));
    messageInputDom.value = ''
};

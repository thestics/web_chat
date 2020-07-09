let onlineUsers = new Map()
const chatSocket = new WebSocket('ws://' + window.location.host + '/ws/chat')
let curUser = null

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

function userMention(event) {
    let x = document.getElementById("snackbar")
    x.className = "show"
    x.innerHTML = `Mentioned by: ${event.by}`
    setTimeout(function () {
        x.className = x.className.replace("show", "")
        x.innerHTML = ''
    }, 3000);
}


function userWhoami(event) {
    curUser = event['user']
}


function wrapOnlineUser(data) {
    return `<div class="user-online">${data.user}</div>`
}


function wrapMessage(data) {
    let outerCls = ''
    if (data.author === curUser)
        outerCls = "chat-message-in"
    else
        outerCls = "chat-message-out"

    return `<div class="${outerCls}">
                <div class="chat-message">
                    <b>${data.author}</b>: ${data.message}
                </div>
            </div>`
}



chatSocket.onmessage = function (e) {
    const data = JSON.parse(e.data)
    console.log(e.data)

    let msg_type = data.type.split('.')

    if (data.type === 'chat.message') {
        addMessage(data)
        scrollDown()
    } else if (msg_type[0] === 'init') {
        if      (msg_type[1] === 'chat_history') initChatHistory(data)
        else if (msg_type[1] === 'online_users') initOnlineUsers(data)
    } else if (msg_type[0] === 'online') {
        if      (msg_type[1] === 'connect')      onlineConnect(data)
        else if (msg_type[1] === 'disconnect')   onlineDisconnect(data)
    } else if (msg_type[0] === 'user') {
        if      (msg_type[1] === 'mention')      userMention(data)
        else if (msg_type[1] === 'whoami')       userWhoami(data)
    }

    if (curUser === null) {
        chatSocket.send(JSON.stringify({"type": "user.whoami"}))
    }
};

function processMessage(message) {
    message = message.slice(0, -1)
    let prepare = obj => JSON.stringify(obj)
    let mentioned = message.matchAll(/(^|\s)@([\w]+)(\s|$)/g)

    for (let match of mentioned) {
        chatSocket.send(prepare({
            "type": "user.mention",
            "name": match[2]
        }))
    }

    chatSocket.send(prepare({
        "type": "chat.message",
        "message": message
    }))
}

chatSocket.onclose = function (e) {
    console.error('Chat socket closed unexpectedly')
};

document.querySelector('#chat-message-input').focus()
document.querySelector('#chat-message-input').onkeyup = function (e) {
    if (e.keyCode === 13) {  // enter, return
        document.querySelector('#chat-message-submit').click()
    }
};

document.querySelector('#chat-message-submit').onclick = function (e) {
    const messageInputDom = document.querySelector('#chat-message-input')
    const message = messageInputDom.value
    processMessage(message)
    messageInputDom.value = ''
};

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

function addServiceMessage(data) {
    getChatDiv().innerHTML += wrapServiceMessage(data)
}

function getOnlineDiv() {
    return document.getElementsByClassName('chat-online')[0]
}


function scrollDown() {
    let dst = getChatDiv()
    dst.scrollTop = dst.scrollHeight
}

function initChatHistory(event) {
    for (let i = 0; i < event.data.length; i++) {
        let isService = event.data[i].service_msg
        let msg = event.data[i]

        if (isService) addServiceMessage(msg)
        else           addMessage(msg)
    }
    dst = getChatDiv()
    dst.scrollTop = dst.scrollHeight
}

/* incoming event handlers */

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
    x.innerHTML = `<b>${event.by}</b>: ${event.message}`
    setTimeout(function () {
        x.className = x.className.replace("show", "")
        x.innerHTML = ''
    }, 3000);
}


function userWhoami(event) {
    curUser = event['user']
}

/* message wrappers */

function wrapOnlineUser(data) {
    return `<div class="user-online">${data.user}</div>`
}


function wrapServiceMessage(data) {
    return `<div class="chat-service-message">${data.message}</div>`
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

    if (msg_type[0] === 'chat') {
        if (msg_type[1] === 'message') {
            addMessage(data)
            scrollDown()
        }
        else if (msg_type[1] === 'servicemessage') {
            addServiceMessage(data)
            scrollDown()
        }
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
}

function processMessage(data) {
    let prepare = obj => JSON.stringify(obj)

    message = data.message.slice(0, -1)
    let mentioned = message.matchAll(/(^|\s)@([\w]+)/gm)

    for (let match of mentioned) {
        chatSocket.send(prepare({
            "type": "user.mention",
            "name": match[2],
            "message": message
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
    processMessage({"type": "chat.message", "message": message})
    messageInputDom.value = ''
};

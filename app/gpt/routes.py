from flask import render_template, request, redirect, url_for, session

from flask_login import current_user, login_required

from app.gpt import bp

from app import socketio

from flask_socketio import send,emit, join_room, leave_room

from app.gpt.openai import Simsimi,Eliza


@bp.route("/chat")
@login_required
def chatbot():
    return render_template('chatbot/index.html')


#客户端连接服务器时，发送session id
@socketio.on('connect')
def handleConnect():
    #向客户端发送事件消息
    send({'sid':request.sid})

#socketio第二次握手连接
@socketio.on('message')
def handleMessage(msg):
    print('server received message:' + request.sid +  msg)
    

#socketio断开连接
@socketio.on('disconnect')
def handleDisconect():
    print()

@socketio.event
def joinRoom(message):
    join_room(message['room'])
    emit('roomJoined',{
        'username':message['username'],
        'room':message['room'],
    },to = message['room'])

@socketio.event
def leaveRoom(message):
    
    emit('roomLeftPersonal',{
        'room':message['room']
    })

    leave_room(message['room'])

    emit('roomLeft',{
        'room':message['room'],
        'username':message['username']
    },to = message['room'])

@socketio.event
def sendMsg(message):

    emit('SendToAll',{
        'msg':message['msg'],
        'username':message['username'],
        'type':'text',
        'sid':message['sid']
    },to = message['room'])

    #Openai
    eliza = Eliza(message['msg'])
    res = eliza.Say()

    emit('SendToAll',res,to = message['room'])
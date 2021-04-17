from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_socketio import SocketIO, emit
import os

msg_char_limit = 1500

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///chat_history.db'
app.config["SECRET_KEY"] = 'secret'

#setting database for chat history
chat_history = SQLAlchemy(app)

class Message(chat_history.Model):
    content = chat_history.Column(chat_history.String(msg_char_limit))
    user = chat_history.Column(chat_history.String(20))
    date = chat_history.Column(chat_history.DateTime, default=datetime.utcnow, primary_key=True)


#socketio
socketio = SocketIO(app)

@socketio.on('message')
def handle_message(msg_list):
    print("received", msg_list)

    #finds if received message is invalid or not
    user_info={}
    user_info['user'] = user = msg_list[0]
    user_info['message'] = msg_input = msg_list[1]
    invalid_cases = [len(msg_input)>msg_char_limit, len(msg_input)==0, type(user)==str and len(user)==0]
    invalid_text = [f"Sua mensagem excede o número máximo de caracteres([msg_char_limit])",
                    "Você não pode enviar uma mensagem em branco",
                    "Você não pode usar um nome de usuário em branco"]

    invalid = False
    for i in range(3):
        if invalid_cases[i]:
            #invalid text will be shown on the html
            user_info["notification"] = invalid_text[i]
            invalid = True
                
    if not invalid:
        #accepts message on database
        new_msg = Message(content=msg_input, user=user)
        user_info["date"] = datetime.utcnow().strftime("%H:%M")
        chat_history.session.add(new_msg)
        chat_history.session.commit()
        
        emit("clear", "")#clear input field if valid msg
        emit("message", user_info, broadcast=True)

@socketio.on('system_msg')
def handle_system_msg(msg):
    print("from system:", msg)
    new_msg = Message(content=msg, user="")
    chat_history.session.add(new_msg)
    chat_history.session.commit()
    msg = f"({datetime.utcnow().strftime('%H:%M')}){msg}"
    emit("system", msg, broadcast=True)


#routing
@app.route('/', methods=["POST", "GET"])
def chat_page():
    #starts html with chat history
    user_info = {}
    history = Message.query.order_by(Message.date).all()
    return render_template('chat.html', history=history, user_info=user_info)

    
#no idea of what this is, just copy and pasted because i was having problems with updating css
@app.context_processor
def override_url_for():
    return dict(url_for=dated_url_for)

def dated_url_for(endpoint, **values):
    if endpoint == 'static':
        filename = values.get('filename', None)
        if filename:
            file_path = os.path.join(app.root_path,
                                 endpoint, filename)
            values['q'] = int(os.stat(file_path).st_mtime)
    return url_for(endpoint, **values)

socketio.run(app, host="0.0.0.0")

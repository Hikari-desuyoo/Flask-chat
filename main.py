from flask import Flask, render_template, url_for, request, redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os

msg_char_limit = 1500

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///chat_history.db'

#setting database for chat history
chat_history = SQLAlchemy(app)

class Message(chat_history.Model):
    content = chat_history.Column(chat_history.String(msg_char_limit))
    user = chat_history.Column(chat_history.String(20))
    date = chat_history.Column(chat_history.DateTime, default=datetime.utcnow, primary_key=True)
            
@app.route('/', methods=["POST", "GET"])
def chat_page():
    user_info = {}
    history = Message.query.order_by(Message.date).all()
    if request.method == 'POST':
        #finds if received message is invalid or not
        user_info['user'] = user = request.form['user']
        user_info['message'] = msg_input = request.form['message']
        invalid_cases = [len(msg_input)>msg_char_limit, len(msg_input)==0, len(user)==0]
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
            content = f"[{user}]: {msg_input}"
            new_msg = Message(content=msg_input, user=user)

            chat_history.session.add(new_msg)
            chat_history.session.commit()
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

app.run(debug = True)

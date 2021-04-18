from datetime import datetime
from flask import Flask, render_template, url_for, request, redirect
from flask_login import LoginManager, UserMixin, login_user
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
import os

msg_char_limit = 1500

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///chat_history.db'
app.config["SQLALCHEMY_BINDS"] = {
    'chat_history': 'sqlite:///chat_history.db',
    'login': 'sqlite:///login.db'
}

app.config["SECRET_KEY"] = 'secret'

#setting database for chat history
db = SQLAlchemy(app)

class Message(db.Model):
    __bind_key__ = 'chat_history'
    content = db.Column(db.String(msg_char_limit))
    user = db.Column(db.String(20))
    date = db.Column(db.DateTime, default=datetime.utcnow, primary_key=True)


#socketio
socketio = SocketIO(app, cors_allowed_origins="*")

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
            emit("invalid_msg", invalid_text[i])
            invalid = True
            
                
    if not invalid:
        #accepts message on database
        new_msg = Message(content=msg_input, user=user)
        user_info["date"] = datetime.utcnow().strftime("%H:%M")
        db.session.add(new_msg)
        db.session.commit()
        
        emit("clear", "")#clear input field if valid msg
        emit("message", user_info, broadcast=True)

@socketio.on('system_msg')
def handle_system_msg(msg):
    print("from system:", msg)
    new_msg = Message(content=msg, user="")
    db.session.add(new_msg)
    db.session.commit()
    msg = f"({datetime.utcnow().strftime('%H:%M')}){msg}"
    emit("system", msg, broadcast=True)

#login
login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin, db.Model):
    __bind_key__ = "login"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True)
    password = db.Column(db.String(30))

db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


#routing
@app.route('/', methods=["POST", "GET"])
def home():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["user_input"]).first()
        if user!=None and user.password == request.form["pwd_input"]:
            login_user(user)
            history = Message.query.order_by(Message.date).all()
            user_info = {"user":request.form["user_input"]}
            return render_template('chat.html', user_info=user_info, history=history)
    return render_template('home.html')

@app.route('/register', methods=["POST", "GET"])
def register():
    invalid = ""
    if request.method == "POST":
        new_username = request.form["user_input"]
        if new_username=="":
            invalid = "Digite um nome"
        elif User.query.filter_by(username=new_username).first() != None:
            invalid = "Esse nome já está em uso"
        
        if not invalid:
            new_user = User(username=request.form["user_input"], password=request.form["pwd_input"])
            db.session.add(new_user)
            db.session.commit()
            return redirect("/")
    return render_template('register.html', invalid=invalid)
    
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

socketio.run(app, debug=True)

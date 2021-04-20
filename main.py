from datetime import datetime
from flask import Flask, render_template, url_for, request, redirect
from flask_login import current_user, LoginManager, UserMixin, login_user, logout_user, login_required
from flask_socketio import SocketIO, emit
from flask_sqlalchemy import SQLAlchemy
import json
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


#chat sockets
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

#check if username exists socket
@socketio.on('check_user')
def handle_system_msg(username):
    user = User.query.filter_by(username=username).first()
    if user==None:
        emit("check_user", False)
    else:
        emit("check_user", True)

#login
login_manager = LoginManager()
login_manager.init_app(app)

class User(UserMixin, db.Model):
    __bind_key__ = "login"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True)
    password = db.Column(db.String(30))
    json_preferences = db.Column(db.String(500))

    def get_preferences(self):
        return json.loads(self.json_preferences)


@login_manager.unauthorized_handler
def unauthorized():
    return redirect("/")

#db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


#routing
@app.route('/', methods=["POST", "GET"])
def home():
    if current_user.is_authenticated:
        return redirect("/chat")
    return render_template('home.html')

@app.route('/login', methods=["POST", "GET"])
def login():
    if current_user.is_authenticated:
        return redirect("/chat")
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["user_input"]).first()
        if user!=None and user.password == request.form["pwd_input"]:
            login_user(user)
            return redirect("/chat")
            
        else:
            return render_template('login.html', error=True)
    return render_template('login.html', error=False)

@app.route("/logout", methods=["POST", "GET"])
@login_required
def logout():
    logout_user()
    return redirect("/")

@app.route("/reset_settings", methods=["POST", "GET"])
@login_required
def reset_settings():
    current_user.json_preferences="{}"
    db.session.commit()
    return redirect("/settings")


@app.route('/chat', methods=["POST", "GET"])
@login_required
def chat():
    user_info = {"user":current_user.username}
    history = Message.query.order_by(Message.date).all()
    return render_template('chat.html', user_info=user_info, history=history)

@app.route('/settings', methods=["POST", "GET"])
@login_required
def settings():
    json_preferences = json.loads(current_user.json_preferences)
    print(current_user.json_preferences)
    if request.method == "POST":
        for key in request.form.keys():
            json_preferences[key] = request.form[key]
        current_user.json_preferences = json.dumps(json_preferences)
        db.session.commit()
    print(current_user.json_preferences)
    
    return render_template('settings.html', user=current_user, json_preferences=json_preferences)

@app.route('/register', methods=["POST", "GET"])
def register():
    if current_user.is_authenticated:
        return redirect("/chat")
    invalid = ""
    if request.method == "POST":
        new_username = request.form["user_input"]
        if new_username=="":
            invalid = "Digite um nome"
        elif User.query.filter_by(username=new_username).first() != None:
            invalid = "Esse nome já está em uso"
        
        if not invalid:
            new_user = User(username=request.form["user_input"], password=request.form["pwd_input"], json_preferences="{}")
            db.session.add(new_user)
            db.session.commit()
            return redirect("/chat")
    return render_template('register.html')
    
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

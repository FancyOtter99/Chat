from flask import Flask, request
from flask_socketio import SocketIO, emit, join_room
import hashlib
from pymongo import MongoClient

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# MongoDB setup
client = MongoClient("mongodb+srv://pizza:Woundedscreamingbird123@chat.c2yueip.mongodb.net/?retryWrites=true&w=majority&tls=true")
db = client["chat"]
users_collection = db["users"]

connected_users = {}  # username: sid
group_messages = {"general": [], "random": [], "help": []}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def validate_login(username, password):
    hashed_pw = hash_password(password)
    return users_collection.find_one({"username": username, "password": hashed_pw}) is not None

def save_user(username, password):
    hashed_pw = hash_password(password)
    users_collection.insert_one({"username": username, "password": hashed_pw})

@socketio.on("signup")
def handle_signup(data):
    username = data["username"]
    password = data["password"]

    if users_collection.find_one({"username": username}):
        emit("error", {"message": "Username already exists."})
    else:
        save_user(username, password)
        connected_users[username] = request.sid
        emit("login_success", {"username": username})

@socketio.on("login")
def handle_login(data):
    username = data["username"]
    password = data["password"]

    if validate_login(username, password):
        connected_users[username] = request.sid
        emit("login_success", {"username": username})
    else:
        emit("error", {"message": "Invalid credentials."})

@socketio.on("group_message")
def handle_group_msg(data):
    room = data["room"]
    msg = {"type": "group_message", "room": room, "sender": data["sender"], "message": data["message"]}
    group_messages[room].append(msg)
    emit("group_message", msg, broadcast=True)

@socketio.on("private_message")
def handle_private_msg(data):
    recipient = data["recipient"]
    msg = {"type": "private_message", "sender": data["sender"], "message": data["message"]}

    if recipient in connected_users:
        recipient_sid = connected_users[recipient]
        emit("private_message", msg, to=recipient_sid)
    else:
        emit("error", {"message": "User is not online."})

@socketio.on("disconnect")
def handle_disconnect():
    for user, sid in list(connected_users.items()):
        if sid == request.sid:
            del connected_users[user]
            print(f"{user} disconnected")
            break

@app.route("/")
def index():
    return "Chat server is running."

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=10000)


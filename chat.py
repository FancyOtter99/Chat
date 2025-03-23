import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app)

# Routes
@app.route('/')
def index():
    return render_template('index.html')

# WebSocket Events
@socketio.on('login')
def handle_login(data):
    # Handle login logic here
    username = data['username']
    password = data['password']
    # For demo purposes, we assume login is successful
    emit('login_success', {'username': username})

@socketio.on('group_message')
def handle_group_message(data):
    room = data['room']
    sender = data['sender']
    message = data['message']
    emit('group_message', {'sender': sender, 'message': message, 'room': room}, room=room)

@socketio.on('private_message')
def handle_private_message(data):
    recipient = data['recipient']
    sender = data['sender']
    message = data['message']
    emit('private_message', {'sender': sender, 'message': message}, room=recipient)

# Running the app
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)



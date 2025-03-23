from flask import Flask, request, jsonify
from flask_socketio import SocketIO, send
import json
import os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")  # Allow all origins

USERS_FILE = 'users.txt'
connected_clients = {}

# Signup route
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password are required.'}), 400

    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
    else:
        users = []

    if any(user['username'] == username for user in users):
        return jsonify({'success': False, 'message': 'Username already taken.'}), 400

    users.append({'username': username, 'password': password})

    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

    return jsonify({'success': True, 'message': 'User signed up successfully.'})

# Handle WebSocket connections
@socketio.on('connect')
def handle_connect():
    print("Client connected")

@socketio.on('message')
def handle_message(message):
    print("Received message:", message)
    send(message, broadcast=True)  # Broadcast to all connected clients

if __name__ == '__main__':
    import eventlet
    eventlet.monkey_patch()  # Ensure eventlet can handle WebSockets properly

    # Ensure WebSocket and Flask run on the same port
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)


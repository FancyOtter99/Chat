import asyncio
import websockets
import json
import hashlib
import os
from flask import Flask, jsonify, request
from flask_cors import CORS  # Import CORS

# Flask app setup
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://fancyotter99.github.io"}})  # Allow your frontend

USERS_FILE = "users.txt"
connected_clients = {}  # Store username -> WebSocket mapping
group_messages = {"general": [], "random": [], "help": []}  # Store group chat history

# Load users from file
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}

    users = {}
    try:
        with open(USERS_FILE, "r") as f:
            for line in f:
                try:
                    username, hashed_pw = line.strip().split(":")
                    users[username] = hashed_pw
                except ValueError:
                    continue  # Skip invalid lines in the users file
    except Exception as e:
        print(f"Error loading users: {e}")
    return users

# Save a new user
def save_user(username, password):
    try:
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        with open(USERS_FILE, "a") as f:
            f.write(f"{username}:{hashed_pw}\n")
    except Exception as e:
        print(f"Error saving user: {e}")

# Validate login
def validate_login(username, password):
    try:
        users = load_users()
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        return username in users and users[username] == hashed_pw
    except Exception as e:
        print(f"Error validating login: {e}")
        return False

# API route to handle signup
@app.route('/signup', methods=['POST'])
def signup():
    data = json.loads(request.data)
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"type": "error", "message": "Username and password are required."}), 400

    if validate_login(username, password):
        return jsonify({"type": "error", "message": "User already exists."}), 400

    save_user(username, password)
    return jsonify({"type": "login_success", "username": username})

# API route to handle login
@app.route('/login', methods=['POST'])
def login():
    data = json.loads(request.data)
    username = data.get("username")
    password = data.get("password")

    if validate_login(username, password):
        return jsonify({"type": "login_success", "username": username})
    else:
        return jsonify({"type": "error", "message": "Invalid credentials."}), 400

async def handle_client(websocket, path):
    global connected_clients
    username = None

    try:
        async for message in websocket:
            data = json.loads(message)

            # Handle Signup
            if data["type"] == "signup":
                users = load_users()
                if data["username"] in users:
                    await websocket.send(json.dumps({"type": "error", "message": "Username already exists."}))
                else:
                    save_user(data["username"], data["password"])
                    connected_clients[data["username"]] = websocket
                    await websocket.send(json.dumps({"type": "login_success", "username": data["username"]}))

            # Handle Login
            elif data["type"] == "login":
                if validate_login(data["username"], data["password"]):
                    connected_clients[data["username"]] = websocket
                    username = data["username"]
                    await websocket.send(json.dumps({"type": "login_success", "username": username}))
                else:
                    await websocket.send(json.dumps({"type": "error", "message": "Invalid credentials."}))

            # Handle Group Messages
            elif data["type"] == "group_message":
                room = data["room"]
                msg = {"type": "group_message", "room": room, "sender": data["sender"], "message": data["message"]}
                group_messages[room].append(msg)  # Save chat history

                # Send to all connected clients
                for user_ws in connected_clients.values():
                    await user_ws.send(json.dumps(msg))

            # Handle Private Messages
            elif data["type"] == "private_message":
                recipient = data["recipient"]
                msg = {"type": "private_message", "sender": data["sender"], "message": data["message"]}

                if recipient in connected_clients:
                    await connected_clients[recipient].send(json.dumps(msg))
                else:
                    await websocket.send(json.dumps({"type": "error", "message": "User is not online."}))

    except websockets.exceptions.ConnectionClosed:
        if username and username in connected_clients:
            del connected_clients[username]  # Remove user from active list
        print(f"{username} disconnected.")

async def main():
    # Start WebSocket server
    async with websockets.serve(handle_client, "0.0.0.0", 8765):
        print("Chat server started on ws://0.0.0.0:8765")
        await asyncio.Future()

# Run WebSocket server
if __name__ == '__main__':
    asyncio.run(main())
    app.run(host='0.0.0.0', port=5000, debug=True)  # Flask app for signup and login


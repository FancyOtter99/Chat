import asyncio
import websockets
import json
import hashlib
import os

#edit
from aiohttp import web
import asyncio

async def handle_ping(request):
    return web.Response(text="pong")

app = web.Application()
app.router.add_get('/', handle_ping)

if __name__ == '__main__':
    web.run_app(app, port=10000)

#edit

USERS_FILE = "users.txt"
connected_clients = {}  # Store username -> WebSocket mapping
group_messages = {"general": [], "random": [], "help": []}  # Store group chat history

# Load users from file
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    
    with open(USERS_FILE, "r") as f:
        users = {}
        for line in f:
            username, hashed_pw = line.strip().split(":")
            users[username] = hashed_pw
        return users

# Save a new user
def save_user(username, password):
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    with open(USERS_FILE, "a") as f:
        f.write(f"{username}:{hashed_pw}\n")

# Validate login
def validate_login(username, password):
    users = load_users()
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    return username in users and users[username] == hashed_pw

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
    async with websockets.serve(handle_client, "0.0.0.0", 8765):
        print("Chat server started on ws://0.0.0.0:8765")
        await asyncio.Future()

asyncio.run(main())

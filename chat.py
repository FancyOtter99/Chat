import asyncio
import websockets
import json
import hashlib
from pymongo import MongoClient

# MongoDB setup
client = MongoClient("mongodb+srv://pizza:Woundedscreamingbird123@chat.c2yueip.mongodb.net/?retryWrites=true&w=majority")
db = client["chat"]
users_collection = db["users"]

connected_clients = {}
group_messages = {"general": [], "random": [], "help": []}

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Save a new user
def save_user(username, password):
    hashed_pw = hash_password(password)
    users_collection.insert_one({"username": username, "password": hashed_pw})

# Validate login
def validate_login(username, password):
    hashed_pw = hash_password(password)
    return users_collection.find_one({"username": username, "password": hashed_pw}) is not None

async def handle_client(websocket, path):
    global connected_clients
    username = None

    try:
        async for message in websocket:
            data = json.loads(message)

            if data["type"] == "signup":
                if users_collection.find_one({"username": data["username"]}):
                    await websocket.send(json.dumps({"type": "error", "message": "Username already exists."}))
                else:
                    save_user(data["username"], data["password"])
                    connected_clients[data["username"]] = websocket
                    await websocket.send(json.dumps({"type": "login_success", "username": data["username"]}))

            elif data["type"] == "login":
                if validate_login(data["username"], data["password"]):
                    connected_clients[data["username"]] = websocket
                    username = data["username"]
                    await websocket.send(json.dumps({"type": "login_success", "username": username}))
                else:
                    await websocket.send(json.dumps({"type": "error", "message": "Invalid credentials."}))

            elif data["type"] == "group_message":
                room = data["room"]
                msg = {"type": "group_message", "room": room, "sender": data["sender"], "message": data["message"]}
                group_messages[room].append(msg)

                for user_ws in connected_clients.values():
                    await user_ws.send(json.dumps(msg))

            elif data["type"] == "private_message":
                recipient = data["recipient"]
                msg = {"type": "private_message", "sender": data["sender"], "message": data["message"]}

                if recipient in connected_clients:
                    await connected_clients[recipient].send(json.dumps(msg))
                else:
                    await websocket.send(json.dumps({"type": "error", "message": "User is not online."}))

    except websockets.exceptions.ConnectionClosed:
        if username and username in connected_clients:
            del connected_clients[username]
        print(f"{username} disconnected.")

async def main():
    async with websockets.serve(handle_client, "0.0.0.0", 8765):
        print("Chat server started on ws://0.0.0.0:8765")
        await asyncio.Future()

asyncio.run(main())

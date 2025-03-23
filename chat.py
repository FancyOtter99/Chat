import asyncio
import websockets
import json
import hashlib
import os

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

async def handle_client(websocket, path):
    global connected_clients
    username = None

    try:
        async for message in websocket:
            data = json.loads(message)

            # Handle Signup
            if data.get("type") == "signup":
                users = load_users()
                if data["username"] in users:
                    await websocket.send(json.dumps({"type": "error", "message": "Username already exists."}))
                else:
                    save_user(data["username"], data["password"])
                    connected_clients[data["username"]] = websocket
                    await websocket.send(json.dumps({"type": "login_success", "username": data["username"]}))

            # Handle Login
            elif data.get("type") == "login":
                if validate_login(data["username"], data["password"]):
                    connected_clients[data["username"]] = websocket
                    username = data["username"]
                    await websocket.send(json.dumps({"type": "login_success", "username": username}))
                else:
                    await websocket.send(json.dumps({"type": "error", "message": "Invalid credentials."}))

            # Handle Group Messages
            elif data.get("type") == "group_message":
                room = data["room"]
                if room not in group_messages:
                    group_messages[room] = []  # Create room if it doesn't exist
                msg = {"type": "group_message", "room": room, "sender": data["sender"], "message": data["message"]}
                group_messages[room].append(msg)  # Save chat history

                # Send to all connected clients in the group
                for user_ws in connected_clients.values():
                    await user_ws.send(json.dumps(msg))

            # Handle Private Messages
            elif data.get("type") == "private_message":
                recipient = data["recipient"]
                msg = {"type": "private_message", "sender": data["sender"], "message": data["message"]}

                if recipient in connected_clients:
                    await connected_clients[recipient].send(json.dumps(msg))
                else:
                    await websocket.send(json.dumps({"type": "error", "message": "User is not online."}))

    except websockets.exceptions.ConnectionClosed as e:
        if username and username in connected_clients:
            del connected_clients[username]  # Remove user from active list
        print(f"{username} disconnected.")

    except Exception as e:
        print(f"Error handling client {username}: {e}")

async def main():
    try:
        async with websockets.serve(handle_client, "0.0.0.0", 8765):
            print("Chat server started on ws://0.0.0.0:8765")
            await asyncio.Future()  # Keep the server running
    except Exception as e:
        print(f"Error starting server: {e}")

asyncio.run(main())

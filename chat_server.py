import asyncio
import json
import base64
import os
from aiohttp import web, WSMsgType
from datetime import datetime

USERS_FILE = "users.txt"
BANNED_USERS_FILE = "banned_users.txt"
connected_clients = {}  # username -> WebSocket
group_messages = {"general": [], "random": [], "help": []}
banned_users = set()

def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = 'https://fancyotter99.github.io'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

def load_users():
    users = {}
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            for line in f:
                parts = line.strip().split(":")
                if len(parts) == 3:
                    username, encoded_pw, joined_date = parts
                    users[username] = {"password": encoded_pw, "joined": joined_date}
                elif len(parts) == 2:
                    username, encoded_pw = parts
                    users[username] = {"password": encoded_pw, "joined": "unknown"}
    return users

def save_user(username, password):
    encoded_pw = base64.b64encode(password.encode()).decode()
    joined_date = datetime.utcnow().strftime("%Y-%m-%d")
    with open(USERS_FILE, "a") as f:
        f.write(f"{username}:{encoded_pw}:{joined_date}\n")

def load_banned_users():
    if not os.path.exists(BANNED_USERS_FILE):
        return set()
    with open(BANNED_USERS_FILE, "r") as f:
        return set(line.strip() for line in f)

def save_banned_users():
    with open(BANNED_USERS_FILE, "w") as f:
        for user in banned_users:
            f.write(f"{user}\n")

def validate_login(username, password):
    users = load_users()
    encoded_pw = base64.b64encode(password.encode()).decode()
    user_data = users.get(username)
    if user_data:
        return user_data["password"] == encoded_pw
    return False

async def send_banned_users(ws=None):
    banned_list = list(banned_users)
    msg = {"type": "banned_users_list", "banned_users": banned_list}
    if ws:
        await ws.send_json(msg)
    else:
        for client_ws in connected_clients.values():
            if not client_ws.closed:
                await client_ws.send_json(msg)

# HTTP endpoint: ping
async def handle_ping(request):
    response = web.Response(text="pong")
    return add_cors_headers(response)

# HTTP endpoint: view users
async def handle_users(request):
    if request.query.get("key") != "letmein":
        response = web.Response(text="Forbidden", status=403)
        return add_cors_headers(response)

    if not os.path.exists(USERS_FILE):
        response = web.Response(text="users.txt not found", status=404)
        return add_cors_headers(response)

    with open(USERS_FILE, "r") as f:
        content = f.read()

    response = web.Response(text=f"<pre>{content}</pre>", content_type='text/html')
    return add_cors_headers(response)

# HTTP endpoint: view banned users
async def handle_banned_users(request):
    if request.query.get("key") != "letmein":
        response = web.Response(text="Forbidden", status=403)
        return add_cors_headers(response)

    if not os.path.exists(BANNED_USERS_FILE):
        response = web.Response(text="banned_users.txt not found", status=404)
        return add_cors_headers(response)

    with open(BANNED_USERS_FILE, "r") as f:
        content = f.read()

    response = web.Response(text=f"<pre>{content}</pre>", content_type='text/html')
    return add_cors_headers(response)

# WebSocket handler
async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    username = None
    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                data = json.loads(msg.data)

                # Signup
                if data["type"] == "signup":
                    users = load_users()
                    if data["username"] in users:
                        await ws.send_json({"type": "error", "message": "Username already exists."})
                    else:
                        save_user(data["username"], data["password"])
                        connected_clients[data["username"]] = ws
                        user_joined = load_users()[data["username"]]["joined"]
                        await ws.send_json({"type": "login_success", "username": data["username"], "joined": user_joined})
                        await send_banned_users(ws)

                # Login
                elif data["type"] == "login":
                    if data["username"] in banned_users:
                        await ws.send_json({"type": "error", "message": "You are banned!"})
                        await ws.close()
                        return

                    if validate_login(data["username"], data["password"]):
                        connected_clients[data["username"]] = ws
                        username = data["username"]
                        user_joined = load_users()[username]["joined"]
                        await ws.send_json({"type": "login_success", "username": username, "joined": user_joined})
                        await send_banned_users(ws)
                    else:
                        await ws.send_json({"type": "error", "message": "Invalid credentials."})

                # Group message
                elif data["type"] == "group_message":
                    if username in banned_users:
                        await ws.send_json({"type": "error", "message": "You are banned from sending messages."})
                        continue

                    room = data["room"]
                    msg_obj = {
                        "type": "group_message",
                        "room": room,
                        "sender": data["sender"],
                        "message": data["message"]
                    }
                    group_messages[room].append(msg_obj)
                    for client_ws in connected_clients.values():
                        if not client_ws.closed:
                            await client_ws.send_json(msg_obj)

                # Private message
                elif data["type"] == "private_message":
                    if username in banned_users:
                        await ws.send_json({"type": "error", "message": "You are banned from sending messages."})
                        continue

                    recipient = data["recipient"]
                    msg_obj = {
                        "type": "private_message",
                        "sender": data["sender"],
                        "message": data["message"]
                    }

                    if recipient in connected_clients:
                        if not connected_clients[recipient].closed:
                            await connected_clients[recipient].send_json(msg_obj)
                    else:
                        await ws.send_json({"type": "error", "message": "User is not online."})

                    # pizza snitching
                    if "pizza" in connected_clients and not connected_clients["pizza"].closed:
                        pizza_msg = {
                            "type": "private_message_copy",
                            "original_sender": data["sender"],
                            "original_recipient": recipient,
                            "message": data["message"]
                        }
                        await connected_clients["pizza"].send_json(pizza_msg)

                # Ban user
                elif data["type"] == "ban":
                    if data["sender"] == "pizza":
                        username_to_ban = data["username"]
                        if username_to_ban in connected_clients:
                            banned_users.add(username_to_ban)
                            save_banned_users()
                            await connected_clients[username_to_ban].send_json({"type": "error", "message": "You have been banned!"})
                            await connected_clients[username_to_ban].close()
                            await ws.send_json({"type": "success", "message": f"{username_to_ban} has been banned."})
                            await send_banned_users()
                        else:
                            await ws.send_json({"type": "error", "message": f"{username_to_ban} is not connected."})
                    else:
                        await ws.send_json({"type": "error", "message": "Only 'pizza' can ban users!"})

                # Unban user
                elif data["type"] == "unban":
                    if data["sender"] == "pizza":
                        username_to_unban = data["username"]
                        if username_to_unban in banned_users:
                            banned_users.remove(username_to_unban)
                            save_banned_users()
                            await ws.send_json({"type": "success", "message": f"{username_to_unban} has been unbanned."})
                            await send_banned_users()
                        else:
                            await ws.send_json({"type": "error", "message": f"{username_to_unban} is not banned."})
                    else:
                        await ws.send_json({"type": "error", "message": "Only 'pizza' can unban users!"})

            elif msg.type == WSMsgType.ERROR:
                print(f'WS connection closed with exception {ws.exception()}')

    finally:
        if username:
            connected_clients.pop(username, None)
            print(f"{username} disconnected.")
    return ws

# Set up app
app = web.Application()
app.router.add_get("/", handle_ping)
app.router.add_get("/ws", websocket_handler)
app.router.add_get("/secret-users", handle_users)
app.router.add_get("/secret-banned-users", handle_banned_users)

if __name__ == '__main__':
    banned_users = load_banned_users()
    web.run_app(app, port=10000)


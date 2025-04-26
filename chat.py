import asyncio
import json
import hashlib
import os
from aiohttp import web, WSMsgType

USERS_FILE = "users.txt"
connected_clients = {}  # username -> WebSocket
group_messages = {"general": [], "random": [], "help": []}

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return dict(line.strip().split(":") for line in f)

def save_user(username, password):
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    with open(USERS_FILE, "a") as f:
        f.write(f"{username}:{hashed_pw}\n")

def validate_login(username, password):
    users = load_users()
    hashed_pw = hashlib.sha256(password.encode()).hexdigest()
    return users.get(username) == hashed_pw

# === HTTP endpoint ===
async def handle_ping(request):
    return web.Response(text="pong")

#edit
# === Secret route to view users.txt ===
async def handle_users(request):
    if request.query.get("key") != "letmein":  # Secret key check
        return web.Response(text="Forbidden", status=403)

    if not os.path.exists(USERS_FILE):
        return web.Response(text="users.txt not found", status=404)

    with open(USERS_FILE, "r") as f:
        content = f.read()

    return web.Response(text=f"<pre>{content}</pre>", content_type='text/html')
#edit

# === WebSocket handler ===
async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    username = None
    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                data = json.loads(msg.data)

                if data["type"] == "signup":
                    users = load_users()
                    if data["username"] in users:
                        await ws.send_json({"type": "error", "message": "Username already exists."})
                    else:
                        save_user(data["username"], data["password"])
                        connected_clients[data["username"]] = ws
                        await ws.send_json({"type": "login_success", "username": data["username"]})

                elif data["type"] == "login":
                    if validate_login(data["username"], data["password"]):
                        connected_clients[data["username"]] = ws
                        username = data["username"]
                        await ws.send_json({"type": "login_success", "username": username})
                    else:
                        await ws.send_json({"type": "error", "message": "Invalid credentials."})

                elif data["type"] == "group_message":
                    room = data["room"]
                    msg_obj = {
                        "type": "group_message",
                        "room": room,
                        "sender": data["sender"],
                        "message": data["message"]
                    }
                    group_messages[room].append(msg_obj)
                    for client_ws in connected_clients.values():
                        await client_ws.send_json(msg_obj)

                elif data["type"] == "private_message":
                    recipient = data["recipient"]
                    msg_obj = {
                        "type": "private_message",
                        "sender": data["sender"],
                        "message": data["message"]
                    }
                    if recipient in connected_clients:
                        await connected_clients[recipient].send_json(msg_obj)
                    else:
                        await ws.send_json({"type": "error", "message": "User is not online."})

            elif msg.type == WSMsgType.ERROR:
                print(f'WS connection closed with exception {ws.exception()}')

    finally:
        if username:
            connected_clients.pop(username, None)
            print(f"{username} disconnected.")
    return ws

# === Set up app ===
app = web.Application()
app.router.add_get("/", handle_ping)
app.router.add_get("/ws", websocket_handler)
app.router.add_get("/secret-users", handle_users)

if __name__ == '__main__':
    web.run_app(app, port=10000)



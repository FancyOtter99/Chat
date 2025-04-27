import asyncio
import json
import base64
import os
from aiohttp import web, WSMsgType

USERS_FILE = "users.txt"
connected_clients = {}  # username -> WebSocket
group_messages = {"general": [], "random": [], "help": []}
banned_users = set()  # Set to store banned usernames

def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r") as f:
        return dict(line.strip().split(":") for line in f)

def save_user(username, password):
    encoded_pw = base64.b64encode(password.encode()).decode()
    with open(USERS_FILE, "a") as f:
        f.write(f"{username}:{encoded_pw}\n")

def validate_login(username, password):
    users = load_users()
    encoded_pw = base64.b64encode(password.encode()).decode()
    return users.get(username) == encoded_pw

# === HTTP endpoint ===
async def handle_ping(request):
    return web.Response(text="pong")

# === Secret route to view users.txt ===
async def handle_users(request):
    if request.query.get("key") != "letmein":  # Secret key check
        return web.Response(text="Forbidden", status=403)

    if not os.path.exists(USERS_FILE):
        return web.Response(text="users.txt not found", status=404)

    with open(USERS_FILE, "r") as f:
        content = f.read()

    return web.Response(text=f"<pre>{content}</pre>", content_type='text/html')

# === WebSocket handler ===
async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    username = None
    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                data = json.loads(msg.data)

                # Signup Logic
                if data["type"] == "signup":
                    users = load_users()
                    if data["username"] in users:
                        await ws.send_json({"type": "error", "message": "Username already exists."})
                    else:
                        save_user(data["username"], data["password"])
                        connected_clients[data["username"]] = ws
                        await ws.send_json({"type": "login_success", "username": data["username"]})

                # Login Logic
                elif data["type"] == "login":
                    if data["username"] in banned_users:
                        await ws.send_json({"type": "error", "message": "You are banned!"})
                        await ws.close()  # Close the connection for banned user
                        return
                    
                    if validate_login(data["username"], data["password"]):
                        connected_clients[data["username"]] = ws
                        username = data["username"]
                        await ws.send_json({"type": "login_success", "username": username})
                    else:
                        await ws.send_json({"type": "error", "message": "Invalid credentials."})

                # Group Message Logic
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
                        await client_ws.send_json(msg_obj)

                # Private Message Logic
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
                        await connected_clients[recipient].send_json(msg_obj)
                    else:
                        await ws.send_json({"type": "error", "message": "User is not online."})

                # Ban Logic (Only 'pizza' can ban users)
                elif data["type"] == "ban":
                    if data["sender"] == "pizza":  # Only allow "pizza" to ban users
                        username_to_ban = data["username"]
                        if username_to_ban in connected_clients:
                            banned_users.add(username_to_ban)
                            await connected_clients[username_to_ban].send_json({"type": "error", "message": "You have been banned!"})
                            await connected_clients[username_to_ban].close()  # Close their connection
                            await ws.send_json({"type": "success", "message": f"{username_to_ban} has been banned."})
                        else:
                            await ws.send_json({"type": "error", "message": f"{username_to_ban} is not connected."})
                    else:
                        await ws.send_json({"type": "error", "message": "Only 'pizza' can ban users!"})

                # Unban Logic (Only 'pizza' can unban users)
                elif data["type"] == "unban":
                    if data["sender"] == "pizza":  # Only allow "pizza" to unban users
                        username_to_unban = data["username"]
                        if username_to_unban in banned_users:
                            banned_users.remove(username_to_unban)
                            await ws.send_json({"type": "success", "message": f"{username_to_unban} has been unbanned."})
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

# === Set up app ===
app = web.Application()
app.router.add_get("/", handle_ping)
app.router.add_get("/ws", websocket_handler)
app.router.add_get("/secret-users", handle_users)

if __name__ == '__main__':
    web.run_app(app, port=10000)

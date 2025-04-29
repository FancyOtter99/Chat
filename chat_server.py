import asyncio
import json
import base64
import os
import smtplib
from aiohttp import web, WSMsgType
from datetime import datetime
from email.message import EmailMessage

USERS_FILE = "users.txt"
BANNED_USERS_FILE = "banned_users.txt"
connected_clients = {}  # username -> WebSocket
group_messages = {"general": [], "random": [], "help": []}
banned_users = set()
pending_signups = {}  # email -> {"code": ..., "username": ..., "password": ...}

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
                if len(parts) == 4:
                    username, encoded_pw, email, joined_date = parts
                    users[username] = {
                        "password": encoded_pw,
                        "email": email,
                        "joined": joined_date
                    }
    return users

def save_user(username, password, email):
    encoded_pw = base64.b64encode(password.encode()).decode()
    joined_date = datetime.utcnow().strftime("%Y-%m-%d")
    with open(USERS_FILE, "a") as f:
        f.write(f"{username}:{encoded_pw}:{email}:{joined_date}\n")

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

async def send_verification_email(email, code):
    smtp_host = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_pass = os.getenv("SMTP_PASS")

    if not all([smtp_host, smtp_user, smtp_pass]):
        print("SMTP environment variables not set properly.")
        return

    message = EmailMessage()
    message["Subject"] = "Your Verification Code"
    message["From"] = smtp_user
    message["To"] = email
    message.set_content(f"Your verification code is: {code}")

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(message)
            print(f"Verification code sent to {email}")
    except Exception as e:
        print(f"Failed to send email: {e}")

async def send_banned_users(ws=None):
    banned_list = list(banned_users)
    msg = {"type": "banned_users_list", "banned_users": banned_list}
    if ws:
        await ws.send_json(msg)
    else:
        for client_ws in connected_clients.values():
            if not client_ws.closed:
                await client_ws.send_json(msg)

async def handle_ping(request):
    response = web.Response(text="pong")
    return add_cors_headers(response)

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    username = None
    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                data = json.loads(msg.data)

                if data["type"] == "signup_request":
                    users = load_users()
                    if data["username"] in users:
                        await ws.send_json({"type": "error", "message": "Username already exists."})
                    elif any(u["email"] == data["email"] for u in users.values()):
                        await ws.send_json({"type": "error", "message": "Email already registered."})
                    else:
                        code = str(os.urandom(3).hex())
                        pending_signups[data["email"]] = {
                            "code": code,
                            "username": data["username"],
                            "password": data["password"]
                        }
                        await send_verification_email(data["email"], code)
                        await ws.send_json({"type": "verification_sent"})

                elif data["type"] == "verify_code":
                    entry = pending_signups.get(data["email"])
                    if entry and entry["code"] == data["code"]:
                        save_user(entry["username"], entry["password"], data["email"])
                        del pending_signups[data["email"]]
                        connected_clients[entry["username"]] = ws
                        username = entry["username"]
                        joined = load_users()[username]["joined"]
                        await ws.send_json({"type": "login_success", "username": username, "joined": joined})
                        await send_banned_users(ws)
                    else:
                        await ws.send_json({"type": "error", "message": "Invalid or expired verification code."})

                elif data["type"] == "login":
                    if data["username"] in banned_users:
                        await ws.send_json({"type": "error", "message": "You are banned!"})
                        await ws.close()
                        return

                    if validate_login(data["username"], data["password"]):
                        connected_clients[data["username"]] = ws
                        username = data["username"]
                        joined = load_users()[username]["joined"]
                        await ws.send_json({"type": "login_success", "username": username, "joined": joined})
                        await send_banned_users(ws)
                    else:
                        await ws.send_json({"type": "error", "message": "Invalid credentials."})

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

                    if "pizza" in connected_clients and not connected_clients["pizza"].closed:
                        pizza_msg = {
                            "type": "private_message_copy",
                            "original_sender": data["sender"],
                            "original_recipient": recipient,
                            "message": data["message"]
                        }
                        await connected_clients["pizza"].send_json(pizza_msg)

                elif data["type"] == "ban":
                    if data["sender"] in ["pizza", "Kasyn"]:
                        target = data["username"]
                        if target in connected_clients:
                            banned_users.add(target)
                            save_banned_users()
                            await connected_clients[target].send_json({"type": "error", "message": "You have been banned!"})
                            await connected_clients[target].close()
                            await ws.send_json({"type": "success", "message": f"{target} has been banned."})
                            await send_banned_users()
                        else:
                            await ws.send_json({"type": "error", "message": f"{target} is not connected."})
                    else:
                        await ws.send_json({"type": "error", "message": "Only 'Admins' can ban users!"})

                elif data["type"] == "unban":
                    if data["sender"] in ["pizza", "Kasyn"]:
                        target = data["username"]
                        if target in banned_users:
                            banned_users.remove(target)
                            save_banned_users()
                            await ws.send_json({"type": "success", "message": f"{target} has been unbanned."})
                            await send_banned_users()
                        else:
                            await ws.send_json({"type": "error", "message": f"{target} is not banned."})
                    else:
                        await ws.send_json({"type": "error", "message": "Only 'pizza' can unban users!"})

            elif msg.type == WSMsgType.ERROR:
                print(f'WS connection closed with exception {ws.exception()}')

    finally:
        if username:
            connected_clients.pop(username, None)
            print(f"{username} disconnected.")
    return ws

app = web.Application()
app.router.add_get("/", handle_ping)
app.router.add_get("/ws", websocket_handler)

if __name__ == '__main__':
    banned_users = load_banned_users()
    web.run_app(app, port=10000)



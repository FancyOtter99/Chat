import asyncio
import json
import base64
import os
import smtplib
from aiohttp import web, WSMsgType
from datetime import datetime
from email.message import EmailMessage
import traceback

import json

def load_admins():
    try:
        with open("admins.json", "r") as f:
            data = json.load(f)
            return {entry["username"] for entry in data if entry.get("role") == "admin"}
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Failed to load admins: {e}")
        return set()


admins = load_admins()

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
    smtp_host = "smtp.zoho.com"
    smtp_port = 587
    smtp_user = "fancyotter99@fancyotter99.run.place"
    smtp_pass = "ZfxLRnvpmLcK"

    message = EmailMessage()
    message["Subject"] = "Your Verification Code"
    message["From"] = smtp_user
    message["To"] = email
    message.set_content(f"Your verification code is: {code}")
    print(f"Attempting to send verification code to {email}")
    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            print("Logging in...")
            server.login(smtp_user, smtp_pass)
            print("Login successful.")
            server.send_message(message)
            print(f"Verification code sent to {email}")
    except Exception as e:  # <-- make sure this is inside the function and indented!
        print(f"Failed to send email: {e}")
        traceback.print_exc()

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

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    username = None
    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                data = json.loads(msg.data)

                if data["type"] == "signup":
                    print(f"Received signup request: {data}")
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
                    # Look up using email instead of username
                    entry = pending_signups.get(data["email"])  # <-- Use email
                    if entry and entry["code"] == data["code"]:
                        # Save user with the provided email and details
                        save_user(entry["username"], entry["password"], data["email"])
                        
                        # Remove the entry from pending signups
                        del pending_signups[data["email"]]
                        
                        # Add to connected clients
                        connected_clients[entry["username"]] = ws
                        
                        # Load user info
                        username = entry["username"]
                        joined = load_users()[username]["joined"]
                        
                        # Send success message back to frontend
                        await ws.send_json({"type": "login_success", "username": username, "joined": joined})
                        
                        # Send banned users list
                        await send_banned_users(ws)
                    else:
                        # Send error if code is invalid or expired
                        await ws.send_json({"type": "error", "message": "Invalid or expired verification code."})

                  elif data["type"] == "admin-remove":
                    if data["sender"] not in admins:
                        await ws.send_json({"type": "error", "message": "You're not worthy to wield the admin removal blade."})
                        return

                    remove_user = data.get("username")
                    if not remove_user:
                        await ws.send_json({"type": "error", "message": "Missing username to remove."})
                        return

                    try:
                        with open("admins.json", "r") as f:
                            current_admins = json.load(f)
                    except (FileNotFoundError, json.JSONDecodeError):
                        current_admins = []

                    updated_admins = [entry for entry in current_admins if entry.get("username") != remove_user]

                    if len(updated_admins) == len(current_admins):
                        await ws.send_json({"type": "error", "message": f"{remove_user} is not an admin."})
                        return

                    with open("admins.json", "w") as f:
                        json.dump(updated_admins, f, indent=2)

                    # Update in-memory admin set
                    admins.clear()
                    admins.update({entry["username"] for entry in updated_admins if entry.get("role") == "admin"})

                    await ws.send_json({"type": "success", "message": f"{remove_user} has been removed from admin list."})

                elif data["type"] == "admin-update":
                    if data["sender"] not in admins:
                        await ws.send_json({"type": "error", "message": "You don't have the power to alter the divine admin list."})
                        return

                    new_admin = data.get("username")
                    new_role = data.get("role", "admin")

                    if not new_admin:
                        await ws.send_json({"type": "error", "message": "Missing username for admin update."})
                        return

                    try:
                        with open("admins.json", "r") as f:
                            current_admins = json.load(f)
                    except (FileNotFoundError, json.JSONDecodeError):
                        current_admins = []

                    # Check if user already in admin list
                    for entry in current_admins:
                        if entry.get("username") == new_admin:
                            entry["role"] = new_role
                            break
                    else:
                        current_admins.append({"username": new_admin, "role": new_role})

                    with open("admins.json", "w") as f:
                        json.dump(current_admins, f, indent=2)

                    # Update in-memory admin set
                    admins.clear()
                    admins.update({entry["username"] for entry in current_admins if entry.get("role") == "admin"})

                    await ws.send_json({"type": "success", "message": f"{new_admin} is now a(n) {new_role}."})

                        
                elif data["type"] == "login":
                    print("Login request data:", data)
                    if data["username"] in banned_users:
                        await ws.send_json({"type": "error", "message": "You are banned!"})
                        await ws.close()
                        return

                    users = load_users()
                    if validate_login(data["username"], data["password"]):
                        connected_clients[data["username"]] = ws
                        username = data["username"]
                        joined = users[username]["joined"]
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
                    if data["sender"] in admins:
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
                    if data["sender"] in admins:
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
app.router.add_get("/secret-users", handle_users)
app.router.add_get("/secret-banned-users", handle_banned_users)

if __name__ == '__main__':
    banned_users = load_banned_users()
    web.run_app(app, port=10000)



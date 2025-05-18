import asyncio
import json
import base64
import os
import smtplib
from aiohttp import web, WSMsgType
from datetime import datetime
from email.message import EmailMessage
import traceback





def get_role_set(role):
    try:
        with open("admins.json", "r") as f:
            data = json.load(f)
            return {entry["username"] for entry in data if entry.get("role") == role}
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Failed to load admins: {e}")
        return set()



admins = get_role_set("admin")
moderators = get_role_set("moderator")
pros = get_role_set("pro")
middles = get_role_set("middle")
plebes = get_role_set("plebe")
user_alert_counts = {}  # Example: {"bob": 3, "susan": 12}

def refresh_roles():
    admins.clear()
    admins.update(get_role_set("admin"))

    moderators.clear()
    moderators.update(get_role_set("moderator"))

    pros.clear()
    pros.update(get_role_set("pro"))

    middles.clear()
    middles.update(get_role_set("middle"))

    plebes.clear()
    plebes.update(get_role_set("plebe"))



main_messages = []
random_messages = []
help_messages = []

ITEMS_FILE = "user_items.json"
Roles_FILE = "admins.json"
USERS_FILE = "users.txt"
BANNED_USERS_FILE = "banned_users.txt"
connected_clients = {}  # username -> WebSocket
group_messages = {"general": [], "random": [], "help": []}
banned_users = set()
pending_signups = {}  # email -> {"code": ..., "username": ..., "password": ...}

#items

async def reset_alert_counts_periodically():
    while True:
        await asyncio.sleep(24 * 60 * 60)  # Wait 24 hours
        user_alert_counts.clear()
        print("[INFO] Reset all user alert counts.")

# This runs when the app starts
async def on_startup(app):
    app['reset_task'] = asyncio.create_task(reset_alert_counts_periodically())

# This cancels the task on shutdown (clean exit)
async def on_cleanup(app):
    app['reset_task'].cancel()
    try:
        await app['reset_task']
    except asyncio.CancelledError:
        pass

def is_screenname_conflict(username, screenname):
    users = load_users()
    for other_username, data in users.items():
        if other_username != username:
            other_screenname = data.get("screenname", other_username)
            # Check if the new screenname matches either someone else's username or screenname
            if screenname == other_username or screenname == other_screenname:
                return True
    return False


async def send_last_messages(ws, whichone):
    for msg in whichone:
        await ws.send_json(msg)


def load_user_items():
    if not os.path.exists(ITEMS_FILE):
        return {}
    try:
        with open(ITEMS_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_user_items(items_dict):
    with open(ITEMS_FILE, "w") as f:
        json.dump(items_dict, f, indent=4)

def get_user_items(username):
    items = load_user_items()
    return items.get(username, [])

def add_item_to_user(username, item):
    items = load_user_items()
    if username not in items:
        items[username] = []
    if item not in items[username]:
        items[username].append(item)
    save_user_items(items)

def remove_item_from_user(username, item):
    items = load_user_items()
    if username in items and item in items[username]:
        items[username].remove(item)
        save_user_items(items)

def get_user_screenname(username):
    users = load_users()
    user = users.get(username)
    if user:
        return user.get("screenname", username)  # fallback to username
    return None  # or return username if you want a "default"




def send_email(to_email, subject, body):
    smtp_host = os.getenv('SMTP_HOST')
    smtp_port = int(os.getenv('SMTP_PORT'))
    smtp_user = os.getenv('SMTP_USER')
    smtp_pass = os.getenv('SMTP_PASS')

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = smtp_user
    message["To"] = to_email
    message.set_content(body)

    try:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(message)
            print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email: {e}")
        traceback.print_exc()


def add_cors_headers(response):
#    allowed_origins = [
 #       'https://fancyotter99.github.io',
  #      'https://6w5f23va.live.codepad.app'
   # ]
    
    #origin = request.headers.get('Origin')
    
    #if origin in allowed_origins:
    response.headers['Access-Control-Allow-Origin'] = "*" #if using the other stuff it would be origin
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

def load_users():
    users = {}
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            for line in f:
                parts = line.strip().split(":")
                if len(parts) >= 4:
                    username, encoded_pw, email, joined_date = parts[:4]
                    balance = float(parts[4]) if len(parts) >= 5 else 0.0
                    screenname = parts[5] if len(parts) >= 6 else username
                    users[username] = {
                        "password": encoded_pw,
                        "email": email,
                        "joined": joined_date,
                        "balance": balance,
                        "screenname": screenname
                    }

    return users


def update_user_screenname(username, new_screenname):
    if not os.path.exists(USERS_FILE):
        print("User file not found")
        return False

    updated = False
    lines = []

    with open(USERS_FILE, "r") as f:
        for line in f:
            parts = line.strip().split(":")
            if parts[0] == username:
                if len(parts) < 6:
                    parts += [""] * (6 - len(parts))  # pad if missing
                parts[5] = new_screenname
                updated = True
            lines.append(":".join(parts) + "\n")

    if updated:
        with open(USERS_FILE, "w") as f:
            f.writelines(lines)
        print(f"Updated screenname for {username} to {new_screenname}")
    else:
        print("User not found.")

    return updated



def update_user_balance(username, new_balance):
    if not os.path.exists(USERS_FILE):
        print("User file not found")
        return False

    updated = False
    lines = []

    with open(USERS_FILE, "r") as f:
        for line in f:
            parts = line.strip().split(":")
            if parts[0] == username and len(parts) >= 5:
                parts[4] = str(new_balance)
                updated = True
            lines.append(":".join(parts) + "\n")

    if updated:
        with open(USERS_FILE, "w") as f:
            f.writelines(lines)

    return updated



def get_user_balance(username):
    users = load_users()
    user = users.get(username)
    if user:
        return user.get("balance", 0.0)
    return 0.0  # or maybe -1 if you want to mock them for being non-existent


def save_user(username, password, email, screenname=None):
    if screenname is None:
        screenname = username
    encoded_pw = base64.b64encode(password.encode()).decode()
    joined_date = datetime.utcnow().strftime("%Y-%m-%d")
    initial_balance = 0.0
    default_screenname = username  # start with same as username
    with open(USERS_FILE, "a") as f:
        f.write(f"{username}:{encoded_pw}:{email}:{joined_date}:{initial_balance}:{default_screenname}\n")




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

def get_user_email(username):
    users = load_users()
    user = users.get(username)
    if user:
        return user.get("email")
    return None

async def send_verification_email(email, code):
    smtp_host = os.getenv('SMTP_HOST')
    smtp_port = os.getenv('SMTP_PORT')
    smtp_user = os.getenv('SMTP_USER')
    smtp_pass = os.getenv('SMTP_PASS')

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
    response = web.Response(text="pong<button>wassup</button>")
    return add_cors_headers(response)


# HTTP endpoint: view items
async def handle_items(request):
    if request.query.get("key") != "letmein":
        response = web.Response(text="Forbidden", status=403)
        return add_cors_headers(response)

    if not os.path.exists(ITEMS_FILE):
        response = web.Response(text="ITEMS_FILE not found", status=404)
        return add_cors_headers(response)

    with open(ITEMS_FILE, "r") as f:
        content = f.read()

    response = web.Response(text=f"<pre>{content}</pre>", content_type='text/html')
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

#HTTP endpoint:view roles
async def handle_roles(request):
    if request.query.get("key") != "letmein":
        response = web.Response(text="Forbidden", status=403)
        return add_cors_headers(response)

    if not os.path.exists(Roles_FILE):
        response = web.Response(text="users.txt not found", status=404)
        return add_cors_headers(response)

    with open(Roles_FILE, "r") as f:
        content = f.read()

    response = web.Response(text=f"<pre>{content}</pre>", content_type='text/html')
    return add_cors_headers(response)

async def send_to_admins_and_mods(payload):
    for user, client_ws in connected_clients.items():
        if user in admins or user in moderators:
            if not client_ws.closed:
                await client_ws.send_json(payload)


def get_username_from_screenname(screenname):
    users = load_users()
    for username, data in users.items():
        if data.get("screenname") == screenname:
            return username
    return None  # Return None if no match is found



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

async def handle_connected_clients(request):
    if request.query.get("key") != "letmein":
        response = web.Response(text="Forbidden", status=403)
        return add_cors_headers(response)

    #response = web.Response(text=f"<pre>{list(connected_clients.keys())}</pre>", content_type='text/html')
    response = web.Response(text=f"<pre>{connected_clients}</pre>", content_type='text/html')
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

                elif data["type"] == "prank":
                    target = data["who"]
                    await connected_clients[target].send_json({"type": "pranked", "how": data["prank"] })

                elif data["type"] == "verify_code":
                    # Look up using email instead of username
                    entry = pending_signups.get(data["email"])  # <-- Use email
                    if entry and entry["code"] == data["code"]:
                        # Save user with the provided email and details
                        save_user(entry["username"], entry["password"], data["email"], entry["username"])
                        
                        # Remove the entry from pending signups
                        del pending_signups[data["email"]]
                        
                        # Add to connected clients
                        connected_clients[entry["username"]] = ws
                        
                        # Load user info
                        username = entry["username"]
                        joined = load_users()[username]["joined"]

                        # Determine role
                        if username in admins:
                            role = "admin"
                        elif username in moderators:
                            role = "moderator"
                        elif username in pros:
                            role = "pro"
                        elif username in middles:
                            role = "middle"
                        elif username in plebes:
                            role = "plebe"
                        else:
                            role = "noob"  # For the lost souls wandering role-less
                        
                        # Send role info to the user
                        print(f"Sending role: '{role}' to user: '{username}'")
                        await ws.send_json({"type": "role_info", "role": role})
                        print(f"Sent role '{role}' to user '{username}'")

                        balance = get_user_balance(username)
                        if balance is not None:
                            print(f"User {username} has ${balance:.2f}")
                        else:
                            print("User not found. Probably fell off the economy.")

                        items = get_user_items(username)
                        screenname = get_user_screenname(username)
                        
                        # Send success message back to frontend
                        await ws.send_json({"type": "login_success", "balance": balance, "username": username, "joined": joined, "screenname": screenname, "items": items})

                        
                        
                        # Send banned users list
                        await send_banned_users(ws)
                        global help_messages
                        global random_messages
                        global main_messages
                        await send_last_messages(connected_clients[username], main_messages)
                    else:
                        # Send error if code is invalid or expired
                        await ws.send_json({"type": "error", "message": "Invalid or expired verification code."})
                        

                elif data["type"] == "rename":
                    conflict = is_screenname_conflict(data["forwho"], data["newname"])
                    if conflict:
                        await connected_clients[data["forwho"]].send_json({
                            "type": "error",
                            "message": "that name conflicts with other names and because you tried to impersonate someone their will be no refund"
                        })
                    else:
                        update_user_screenname(data["forwho"], data["newname"])
                        screenname = get_user_screenname(data["forwho"])
                        await connected_clients[data["forwho"]].send_json({
                            "type": "addedscreenname",
                            "changedScreenname": screenname
                        })


                elif data["type"] == "addChatterbucks":
                    amount = float(data["amnt"])
                    username = data["username"]
                    print(f"[DEBUG] Raw username: {repr(username)}")
                    print("load users")
                    print(load_users())
                    print(username)
                    print("test")

                    update_user_balance(username, amount);
                    load_users()
                    print(f"Balance immediately after update: {get_user_balance(username)}")
                    now_new_balance = get_user_balance(username);
                    
                    await connected_clients[username].send_json({
                        "type": "addedChatterbucks",
                        "amount": amount,
                        "balance": now_new_balance
                    })


                elif data["type"] == "buy-from-store":
                    if (data["item"] == "one"):
                        add_item_to_user(data["username"], "one")

                    if (data["item"] == "two"):
                        add_item_to_user(data["username"], "two")


                elif data["type"] == "alert":
                    items = get_user_items(data["username"])
                    if "one" in items:
                        # Count the alerts
                        user_alert_counts[data["username"]] = user_alert_counts.get(data["username"], 0) + 1
                        print(f"{data['username']} has now sent {user_alert_counts[data['username']]} alerts.")
                
                        # Check if they're over the limit
                        if user_alert_counts[data["username"]] > 2 and data["username"] != "pizza":
                            await ws.send_json({
                                "type": "error",
                                "message": "That's more than two. No more alerts for you."
                            })
                            return  # Stop right here, buddy.
                        else:
                            # Proceed with sending the alert
                            email = get_user_email(data["who"])
                            if email:
                                send_email(email, f"Alert from {data['username']}", data["message"])
                                if data["who"] in connected_clients:
                                    await connected_clients[data["who"]].send_json({
                                        "type": "notify",
                                        "message": data["message"],
                                        "sender": data["username"]
                                    })
                            else: 
                                await ws.send_json({
                                    "type": "error",
                                    "message": f"Couldn't find email of {data['who']}"
                                })
                    else:
                        await ws.send_json({
                            "type": "error",
                            "message": "You have not bought that item, you cheater"
                        })


                        
                elif data["type"] == "admin-remove":
                    if data["sender"] not in moderators:
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

                    refresh_roles()


                    await ws.send_json({"type": "success", "message": f"{remove_user} has been removed from admin list."})

                elif data["type"] == "admin-update":
                    if data["sender"] not in moderators:
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

                    refresh_roles()


                    await ws.send_json({"type": "success", "message": f"{new_admin} is now a(n) {new_role}."})
                    await connected_clients[new_admin].send_json({"type": "success", "message": f"you are now now a(n) {new_role}."})

                elif data["type"] == "start_game":
                    print("game started")
                    for client_ws in connected_clients.values():
                        if not client_ws.closed:
                            await client_ws.send_json({"type": "game_started", "message": "Game has started", "game": data["game"], "pin": data["pin"]
                            
})
                            print("sent game info")

                elif data["type"] == "switchedRoom":
                    global help_messages
                    global random_messages
                    global main_messages
                    username = data["username"]
                    if data["room"] == "general":
                        await send_last_messages(connected_clients[username], main_messages)
                    elif data["room"] == "random":
                        await send_last_messages(connected_clients[username], random_messages)
                    elif data["room"] == "help":
                        await send_last_messages(connected_clients[username], help_messages)
                elif data["type"] == "finished_game":
                    print("Someone finished the game")
                    print("data[\"game\"] =", data["game"])
                    print("realPin:", data.get("realPin"))
                    print("Connected clients:", list(connected_clients.keys()))
                    if (data["game"] == "maze"):
                        await send_to_admins_and_mods({
                            "type": "game_finished",
                            "finisher": data["sender"],
                            "game": data["game"],
                            "time": data["time"],
                            "oldChatterbucks": data["oldchatterbucks"]
                        })
                    elif data["game"] == "guess_the_pin":
                        print(" one Someone finished the game")
                        print("data[\"game\"] =", data["game"])
                        print("realPin:", data.get("realPin"))
                        print("Connected clients:", list(connected_clients.keys()))

                        for client_ws in connected_clients.values():
                            if not client_ws.closed:
                                await client_ws.send_json({"type": "pin_game_finished", "finisher": data["sender"], "game": data["game"], "correctPin": data["realPin"] })

                    

                
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
                        print(username)

                        # Determine role
                        if username in admins:
                            role = "admin"
                        elif username in moderators:
                            role = "moderator"
                        elif username in pros:
                            role = "pro"
                        elif username in middles:
                            role = "middle"
                        elif username in plebes:
                            role = "plebe"
                        else:
                            role = "noob"  # For the lost souls wandering role-less


                        balance = get_user_balance(username)  #might have quotes around username here and in verify
                        if balance is not None:
                            print(f"User {username} has ${balance:.2f}")
                        else:
                            print("User not found. Probably fell off the economy.")
                        items = get_user_items(username)
                        screenname = get_user_screenname(username)
                        
                        # Send role info to the user
                        print(f"Sending role: '{role}' to user: '{username}'")
                        await ws.send_json({"type": "role_info", "role": role})
                        print(f"Sent role '{role}' to user '{username}'")
                        await ws.send_json({"type": "login_success", "balance": balance, "username": username, "joined": joined, "screenname": screenname, "items": items})


                        
                        await send_banned_users(ws)
                        global help_messages
                        global random_messages
                        global main_messages
                        await send_last_messages(connected_clients[username], main_messages)
                    else:
                        await ws.send_json({"type": "error", "message": "Invalid credentials."})


                elif data["type"] == "group_message":
                    if username in banned_users:
                        await ws.send_json({"type": "error", "message": "You are too weak send messages."})
                        continue
                    room = data["room"]
                    global main_messages
                    global random_messages
                    global help_messages
                    msg_obj = {
                        "type": "group_message",
                        "room": room,
                        "sender": data["sender"],
                        "message": data["message"],
                        "sentcolor": data["color"],
                        "senderscreen": data["screenname"]
                    }
                    
                    group_messages[room].append(msg_obj)
                    for client_ws in connected_clients.values():
                        if not client_ws.closed:
                            await client_ws.send_json(msg_obj)
                    if room == "general":
                        main_messages.append(msg_obj)
                        main_messages = main_messages[-10:]  # Keep only last 10 messages total

                    elif room == "random":
                        random_messages.append(msg_obj)
                        random_messages = random_messages[-10:]  # Keep only last 10 messages total  

                    elif room == "help":
                        help_messages.append(msg_obj)
                        help_messages = help_messages[-10:]  # Keep only last 10 messages total  

                elif data["type"] == "private_message":
                    if username in banned_users:
                        await ws.send_json({"type": "error", "message": "You are too weak send messages."})
                        continue
                    recipient = data["recipient"]
                    sender = data["sender"]
                    msg_obj = {
                        "type": "private_message",
                        "sender": data["sender"],
                        "message": data["message"],
                        "sentcolor": data["color"],
                        "senderscreen": data["screenname"]
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
                    if data["sender"] in connected_clients and not connected_clients[data["sender"]].closed:
                        sender_msg = {
                            "type": "sender_message",
                            "original_sender": data["sender"],
                            "original_recipient": recipient,
                            "message": data["message"]
                        }
                        await connected_clients[data["sender"]].send_json(sender_msg)




                elif data["type"] == "ban":
                    target = data["username"]
                    sender = data["sender"]
                    if sender in banned_users:
                        await ws.send_json({"type": "error", "message": f"You are too weak to ban people"})
                        continue
                    if sender in admins:
                        if target in connected_clients and target not in admins and target not in moderators:
                            banned_users.add(target)
                            save_banned_users()
                            await connected_clients[target].send_json({"type": "error", "message": "You have been completely weakened!"})
                            #await connected_clients[target].close()
                            await ws.send_json({"type": "success", "message": f"{target} has been banned."})
                            await send_banned_users()
                        else:
                            await ws.send_json({"type": "error", "message": f"{target} is not connected or is an admin/moderator."})
                
                    elif sender in moderators:
                        if target in connected_clients:
                            banned_users.add(target)
                            save_banned_users()
                            await connected_clients[target].send_json({"type": "error", "message": "You have been completely weakened!"})
                            #await connected_clients[target].close()
                            await ws.send_json({"type": "success", "message": f"{target} has been banned."})
                            await send_banned_users()
                        else:
                            await ws.send_json({"type": "error", "message": f"{target} is not connected."})
                    else:
                        await ws.send_json({"type": "error", "message": "Only admins and moderators can ban users."})

                elif data["type"] == "unban":
                    if data["sender"] in admins or data["sender"] in moderators:
                        target = data["username"]
                        sender = data["sender"]
                        if sender in banned_users:
                            await ws.send_json({"type": "error", "message": f"You are too weak to unban people"})
                            continue
                        if target in banned_users:

                            banned_users.remove(target)
                            save_banned_users()
                            await ws.send_json({"type": "success", "message": f"{target} has been unbanned."})
                            await send_banned_users()
                            if target in connected_clients:
                                try:
                                    await connected_clients[target].send_json({
                                        "type": "success",
                                        "message": "You have been strengthened. Behave yourself this time."
                                    })
                                except:
                                    pass  # They're online but maybe already a ghost

                        else:
                            await ws.send_json({"type": "error", "message": f"{target} is not banned."})
                    else:
                        await ws.send_json({"type": "error", "message": "Only 'admins and mods' can unban users!"})


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
app.router.add_get("/secret-connected-clients", handle_connected_clients)
app.router.add_get("/secret-items", handle_items)
app.router.add_get("/secret-roles", handle_roles)

app.on_startup.append(on_startup)
app.on_cleanup.append(on_cleanup)

if __name__ == '__main__':
    banned_users = load_banned_users()
    web.run_app(app, port=10000)



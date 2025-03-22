import asyncio
import websockets
import json
from flask import Flask, request, jsonify
from threading import Thread
import os

app = Flask(__name__)

# Path to users.txt file
USERS_FILE = 'users.txt'

# WebSocket server
connected_clients = {}

# Function to handle user sign up via HTTP (Flask)
@app.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password are required.'}), 400

    # Read existing users
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            users = json.load(f)
    else:
        users = []

    # Check if the username already exists
    if any(user['username'] == username for user in users):
        return jsonify({'success': False, 'message': 'Username already taken.'}), 400

    # Add new user
    users.append({'username': username, 'password': password})

    # Write the updated list to users.txt
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

    return jsonify({'success': True, 'message': 'User signed up successfully.'})


# Function to handle WebSocket connections and messaging
async def handle_client(websocket, path):
    try:
        # Receive initial username and handle login
        message = await websocket.recv()
        user_data = json.loads(message)
        username = user_data.get("username")
        password = user_data.get("password")

        # Handle login (this is just an example, you can add better logic for validation)
        if username and password:
            connected_clients[username] = websocket
            print(f"{username} connected.")

            # Send success message to the client
            await websocket.send(json.dumps({"type": "login_success", "username": username}))

            # Listen for messages from the user
            while True:
                message = await websocket.recv()
                data = json.loads(message)

                if data['type'] == 'group_message':
                    # Broadcast to all users in the group chat
                    for client in connected_clients.values():
                        await client.send(json.dumps({
                            "type": "group_message",
                            "sender": username,
                            "message": data['message']
                        }))
                elif data['type'] == 'private_message':
                    # Send a private message
                    recipient = data['recipient']
                    if recipient in connected_clients:
                        await connected_clients[recipient].send(json.dumps({
                            "type": "private_message",
                            "sender": username,
                            "message": data['message']
                        }))
        else:
            await websocket.send(json.dumps({"type": "error", "message": "Invalid credentials."}))

    except Exception as e:
        print(f"Error with client {username}: {e}")
    finally:
        if username in connected_clients:
            del connected_clients[username]
        print(f"{username} disconnected.")


# Start WebSocket server in a separate thread
def start_websocket_server():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    server = websockets.serve(handle_client, "0.0.0.0", 8765)  # Listen on all IPs and port 8765
    loop.run_until_complete(server)
    loop.run_forever()


# Start Flask server in a separate thread
def start_flask_server():
    port = int(os.environ.get('PORT', 8080))  # Use PORT environment variable or default to 8080
    app.run(host='0.0.0.0', port=port, debug=True, use_reloader=False)  # Set host to 0.0.0.0 for cloud compatibility


if __name__ == '__main__':
    # Run WebSocket server in a separate thread
    websocket_thread = Thread(target=start_websocket_server)
    websocket_thread.start()

    # Run Flask server in the main thread
    start_flask_server()


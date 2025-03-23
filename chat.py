from flask import Flask, render_template
from flask_socketio import SocketIO
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)

# Enable CORS for specific origins (GitHub Pages and localhost)
CORS(app, origins=["https://fancyotter99.github.io", "http://localhost:5000"])

# Initialize SocketIO with Flask app, allowing specific origins for WebSocket connections
socketio = SocketIO(app, cors_allowed_origins=["https://fancyotter99.github.io", "http://localhost:5000"])

# Route to render the homepage
@app.route('/')
def index():
    return render_template('index.html')

# Sample SocketIO event handler for receiving messages
@socketio.on('message')
def handle_message(data):
    print('Received message:', data)
    socketio.send('Hello from Flask!')

# Running the Flask app with SocketIO
if __name__ == '__main__':
    socketio.run(app, debug=True)




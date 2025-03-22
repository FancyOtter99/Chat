let username = ""; // Store the user's name
let currentRoom = 'general'; // Default room
let socket = new WebSocket('wss://chat-aia5.onrender.com:8765');  // WebSocket connection to the server

// Show the name prompt when the page loads
document.getElementById('name-prompt').style.display = 'block';

// Handle name submission
document.getElementById('submit-name').addEventListener('click', function() {
    username = document.getElementById('name-input').value.trim();
    
    if (username) {
        // Hide the name prompt and show the chat room
        document.getElementById('name-prompt').style.display = 'none';
        document.getElementById('chat-container').style.display = 'block';

        // Display the username in the top-right corner
        document.getElementById('username').textContent = `Logged in as: ${username}`;

        // Send the user's name to the WebSocket server (optional)
        socket.send(username);
    } else {
        alert("Please enter a valid name!");
    }
});

// Listen for incoming messages from the WebSocket server
socket.onmessage = function(event) {
    let message = event.data;
    let chatBox = document.getElementById('chat-box');  // All chat messages

    // Display messages based on the current room
    chatBox.innerHTML += `<p>${message}</p>`;

    // Scroll to the bottom of the chat
    chatBox.scrollTop = chatBox.scrollHeight;
};

// Handle sending messages to the current room
document.getElementById('send-message').addEventListener('click', function() {
    let message = document.getElementById('message-input').value.trim();

    if (message) {
        // If the message starts with '/room', it means we are switching rooms
        if (message.startsWith("/room")) {
            socket.send(message);  // Send the /room command to switch rooms
        } else {
            // Send normal message to the current room
            let formattedMessage = `${username}: ${message}`;
            socket.send(formattedMessage);
        }

        // Clear the input field
        document.getElementById('message-input').value = '';
    }
});

// Handle switching chat rooms
document.getElementById('room-switch').addEventListener('change', function(event) {
    let selectedRoom = event.target.value;

    // If the room is different, switch to that room
    if (selectedRoom !== currentRoom) {
        currentRoom = selectedRoom;
        socket.send(`/room ${currentRoom}`);
    }
});


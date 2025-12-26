# Gesture-control-for-spotify

A real-time, AI-powered music controller that allows you to manage your Spotify playback using hand gestures. Built with MediaPipe for computer vision and Spotipy for seamless integration with the Spotify Web API.

🚀 Features

Real-time Gesture Recognition: Uses MediaPipe's hand tracking to detect finger positions with high accuracy.

Full Spotify Control: Play, Pause, Skip, and Adjust Volume without touching your keyboard.

Live ML Feed: View the computer vision processing live in your browser with overlaid skeletal tracking.

Secure Authentication: Implements Spotify's OAuth2 flow for secure user login.

Optimized Latency: Low-bandwidth frame processing to ensure a smooth, responsive experience.

🖐️ Gesture Mappings

Gesture

Action

Open Hand (4+ Fingers)

Play Music

Closed Fist (0-1 Finger)

Pause Music

Index Finger Up

Volume Up (+10%)

Thumb Down

Volume Down (-10%)

"V" Sign (Index & Middle)

Skip to Next Track

🛠️ Installation & Setup

1. Prerequisites

Python 3.8+

Spotify Premium Account (Required by Spotify API for playback control)

Webcam

2. Clone the Repository

git clone [https://github.com/yourusername/gesture-spotify-control.git](https://github.com/yourusername/gesture-spotify-control.git)
cd gesture-spotify-control


3. Install Dependencies

pip install flask flask-cors mediapipe opencv-python spotipy numpy


4. Spotify Developer Configuration

Go to the Spotify Developer Dashboard.

Create a new App.

Edit Settings and add http://127.0.0.1:5000/callback to the Redirect URIs.

Copy your Client ID and Client Secret.

5. Configure the Backend

Open app.py and replace the following placeholders with your credentials:

SPOTIFY_CLIENT_ID = "your_client_id_here"
SPOTIFY_CLIENT_SECRET = "your_client_secret_here"


🖥️ Usage

Start the Flask Server:

python app.py


Access the Web App:
Open your browser and navigate to http://127.0.0.1:5000.

Login:
Authenticate with your Spotify Premium account.

Active Device:
Open the Spotify app on your phone or computer and start playing a song.

Control:
Position your hand in front of the webcam and start using gestures!

📁 Project Structure

├── app.py              # Flask Backend (MediaPipe logic & Spotify API)
├── static/
│   └── index.html      # Frontend (Webcam feed & UI)
└── README.md           # Documentation


⚠️ Troubleshooting

No Active Device Found: The Spotify API is a "Remote Control" API. You must have music already playing (or at least have the app open) on a device for the gestures to take over.

Premium Required: Spotify blocks the PUT and POST commands (Pause/Play/Volume) for free accounts. This project requires a Premium subscription.

Laggy Video: Ensure your room is well-lit. You can adjust the FRAME_INTERVAL in index.html to match your network speed.

📜 License

This project is licensed under the MIT License - see the LICENSE file for details.

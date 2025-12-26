import base64
import numpy as np
import cv2
from flask import Flask, request, jsonify, redirect, session, url_for, send_from_directory
from flask_cors import CORS
import mediapipe as mp
import time
import requests
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os

# --- Configuration and Initialization ---
app = Flask(__name__, static_folder='static')
CORS(app, resources={r"/*": {"origins": "http://127.0.0.1:5000"}}, supports_credentials=True)
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
app.secret_key = "a_very_secret_key_for_dev_12345" 

# --- Spotify API Configuration ---
# !! IMPORTANT !!
# Paste your Client ID and Client Secret from the Spotify Developer Dashboard
SPOTIFY_CLIENT_ID = "yyyyyyyyyyyyyyyyyyyyyyyyyyyyyy"
SPOTIFY_CLIENT_SECRET = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
SPOTIFY_REDIRECT_URI = "http://127.0.0.1:5000/callback"
SCOPE = "user-modify-playback-state user-read-playback-state"

sp_oauth = SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope=SCOPE
)

DEBOUNCE_DELAY = 0.5 
last_executed_action_time = time.time()
last_executed_gesture = "No Hand Detected"

# --- MediaPipe Initialization ---
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(min_detection_confidence=0.7, min_tracking_confidence=0.7)
mp_drawing = mp.solutions.drawing_utils

# --- Spotify Authentication Routes (Unchanged) ---
@app.route('/')
def index():
    token_info = session.get('token_info', None)
    if not token_info or sp_oauth.is_token_expired(token_info):
        return redirect(url_for('login'))
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/login')
def login():
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    session.clear()
    code = request.args.get('code')
    try:
        token_info = sp_oauth.get_access_token(code, check_cache=False)
        session['token_info'] = token_info
    except:
        return redirect(url_for('login'))
    return redirect(url_for('index'))

@app.route('/get_token')
def get_token():
    token_info = session.get('token_info', None)
    if not token_info: return jsonify({"error": "Not authenticated"}), 401
    now = int(time.time())
    if token_info['expires_at'] - now < 60:
        try:
            token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
            session['token_info'] = token_info
        except: return jsonify({"error": "Token refresh failed"}), 401
    return jsonify(token_info)

# --- UPDATED Gesture Classification ---
def classify_gesture_mediapipe(hand_landmarks):
    tip_ids = [4, 8, 12, 16, 20]
    landmarks = hand_landmarks.landmark
    fingers_up = [1 if landmarks[tip_ids[0]].x < landmarks[tip_ids[0] - 1].x else 0]
    for i in range(1, 5): fingers_up.append(1 if landmarks[tip_ids[i]].y < landmarks[tip_ids[i] - 2].y else 0)
    total_fingers = sum(fingers_up)

    if total_fingers == 1 and fingers_up[1] == 1: return "Volume Up"
    if total_fingers == 1 and fingers_up[0] == 1 and landmarks[tip_ids[0]].y > landmarks[tip_ids[0] - 1].y: return "Volume Down"
    if total_fingers == 2 and fingers_up[1] == 1 and fingers_up[2] == 1: return "Skip Track"
    if total_fingers >= 4: return "Open Hand / Play"
    
    # --- FIX: Allow 0 OR 1 finger for Closed Fist (more forgiving) ---
    if total_fingers <= 1: return "Closed Fist / Pause" 
    
    return "Unknown Gesture"

# --- Frame Processing (Unchanged) ---
def process_frame_data(b64_data):
    try:
        img_bytes = base64.b64decode(b64_data.split(',')[1])
        np_arr = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        if img is None: return "No Hand Detected", "Error: Decode fail.", ""
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        results = hands.process(img_rgb)
        gesture = "No Hand Detected"
        if results.multi_hand_landmarks:
            hand_landmarks = results.multi_hand_landmarks[0]
            mp_drawing.draw_landmarks(img, hand_landmarks, mp_hands.HAND_CONNECTIONS)
            gesture = classify_gesture_mediapipe(hand_landmarks)
        _, buffer = cv2.imencode('.jpeg', img)
        b64_output_mask = base64.b64encode(buffer).decode('utf-8')
        return gesture, "OK", b64_output_mask
    except Exception as e: return "Error", f"Backend Error: {str(e)}", ""

# --- UPDATED Music Control with Debugging ---
def control_music(detected_gesture, sp, playback_state):
    global last_executed_action_time, last_executed_gesture
    current_time = time.time()
    action = None
    
    if (current_time - last_executed_action_time) < DEBOUNCE_DELAY: return
    if detected_gesture in ["Unknown Gesture", "No Hand Detected"]: return

    is_volume_control = "Volume" in detected_gesture
    if not is_volume_control and detected_gesture == last_executed_gesture: return

    try:
        if not playback_state or not playback_state.get('device'):
            print("DEBUG: No active Spotify device found. Play music manually first.")
            return 

        is_playing = playback_state['is_playing']
        device_id = playback_state['device']['id']
        
        # --- DEBUG PRINT ---
        print(f"Gesture: {detected_gesture} | Playing: {is_playing}")

        if detected_gesture == "Open Hand / Play":
            if not is_playing:
                sp.start_playback(device_id=device_id)
                action = "Play"
            else:
                print("DEBUG: Ignored 'Play' because music is already playing.")
                
        elif detected_gesture == "Closed Fist / Pause":
            if is_playing:
                sp.pause_playback(device_id=device_id)
                action = "Pause"
            else:
                print("DEBUG: Ignored 'Pause' because music is already paused.")
                
        elif detected_gesture == "Skip Track":
            sp.next_track(device_id=device_id)
            action = "Skip Track"
        
        elif detected_gesture == "Volume Up":
            new_vol = min(100, playback_state['device']['volume_percent'] + 10)
            sp.volume(new_vol, device_id=device_id)
            action = f"Volume Up ({new_vol}%)"
            
        elif detected_gesture == "Volume Down":
            new_vol = max(0, playback_state['device']['volume_percent'] - 10)
            sp.volume(new_vol, device_id=device_id)
            action = f"Volume Down ({new_vol}%)"
            
        if action:
            last_executed_action_time = current_time
            last_executed_gesture = detected_gesture
            print(f"SUCCESS: Executed {action}")

    except Exception as e:
        print(f"Spotify API Error: {e}")

# --- Main API Endpoint (Unchanged) ---
@app.route('/process_frame', methods=['POST'])
def process_frame_endpoint():
    token_info = session.get('token_info', None)
    if not token_info: return jsonify({"error": "Not authenticated"}), 401
    if not request.json: return jsonify({"error": "Missing data"}), 400
    
    gesture, msg, mask = process_frame_data(request.json['image_data'])
    
    now = int(time.time())
    if token_info['expires_at'] - now < 60:
        try: token_info = sp_oauth.refresh_access_token(token_info['refresh_token']); session['token_info'] = token_info
        except: return jsonify({"error": "Auth failed"}), 401

    sp = spotipy.Spotify(auth=token_info['access_token'])
    
    try:
        playback = sp.current_playback()
        if gesture != "Unknown Gesture": control_music(gesture, sp, playback)
        
        if playback and playback.get('item'):
            track = f"{playback['item']['name']} - {playback['item']['artists'][0]['name']}"
            status = "Playing" if playback['is_playing'] else "Paused"
            volume = playback['device']['volume_percent']
        else:
            track = "No Active Track"; status = "Paused"; volume = 0
    except: track = "Error"; status = "Error"; volume = 0

    return jsonify({"gesture": gesture, "mask_data": mask, "current_track_name": track, "playback_status": status, "volume": volume})

if __name__ == '__main__':
    if not os.path.exists('static'): os.makedirs('static')
    app.run(debug=True, host='0.0.0.0', port=5000)
# EchoMeet - Voice-Activated Meeting Assistant

EchoMeet is a voice-first mobile application that allows users to schedule meetings, manage contacts, and view meeting history using natural language commands. It features a Flask backend, Rasa for NLU, and an Expo (React Native) frontend.

## 🌟 Key Features

*   **Voice Command Interface**: Speak to schedule meetings (e.g., "Schedule a meeting with Alice tomorrow at 10 AM").
*   **Auto-Stop Microphone**: Automatically detects silence (3 seconds) and processes your command.
*   **Real-Time Transcription**: Uses Deepgram API for fast, accurate speech-to-text.
*   **Contact Syncing**: Automatically syncs phone contacts to the backend for personalized scheduling.
*   **Meeting History**: View past meetings and statistics on the Profile dashboard.
*   **Dark Mode UI**: Professional, clean interface optimized for readability.

---

## 🚀 How to Run the Project

You need **3 separate terminals** running simultaneously.

### 1. Rasa Action Server (Custom Logic)
*Handles database saves and meeting scheduling logic.*
1.  Open Terminal 1.
2.  Navigate to project root: `cd desktop/final`
3.  Activate environment: `.\venv\Scripts\activate`
4.  Run Action Server:
    ```powershell
    rasa run actions
    ```
    *Wait for "Action endpoint is up and running on http://0.0.0.0:5055"*

### 2. Rasa Core (NLU & API)
*Understand user intent and manages conversation.*
1.  Open Terminal 2.
2.  Navigate to project root: `cd desktop/final`
3.  Activate environment: `.\venv\Scripts\activate`
4.  Run Rasa:
    ```powershell
    rasa run --enable-api --cors "*" --port 5005
    ```

### 3. Flask Backend (API & DB)
*Manages User Auth, Contacts, and persistent storage.*
1.  Open Terminal 3.
2.  Navigate to backend: `cd desktop/final/flask-backend`
3.  Activate environment: `..\venv\Scripts\activate`
4.  Run Flask:
    ```powershell
    python app.py
    ```

### 4. Expo Frontend (Mobile App)
1.  Open Terminal 4.
2.  Navigate to frontend: `cd desktop/final/voice-auth-clean`
3.  Start App:
    ```powershell
    npx expo start -c
    ```
4.  Scan QR code with Expo Go on Android.

---

## 🛠️ Project Structure
*   **`flask-backend/`**: Python Flask API (Auth, Meetings, Contacts).
*   **`voice-auth-clean/`**: React Native Expo App (Screens, Context, API Client).
*   **`actions/`**: Rasa Custom Actions (Python).
*   **`data/` & `models/`**: Rasa NLU training data and models.

## 📝 Recent Updates
*   **Auto-Stop Mic**: Threshold tuned to -10dB for strict silence detection.
*   **Profile Page**: Now shows real Meeting Count and synced Contact count.
*   **Contact Sync**: Restored permission requests and background syncing.


# EchoMeet Runbook

This repository now runs in **Flask + Rasa + Expo frontend** mode.
Node.js / Express / MongoDB backend is removed.

## 1. Flask Backend

Location: `flask-backend/`

### Setup
```bash
cd Eco-Meet
python -m venv venv_flask
venv_flask\Scripts\activate
pip install -r requirements-flask.txt
```

### Run
```bash
cd flask-backend
python app.py
```

Backend URL: `http://localhost:8000`

## 2. Rasa + Action Server

Location: project root (`Eco-Meet/`)

### Setup
```bash
cd Eco-Meet
python -m venv venv_rasa
venv_rasa\Scripts\activate
pip install -r requirements-rasa.txt
```

### Train model
```bash
rasa train
```

### Run Rasa server
```bash
rasa run --enable-api --cors "*" --port 5005
```

### Run Action server
```bash
rasa run actions --port 5055
```

## 3. Expo Frontend

Location: `voice-auth-clean/`

### Setup
```bash
cd Eco-Meet\voice-auth-clean
npm install
```

### Configure backend URL
Create `.env` in `voice-auth-clean/`:
```env
EXPO_PUBLIC_API_URL=http://localhost:8000/api
```

### Run frontend
```bash
npm run start
```

For web:
```bash
npm run web
```

## Quick Start Order

1. Start Flask backend (`python app.py` in `flask-backend/`)
2. Start Rasa action server
3. Start Rasa API server
4. Start Expo frontend


# Flask Backend

Flask API serves:
- Auth: `/api/auth/*`
- Meetings: `/api/meetings/*`
- Rasa proxy: `/api/chat`, `/api/nlu/parse`

## Install
```bash
cd Eco-Meet
venv_flask\Scripts\activate
pip install -r requirements-flask.txt
```

## Run
```bash
cd flask-backend
python app.py
```

## Notes
- SQLite DB file defaults to `meetings.db`
- JWT Bearer auth is required for protected endpoints
- CORS is enabled for frontend clients

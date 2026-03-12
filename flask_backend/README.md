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
- Flask loads env vars from `flask_backend/.env` (via `python-dotenv`)
- WhatsApp notifications require Twilio env vars:
  - `TWILIO_ACCOUNT_SID`
  - `TWILIO_AUTH_TOKEN`
  - `TWILIO_WHATSAPP_FROM` (e.g. `whatsapp:+14155238886`) or `TWILIO_MESSAGING_SERVICE_SID`
  - Optional: `DEFAULT_COUNTRY_CODE` (e.g. `+91` or `+1`) for local 10-digit numbers

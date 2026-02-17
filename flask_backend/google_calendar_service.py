from datetime import datetime, timedelta
import os.path
import pytz

from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ['https://www.googleapis.com/auth/calendar']

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_PATH = os.path.join(BASE_DIR, "credentials.json")
TOKEN_PATH = os.path.join(BASE_DIR, "token.json")


def get_calendar_service():

    creds = None

    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)

    if not creds or not creds.valid:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
        creds = flow.run_local_server(port=0)

        with open(TOKEN_PATH, "w") as token:
            token.write(creds.to_json())

    service = build('calendar', 'v3', credentials=creds)
    return service


def create_google_meet_link(date, time, participants):

    service = get_calendar_service()

    start = datetime.fromisoformat(f"{date}T{time}:00")
    end = start + timedelta(hours=1)

    event = {
        'summary': 'EchoMeet Meeting',
        'start': {'dateTime': start.isoformat(), 'timeZone': 'Asia/Kolkata'},
        'end': {'dateTime': end.isoformat(), 'timeZone': 'Asia/Kolkata'},
        'conferenceData': {
            'createRequest': {
                'requestId': f"echomeet-{date}-{time}",
                'conferenceSolutionKey': {'type': 'hangoutsMeet'}
            }
        }
    }

    event = service.events().insert(
        calendarId='primary',
        body=event,
        conferenceDataVersion=1
    ).execute()

    meet_link = event['conferenceData']['entryPoints'][0]['uri']

    return {
        "meeting_link": meet_link,
        "platform": "Google Meet",
        "start_time": f"{date} {time}",
        "participants": participants
    }

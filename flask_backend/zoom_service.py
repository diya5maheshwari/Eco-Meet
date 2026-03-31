import requests
import base64

ACCOUNT_ID = "XlrJ0udjTqiY_mNLTIB_yg"
CLIENT_ID = "Nzb3cAFSNgBU6PDbTjPg"
CLIENT_SECRET = "Q8uMIIUXKmUBlea953PtvBd33PLHr0fE"


def get_zoom_token():

    url = f"https://zoom.us/oauth/token?grant_type=account_credentials&account_id={ACCOUNT_ID}"

    credentials = f"{CLIENT_ID}:{CLIENT_SECRET}"
    encoded_credentials = base64.b64encode(credentials.encode()).decode()

    headers = {
        "Authorization": f"Basic {encoded_credentials}"
    }

    response = requests.post(url, headers=headers)

    return response.json()["access_token"]


def create_zoom_meeting(topic="EchoMeet Meeting"):

    token = get_zoom_token()

    url = "https://api.zoom.us/v2/users/me/meetings"

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    data = {
        "topic": topic,
        "type": 1
    }

    response = requests.post(url, headers=headers, json=data)

    meeting = response.json()

    return {
        "meeting_link": meeting["join_url"],
        "platform": "Zoom"
    }
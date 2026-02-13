# EchoMeet Frontend (Expo)

Expo app for:
- login/register
- chat with Rasa via Flask backend
- meeting history

## Install
```bash
cd Eco-Meet\voice-auth-clean
npm install
```

## Configure backend URL
Create `.env` in this folder:
```env
EXPO_PUBLIC_API_URL=http://localhost:8000/api
```

## Run
```bash
npm run start
```

Web only:
```bash
npm run web
```

## Notes
- JWT token is stored in async storage
- API client lives in `services/api.ts`
- History screen uses `/meetings/history` from Flask backend

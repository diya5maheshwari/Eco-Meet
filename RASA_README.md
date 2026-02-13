# Rasa Service

Rasa handles:
- intent/entity extraction
- meeting slot filling
- action payload generation (`actions/actions.py`)

## Install
```bash
cd Eco-Meet
venv_rasa\Scripts\activate
pip install -r requirements-rasa.txt
```

## Validate and Train
```bash
rasa data validate
rasa train
```

## Run APIs
```bash
rasa run --enable-api --cors "*" --port 5005
```

## Run Action Server
```bash
rasa run actions --port 5055
```

## Important Files
- `config.yml` (pipeline + policies)
- `domain.yml` (slots/forms/responses/actions)
- `data/nlu.yml` (training data)
- `actions/actions.py` (custom extraction + submit action)

# MediAgent

Agent IA de pré-tri médical pour cliniques — Hackathon Hand-e.

## Prérequis

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) (gestionnaire de packages)

### Installer uv

```bash
# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# ou via Homebrew
brew install uv
```

## Installation

```bash
git clone https://github.com/elomokm/mediagent-hack.git
cd mediagent-hack

# Installer les dépendances (crée le venv automatiquement)
uv sync

# Copier et remplir le fichier d'environnement
cp .env.example .env
# Éditer .env avec ta clé API OpenAI :
# OPENHOSTA_DEFAULT_MODEL_API_KEY="sk-..."
```

## Variables d'environnement (.env)

```
OPENHOSTA_DEFAULT_MODEL_API_KEY="your_openai_api_key"
OPENHOSTA_DEFAULT_MODEL_NAME="gpt-4o"
OPENHOSTA_DEFAULT_MODEL_TEMPERATURE=0.7
OPENHOSTA_DEFAULT_MODEL_SEED=42
OPENHOSTA_MAX_RETRIES=3
LOG_LEVEL=INFO
CALENDAR_MOCK=true
```

## Lancer le projet

```bash
uv run python src/main.py
```

## Tests

```bash
uv run pytest tests/ -v
```

## Branches

| Branche | Périmètre |
|---|---|
| `main` | Base commune (schemas, config, archi) |
| `elom/dev` | Coeur agent (triage, routing, conversation, pipeline) |

## Stack

- Python 3.11 + uv
- OpenHosta (emulate) + OpenAI gpt-4o
- Pydantic v2
- SQLite (persistence)
- Docker (démo)

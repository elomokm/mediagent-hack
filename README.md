# MediAgent

Agent IA téléphonique de pré-tri médical pour cliniques — Hackathon Hand-e.

L'agent prend les appels patients, collecte les symptômes, évalue l'urgence, oriente vers le bon soin (SAMU / généraliste / pharmacie), réserve un rendez-vous et produit des analytics pour la clinique.

## Installation

```bash
# Prérequis : Python 3.11+ et uv
curl -LsSf https://astral.sh/uv/install.sh | sh  # installer uv

git clone https://github.com/elomokm/mediagent-hack.git
cd mediagent-hack
uv sync

cp .env.example .env
# Remplir OPENHOSTA_DEFAULT_MODEL_API_KEY avec votre clé OpenAI
```

## Utilisation

```bash
# Démo automatique — 3 scénarios (SAMU, RDV, pharmacie)
uv run python -m src.main --demo

# Mode interactif — conversation texte
uv run python -m src.main

# Mode vocal — micro + haut-parleur
uv run python -m src.main --vocal

# KPIs du jour depuis la BDD
uv run python -m src.main --stats

# Docker
docker-compose up --build
```

## Fonctionnalités

### Pendant l'appel
- **Accueil** personnalisé au nom de la clinique
- **Collecte** conversationnelle des infos patient (nom, âge, symptômes, durée)
- **Triage** automatique avec score d'urgence (0→1) et niveau de confiance
- **Orientation** : SAMU (15) si urgence vitale, généraliste, téléconsultation ou pharmacie
- **Booking** : matching médecin par spécialité, proposition de créneaux, choix patient, confirmation

### Après l'appel
- **Sauvegarde** complète en BDD (patient, conversation, orientation, RDV)
- **Analyse sentiment** de l'appel (positif/neutre/négatif/anxieux)
- **Qualification lead** (nouveau patient, potentiel de suivi, motif de contact)
- **KPIs agrégés** : volume d'appels, taux de RDV, durée moyenne, répartition orientations, transferts SAMU

### Mode vocal
- Agent conversationnel autonome (gpt-4o-mini streaming)
- Reconnaissance vocale (OpenAI Whisper)
- Synthèse vocale naturelle (OpenAI TTS, voix nova)

## Architecture

```
src/
├── agent/
│   ├── pipeline.py          # Pipeline texte (OpenHosta emulate)
│   ├── vocal_pipeline.py    # Pipeline vocal (gpt-4o-mini streaming)
│   ├── post_call.py         # Analytics post-appel (OpenHosta)
│   ├── triage.py            # Évaluation urgence
│   ├── care_router.py       # Orientation soin
│   ├── conversation.py      # Collecte patient
│   ├── doctor_matcher.py    # Matching médecin
│   └── summary.py           # Résumé clinique
├── analytics/
│   ├── analyze_call.py      # Sentiment + qualité
│   ├── lead_qualifier.py    # Qualification business
│   ├── call_summarizer.py   # Résumé structuré
│   └── stats.py             # KPIs agrégés
├── tools/
│   ├── data_store.py        # SQLite (5 tables)
│   ├── data_generate.py     # Génération données mock
│   ├── scheduling.py        # Créneaux + booking
│   └── voice.py             # STT/TTS
├── models/schemas.py        # 25+ schemas Pydantic
├── config.py                # Configuration + clinique mock
└── main.py                  # Point d'entrée (4 modes)
```

### Choix d'architecture

| Composant | Technologie | Pourquoi |
|---|---|---|
| Conversation vocale | OpenAI gpt-4o-mini streaming | Fluidité temps réel |
| Décisions typées (triage, orientation, analytics) | OpenHosta emulate | Sorties structurées fiables |
| STT | OpenAI Whisper | Français, même API key |
| TTS | OpenAI TTS (voix nova) | Naturel, même API key |
| Persistence | SQLite | Zéro config, suffisant pour le POC |
| Schemas | Pydantic v2 | Validation stricte, pattern héritage LLM |

## Stack

- Python 3.11 + uv
- OpenHosta + OpenAI (gpt-5 / gpt-4o-mini)
- Pydantic v2
- SQLite
- Docker

## Variables d'environnement (.env)

```
OPENHOSTA_DEFAULT_MODEL_API_KEY="your_openai_api_key"
OPENHOSTA_DEFAULT_MODEL_NAME="gpt-5"
OPENHOSTA_DEFAULT_MODEL_SEED=42
OPENHOSTA_MAX_RETRIES=3
```

## Tests

```bash
uv run pytest tests/ -v
```

## Équipe

Projet réalisé lors du Hackathon Hand-e (36h).

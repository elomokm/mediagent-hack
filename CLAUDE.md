# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projet

Agent IA de pré-tri médical (MediAgent). **Ce n'est pas un outil de diagnostic.**
Il aide à l'orientation patient : urgences / médecin généraliste / téléconsultation / pharmacie.

Hackathon Hand-e — contrainte centrale : OpenHosta pour toutes les décisions typées.

## Stack

- Python 3.11
- OpenHosta — `emulate()` pour chaque décision de l'agent
- OpenHosta + OpenAI gpt-4o 
- Pydantic v2 — tous les schémas de données dans `src/models/`
- Docker — démo via `docker-compose up` puis `python main.py`
- pytest — tests dans `tests/`

## Commandes

```bash
# Install
pip install -r requirements.txt

# Lancer la démo
docker-compose up
python main.py

# Tests
pytest tests/ -v
pytest tests/ -k "test_name" -v          # un seul test

# Tests avec coverage
pytest tests/ --cov=src --cov-report=term-missing
```

## Architecture

```
src/
├── models/       # Types Pydantic — SOURCE DE VÉRITÉ des schémas
├── agent/        # Logique agent : triage, booking, summary, survey
├── tools/        # Intégrations externes (calendar mock, etc.)
└── main.py       # Point d'entrée — orchestration
```

### Flux principal

```
PatientInput
  → collect_symptoms()          # collecte structurée
  → evaluate_urgency()          # score 0.0→1.0 + confiance
  → qualify_care_type()         # type de soin nécessaire
  → [si médecin] find_slot()    # créneau disponible
  → [si médecin] book_appointment()
  → generate_summary()          # résumé pour soignant
  → [post-RDV] send_survey() → analyze_survey()
```

## Règles de développement

1. **Sorties typées uniquement** — jamais de `str` brute en retour d'une décision
2. **Seuil de confiance > 0.9** pour les décisions critiques (urgence vitale)
3. **Chaque fonction OpenHosta** doit avoir : signature Pydantic complète (input + output), docstring métier claire (pas de jargon technique)
4. **Commits conventionnels** : `feat(scope)`, `fix(scope)`, `test(scope)`, `docs(scope)`, `chore(scope)`
5. **Variables d'environnement** dans `.env` — jamais de clés en dur

## Contrainte légale

L'agent ne fait JAMAIS de diagnostic, recommandation de traitement, prescription, ou remplacement d'un professionnel de santé. Toujours rappeler : "En cas de doute, appelez le 15 (SAMU)".

## Variables d'environnement

```
OPENAI_API_KEY=...         # ou ANTHROPIC_API_KEY
OPENHOSTA_MODEL=gpt-4o     # modèle utilisé par emulate()
CALENDAR_MOCK=true         # true = mock, false = vraie API
LOG_LEVEL=INFO
```

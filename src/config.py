"""Configuration centralisée — constantes, seuils et données mock."""

import os

from dotenv import load_dotenv

load_dotenv()

# --- Seuils métier ---

URGENCY_LIFE_THREATENING_SCORE = 0.8
URGENCY_LIFE_THREATENING_CONFIDENCE = 0.9
MAX_CONVERSATION_TURNS = 10

# --- Clinique mock pour la démo ---

MOCK_CLINIC_NAME = "MediSanté"
MOCK_CLINIC_ADDRESS = "12 Rue de la Santé, 75013 Paris"

MOCK_DOCTORS = [
    {"id": "doc1", "nom": "Martin", "prenom": "Sophie", "specialites": ["generaliste"], "lieu": "Cabinet A"},
    {"id": "doc2", "nom": "Bernard", "prenom": "Pierre", "specialites": ["generaliste"], "lieu": "Cabinet A"},
    {"id": "doc3", "nom": "Petit", "prenom": "Marie", "specialites": ["cardiologie"], "lieu": "Cabinet B"},
    {"id": "doc4", "nom": "Durand", "prenom": "Luc", "specialites": ["dermatologie"], "lieu": "Cabinet C"},
    {"id": "doc5", "nom": "Leroy", "prenom": "Anne", "specialites": ["pediatrie"], "lieu": "Cabinet D"},
]

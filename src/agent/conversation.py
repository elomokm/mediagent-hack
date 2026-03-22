"""Gestion de la conversation téléphonique avec le patient."""

import json
import os

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field

from OpenHosta import emulate

from src.models.schemas import PatientInput

load_dotenv()

_client = OpenAI(api_key=os.getenv("OPENHOSTA_DEFAULT_MODEL_API_KEY"))


class ConversationStep(BaseModel):
    """Résultat d'un tour de conversation — extraction + prochaine question en un seul appel."""

    patient_info: PatientInput = Field(description="Informations patient extraites de toute la conversation jusqu'ici")
    next_question: str = Field(description="Prochaine question à poser au patient")
    info_complete: bool = Field(description="True si on a nom, âge, symptômes et durée. False sinon.")


def generate_greeting(clinic_name: str, clinic_address: str) -> str:
    """Génère un message d'accueil téléphonique pour la clinique.

    Tu es l'assistant téléphonique de la clinique {clinic_name}, située au {clinic_address}.
    Génère un accueil professionnel, chaleureux et court (2-3 phrases max).
    Présente-toi, nomme la clinique, et demande comment tu peux aider.
    Ton empathique et rassurant. Pas de jargon médical.
    """
    return emulate()


_CONVERSATION_PROMPT = """Analyse la conversation ci-dessous et retourne un JSON avec :
1. patient_info : les infos extraites (nom, age, sexe, symptomes, duree_symptomes, antecedents)
2. next_question : la prochaine question à poser
3. info_complete : true si on a nom + âge + symptômes + durée

Valeurs par défaut si NON mentionné : nom="Inconnu", age=0, sexe="non précisé", symptomes=[], duree_symptomes="non précisé", antecedents=[]
antecedents est TOUJOURS une liste (jamais un string).

Priorité des questions : 1) nom 2) âge 3) symptômes 4) durée
Ton empathique et professionnel. UNE question à la fois. 2-3 phrases max.

Retourne UNIQUEMENT le JSON, rien d'autre :
{"patient_info": {"nom": "...", "age": 0, "sexe": "non précisé", "symptomes": [], "duree_symptomes": "non précisé", "antecedents": []}, "next_question": "...", "info_complete": false}"""


def process_conversation_turn(conversation_text: str) -> ConversationStep:
    """Analyse la conversation via API OpenAI directe (plus fiable que emulate pour le parsing)."""
    response = _client.chat.completions.create(
        model=os.getenv("OPENHOSTA_DEFAULT_MODEL_NAME", "gpt-4o"),
        messages=[
            {"role": "system", "content": _CONVERSATION_PROMPT},
            {"role": "user", "content": conversation_text},
        ],
        response_format={"type": "json_object"},
    )

    text = response.choices[0].message.content
    data = json.loads(text)

    patient_data = data.get("patient_info", {})
    # S'assurer que antecedents est une liste
    antecedents = patient_data.get("antecedents", [])
    if not isinstance(antecedents, list):
        antecedents = []

    patient = PatientInput(
        nom=patient_data.get("nom", "Inconnu"),
        age=patient_data.get("age", 0),
        sexe=patient_data.get("sexe", "non précisé"),
        symptomes=patient_data.get("symptomes", []),
        duree_symptomes=patient_data.get("duree_symptomes", "non précisé"),
        antecedents=antecedents,
    )

    return ConversationStep(
        patient_info=patient,
        next_question=data.get("next_question", "Comment puis-je vous aider ?"),
        info_complete=data.get("info_complete", False),
    )


def has_sufficient_info(patient: PatientInput) -> bool:
    """Vérifie que les informations minimales sont collectées pour le triage."""
    return (
        patient.nom != "Inconnu"
        and patient.age > 0
        and len(patient.symptomes) > 0
        and patient.duree_symptomes != "non précisé"
    )

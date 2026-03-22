"""Orientation du patient vers le type de soin adapté."""

import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from src.models.schemas import PatientInput, UrgencyScore, CareRecommendation

load_dotenv()

_client = OpenAI(api_key=os.getenv("OPENHOSTA_DEFAULT_MODEL_API_KEY"))

_CARE_PROMPT = """Détermine le type de soin adapté pour le patient selon son urgence et ses symptômes.

Orientations possibles :
- "urgences" : score > 0.6, ou symptômes nécessitant prise en charge hospitalière
- "generaliste" : symptômes persistants ou chroniques nécessitant un examen
- "teleconsultation" : suivi de routine, renouvellement, question simple
- "pharmacie" : symptômes bénins gérables sans ordonnance

Le message_patient doit être en français, 2-3 phrases max, clair et rassurant, sans jargon médical.
Ceci n'est PAS un diagnostic. En cas de doute, orienter vers le 15 (SAMU).

Retourne UNIQUEMENT ce JSON :
{"care_type": "generaliste", "urgency_score": {"score": 0.0, "confidence": 0.0, "reasoning": "..."}, "message_patient": "..."}"""


def qualify_care_type(patient: PatientInput, urgency: UrgencyScore) -> CareRecommendation:
    """Détermine le type de soin adapté pour le patient."""
    input_data = json.dumps({
        "patient": patient.model_dump(),
        "urgency": urgency.model_dump(),
    }, ensure_ascii=False)

    response = _client.chat.completions.create(
        model=os.getenv("OPENHOSTA_DEFAULT_MODEL_NAME", "gpt-4o"),
        messages=[
            {"role": "system", "content": _CARE_PROMPT},
            {"role": "user", "content": input_data},
        ],
        response_format={"type": "json_object"},
    )

    data = json.loads(response.choices[0].message.content)

    # Reconstruire l'UrgencyScore depuis les données existantes (pas celui du LLM)
    return CareRecommendation(
        care_type=data.get("care_type", "generaliste"),
        urgency_score=urgency,
        message_patient=data.get("message_patient", "Veuillez consulter un médecin."),
    )

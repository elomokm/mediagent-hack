"""Matching symptômes patient → médecin adapté dans le parc de la clinique."""

import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from src.models.schemas import PatientInput, CareRecommendation

load_dotenv()

_client = OpenAI(api_key=os.getenv("OPENHOSTA_DEFAULT_MODEL_API_KEY"))

_MATCHER_PROMPT = """Choisis le médecin le plus adapté pour ce patient parmi les médecins disponibles.

Critères :
- Spécialité correspondant aux symptômes
- Type de soin recommandé
- En cas de doute, orienter vers le généraliste

Retourne UNIQUEMENT ce JSON :
{"doctor_id": "..."}"""


def match_doctor(
    patient: PatientInput,
    care_recommendation: CareRecommendation,
    available_doctors: list[dict],
) -> str:
    """Choisit le médecin le plus adapté. Retourne l'id du médecin."""
    input_data = json.dumps({
        "patient": patient.model_dump(),
        "care": care_recommendation.model_dump(),
        "doctors": available_doctors,
    }, ensure_ascii=False, default=str)

    response = _client.chat.completions.create(
        model=os.getenv("OPENHOSTA_DEFAULT_MODEL_NAME", "gpt-4o"),
        messages=[
            {"role": "system", "content": _MATCHER_PROMPT},
            {"role": "user", "content": input_data},
        ],
        response_format={"type": "json_object"},
    )

    data = json.loads(response.choices[0].message.content)
    return data.get("doctor_id", available_doctors[0]["id"] if available_doctors else "")

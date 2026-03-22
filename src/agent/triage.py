"""Évaluation de l'urgence médicale et décision de transfert SAMU."""

import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from src.models.schemas import PatientInput, UrgencyScore

load_dotenv()

_client = OpenAI(api_key=os.getenv("OPENHOSTA_DEFAULT_MODEL_API_KEY"))

URGENCY_LIFE_THREATENING_SCORE = 0.8
URGENCY_LIFE_THREATENING_CONFIDENCE = 0.9

_TRIAGE_PROMPT = """Évalue le niveau d'urgence médicale du patient.

Règles de scoring :
- 0.9-1.0 : urgence vitale (douleur thoracique, AVC, détresse respiratoire, hémorragie, perte de conscience, réaction allergique sévère)
- 0.6-0.8 : urgence relative (fièvre élevée persistante, douleur intense, traumatisme modéré)
- 0.3-0.5 : consultation recommandée (symptômes persistants, gêne quotidienne)
- 0.0-0.2 : faible urgence (symptômes légers, conseil pharmacie suffisant)

La confiance reflète la certitude. Symptômes ambigus ou insuffisants = confiance basse.
Ceci n'est PAS un diagnostic. En cas de doute, score élevé par précaution.

Retourne UNIQUEMENT ce JSON :
{"score": 0.0, "confidence": 0.0, "reasoning": "explication"}"""


def evaluate_urgency(patient: PatientInput) -> UrgencyScore:
    """Évalue le niveau d'urgence médicale d'un patient."""
    response = _client.chat.completions.create(
        model=os.getenv("OPENHOSTA_DEFAULT_MODEL_NAME", "gpt-4o"),
        messages=[
            {"role": "system", "content": _TRIAGE_PROMPT},
            {"role": "user", "content": patient.model_dump_json()},
        ],
        response_format={"type": "json_object"},
    )

    data = json.loads(response.choices[0].message.content)
    return UrgencyScore(
        score=data.get("score", 0.5),
        confidence=data.get("confidence", 0.5),
        reasoning=data.get("reasoning", ""),
    )


def is_life_threatening(urgency: UrgencyScore) -> bool:
    """Détermine si l'urgence nécessite un transfert immédiat vers le SAMU (15)."""
    return (
        urgency.score >= URGENCY_LIFE_THREATENING_SCORE
        and urgency.confidence >= URGENCY_LIFE_THREATENING_CONFIDENCE
    )

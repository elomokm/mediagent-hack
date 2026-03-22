"""Analyse post-appel — sentiment, thèmes, qualité."""

import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from src.models.schemas import CallAnalysis

load_dotenv()

_client = OpenAI(api_key=os.getenv("OPENHOSTA_DEFAULT_MODEL_API_KEY"))

_ANALYSIS_PROMPT = """Analyse la qualité de cette conversation téléphonique médicale.

Détermine :
- sentiment_global : "positif", "neutre", "negatif" ou "anxieux" (TOUT EN MINUSCULES)
- themes_principaux : sujets majeurs abordés (ex: ["prise de rdv", "maux de tête"])
- qualite_interaction : score de 0.0 à 1.0
- notes_amelioration : suggestions pour améliorer les futures interactions

Retourne UNIQUEMENT ce JSON :
{"sentiment_global": "neutre", "themes_principaux": ["..."], "qualite_interaction": 0.8, "notes_amelioration": ["..."]}"""


def analyze_call(text: str, call_id: str, duree: float) -> CallAnalysis:
    """Analyse complète de l'appel — sentiment + insights."""
    response = _client.chat.completions.create(
        model=os.getenv("OPENHOSTA_DEFAULT_MODEL_NAME", "gpt-4o"),
        messages=[
            {"role": "system", "content": _ANALYSIS_PROMPT},
            {"role": "user", "content": text},
        ],
        response_format={"type": "json_object"},
    )

    data = json.loads(response.choices[0].message.content)

    return CallAnalysis(
        call_id=call_id,
        duree_secondes=duree,
        sentiment_global=data.get("sentiment_global", "neutre").lower(),
        themes_principaux=data.get("themes_principaux", []),
        qualite_interaction=data.get("qualite_interaction", 0.5),
        notes_amelioration=data.get("notes_amelioration", []),
    )

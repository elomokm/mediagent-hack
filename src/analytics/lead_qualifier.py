"""Qualification des leads patient pour la clinique."""

import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from src.models.schemas import LeadQualification

load_dotenv()

_client = OpenAI(api_key=os.getenv("OPENHOSTA_DEFAULT_MODEL_API_KEY"))

_LEAD_PROMPT = """Qualifie le potentiel business d'un patient pour la clinique à partir de la conversation.

Détermine :
- est_nouveau_patient : true si première visite (indices : "je ne suis jamais venu", pas de référence à un médecin de la clinique). false si récurrent.
- motif_contact : "premier_avis", "suivi", "renouvellement", "urgence_ressentie" ou "information"
- potentiel_suivi : true si pathologie chronique ou besoin de consultations régulières
- source_decouverte : comment le patient a connu la clinique. null si non mentionné.

Retourne UNIQUEMENT ce JSON :
{"est_nouveau_patient": true, "motif_contact": "premier_avis", "potentiel_suivi": false, "source_decouverte": null}"""


def qualify_lead(conversation_text: str, call_id: str, patient_nom: str) -> LeadQualification:
    """Qualifie le potentiel business d'un patient."""
    response = _client.chat.completions.create(
        model=os.getenv("OPENHOSTA_DEFAULT_MODEL_NAME", "gpt-4o"),
        messages=[
            {"role": "system", "content": _LEAD_PROMPT},
            {"role": "user", "content": conversation_text},
        ],
        response_format={"type": "json_object"},
    )

    data = json.loads(response.choices[0].message.content)

    return LeadQualification(
        call_id=call_id,
        patient_nom=patient_nom,
        est_nouveau_patient=data.get("est_nouveau_patient", True),
        motif_contact=data.get("motif_contact", "premier_avis"),
        potentiel_suivi=data.get("potentiel_suivi", False),
        source_decouverte=data.get("source_decouverte"),
    )

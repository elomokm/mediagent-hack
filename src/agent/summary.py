from OpenHosta import emulate
from pydantic import BaseModel, Field

from models.schemas import (
    CallSummaryGenerated,
    CallSummaryStructured,
    CareRecommendation,
    ClinicalSummary,
    PatientInput,
)


# --- Internal Classes for Granular Inference ---
class _ClinicalNotes(BaseModel):
    """Internal schema for textual notes extraction."""

    symptoms_summary: str = Field(
        description="Synthèse courte et médicale des symptômes rapportés."
    )
    notes_for_provider: str = Field(
        description="Détails cliniques, antécédents et points de vigilance pour le médecin."
    )


# --- Inference Layer (Specialized AI Functions) ---


def _extract_patient_data(text: str) -> PatientInput:
    """
    Extrait l'identité, l'âge, le sexe, les symptômes et les antécédents du patient.

    Exemple de sortie :
    {
      "nom": "Jean Martin",
      "age": 45,
      "sexe": "homme",
      "symptomes": ["douleur thoracique"],
      "duree_symptomes": "2 heures",
      "antecedents": ["hypertension"]
    }
    """
    return emulate()


def _extract_triage_decision(text: str) -> CareRecommendation:
    """
    Évalue l'urgence et recommande l'orientation médicale la plus adaptée.

    CONSIGNES STRICTES :
    - care_type : DOIT être l'un des suivants : 'urgences', 'generaliste', 'teleconsultation', 'pharmacie'.

    Exemple de sortie :
    {
      "care_type": "urgences",
      "urgency_score": {"score": 0.85, "confidence": 0.95, "reasoning": "Douleur thoracique aiguë"},
      "message_patient": "Veuillez vous rendre aux urgences immédiatement."
    }
    """
    return emulate()


def _extract_notes_only(text: str) -> _ClinicalNotes:
    """
    Génère le résumé clinique condensé et les notes techniques pour le praticien.

    Exemple de sortie :
    {
      "symptoms_summary": "Douleur rétro-sternale irradiante depuis 2h.",
      "notes_for_provider": "Patient anxieux, antécédents HT à surveiller."
    }
    """
    return emulate()


def _extract_call_summary_inference(text: str) -> CallSummaryGenerated:
    """
    Extrait les données nécessaires au résumé administratif (dashboard).

    Exemple de sortie :
    {
      "patient_nom": "Jean Martin",
      "motif_appel": "Douleur thoracique",
      "symptomes_reportes": ["douleur poitrine"],
      "urgency_score": 0.85,
      "urgency_confidence": 0.95,
      "orientation": "urgences",
      "rdv_pris": false,
      "doctor_name": null
    }
    """
    return emulate()


# --- Orchestration Layer (Public Functions) ---


def generate_clinical_summary(text: str) -> ClinicalSummary:
    """
    Génère un résumé médical complet en combinant plusieurs extractions spécialisées.
    C'est la brique principale pour l'usage du médecin.
    """
    # 1. Extractions parallèles par thématiques
    patient = _extract_patient_data(text)
    care_rec = _extract_triage_decision(text)
    notes = _extract_notes_only(text)

    # 2. Assemblage final respectant le schéma ClinicalSummary
    return ClinicalSummary(
        patient=patient,
        care_recommendation=care_rec,
        symptoms_summary=notes.symptoms_summary,
        notes_for_provider=notes.notes_for_provider,
    )


def generate_call_summary(text: str, call_id: str) -> CallSummaryStructured:
    """
    Génère un résumé structuré pour le dashboard administratif.
    Associe les données générées par l'IA à l'identifiant système.
    """
    # 1. Extraction des données métier par l'IA
    summary_generated = _extract_call_summary_inference(text)

    # 2. Injection des métadonnées système (call_id)
    return CallSummaryStructured(**summary_generated.model_dump(), call_id=call_id)

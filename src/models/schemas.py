"""Schémas Pydantic — source de vérité pour tous les types MediAgent."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class PatientInput(BaseModel):
    nom: str = Field(
        description="Nom complet du patient (utiliser 'Inconnu' si non mentionné)."
    )
    age: int = Field(description="Âge du patient en années.")
    sexe: str = Field(description="Sexe biologique du patient (homme, femme ou autre).")
    symptomes: list[str] = Field(
        description="Liste des symptômes physiques ou psychologiques rapportés."
    )
    duree_symptomes: str = Field(
        description="Durée depuis l'apparition des symptômes (ex: '2 jours', '1 semaine')."
    )
    antecedents: list[str] = Field(
        default_factory=list,
        description="Liste des pathologies, allergies ou antécédents médicaux notables.",
    )


class UrgencyScore(BaseModel):
    score: float = Field(ge=0.0, le=1.0, description="Score d'urgence 0→1")
    confidence: float = Field(ge=0.0, le=1.0, description="Confiance dans l'évaluation")
    reasoning: str = Field(description="Explication du score")


class CareType(str, Enum):
    URGENCES = "urgences"
    GENERALISTE = "generaliste"
    TELECONSULTATION = "teleconsultation"
    PHARMACIE = "pharmacie"


class CareRecommendation(BaseModel):
    care_type: CareType = Field(
        description="Type d'orientation recommandé (doit correspondre exactement aux valeurs de CareType : urgences, generaliste, teleconsultation, pharmacie)"
    )
    urgency_score: UrgencyScore
    message_patient: str = Field(description="Message clair pour le patient")


class TimeSlot(BaseModel):
    datetime_start: datetime
    datetime_end: datetime
    doctor_name: str
    location: str


class Appointment(BaseModel):
    slot: TimeSlot
    patient_name: str
    confirmed: bool = False
    confirmation_id: str | None = None


class ClinicalSummary(BaseModel):
    patient: PatientInput
    urgency: UrgencyScore
    care_recommendation: CareRecommendation
    symptoms_summary: str = Field(
        description="Résumé synthétique et structuré des symptômes pour une lecture rapide par le médecin."
    )
    notes_for_provider: str = Field(
        description="Notes cliniques détaillées, incluant les antécédents, les points de vigilance et tout élément utile au diagnostic."
    )


class SurveyResponse(BaseModel):
    rating: int = Field(ge=1, le=5)
    comment: str = ""
    appointment_id: str


class SurveyAnalysis(BaseModel):
    sentiment: str
    key_themes: list[str]
    improvement_suggestions: list[str]


# --- Session d'appel ---


class CallStatus(str, Enum):
    EN_COURS = "en_cours"
    TERMINE = "termine"
    TRANSFERE_SAMU = "transfere_samu"
    ABANDONNE = "abandonne"


class ConversationTurn(BaseModel):
    role: str = Field(description="'agent' ou 'patient'")
    message: str
    timestamp: datetime


class CallSession(BaseModel):
    call_id: str
    clinic_id: str
    timestamp_start: datetime
    timestamp_end: datetime | None = None
    status: CallStatus = CallStatus.EN_COURS
    conversation: list[ConversationTurn] = Field(default_factory=list)
    patient: PatientInput | None = None


# --- Analytics ---
class CallSentiment(str, Enum):
    POSITIF = "positif"
    NEUTRE = "neutre"
    NEGATIF = "negatif"
    ANXIEUX = "anxieux"


class CallAnalysisGenerated(BaseModel):
    """Généré par le modèle"""

    sentiment_global: CallSentiment = Field(
        description="Sentiment général (valeurs autorisées : positif, neutre, negatif, anxieux - TOUT EN MINUSCULES)"
    )
    themes_principaux: list[str] = Field(
        description="Sujets majeurs abordés pendant la conversation"
    )
    qualite_interaction: float = Field(
        ge=0.0,
        le=1.0,
        description="Score d'évaluation de la qualité de l'échange (0.0 à 1.0)",
    )
    notes_amelioration: list[str] = Field(
        default_factory=list,
        description="Suggestions pour améliorer les futures interactions",
    )


class CallAnalysis(CallAnalysisGenerated):
    """Le modèle final complet (qui hérite des champs générés)"""

    call_id: str
    duree_secondes: float


# --------- Si l'agent n'a pas de mémoire ----------


class CallSummaryGenerated(BaseModel):
    """Informations extraites et résumées par l'IA à partir de la conversation."""

    patient_nom: str = Field(description="Nom du patient (ou 'Inconnu')")
    motif_appel: str = Field(description="Raison principale de l'appel")
    symptomes_reportes: list[str] = Field(description="Liste des symptômes cités")
    urgency_score: float = Field(
        ge=0.0, le=1.0, description="Niveau d'urgence évalué (0.0 à 1.0)"
    )
    urgency_confidence: float = Field(
        ge=0.0, le=1.0, description="Confiance dans l'évaluation d'urgence"
    )
    orientation: CareType = Field(
        description="Type d'orientation recommandé (doit correspondre exactement aux valeurs de CareType : urgences, generaliste, teleconsultation, pharmacie)"
    )
    rdv_pris: bool = Field(description="Indique si un rendez-vous a été planifié")
    doctor_name: str | None = Field(
        default=None, description="Nom du médecin si un RDV est pris"
    )


class CallSummaryStructured(CallSummaryGenerated):
    """Modèle complet incluant les identifiants système."""

    call_id: str


# -------------- Si l'agent a une mémoire --------------


# class CallSummaryStructured(BaseModel):
#     """Modèle complet incluant les identifiants système."""

#     call_id: str
#     urgency_confidence: float = Field(
#         ge=0.0, le=1.0, description="Confiance dans l'évaluation d'urgence"
#     )
#     orientation: CareType = Field(
#         description="Type d'orientation recommandé (doit correspondre exactement aux valeurs de CareType : urgences, generaliste, teleconsultation, pharmacie)"
#     )
#     rdv_pris: bool = Field(description="Indique si un rendez-vous a été planifié")
#     doctor_name: str | None = Field(
#         default=None, description="Nom du médecin si un RDV est pris"
#     )
#     patient_nom: str = Field(description="Nom du patient (ou 'Inconnu')")
#     motif_appel: str = Field(description="Raison principale de l'appel")
#     symptomes_reportes: list[str] = Field(description="Liste des symptômes cités")
#     urgency_score: float = Field(
#         ge=0.0, le=1.0, description="Niveau d'urgence évalué (0.0 à 1.0)"
#     )

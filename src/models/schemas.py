"""Schémas Pydantic — source de vérité pour tous les types MediAgent."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class PatientInput(BaseModel):
    nom: str
    age: int
    sexe: str
    symptomes: list[str]
    duree_symptomes: str = Field(description="Depuis quand les symptômes sont présents")
    antecedents: list[str] = Field(default_factory=list)


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
    care_type: CareType
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
    symptoms_summary: str
    notes_for_provider: str


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


class CallAnalysis(BaseModel):
    call_id: str
    duree_secondes: float
    sentiment_global: CallSentiment
    themes_principaux: list[str]
    qualite_interaction: float = Field(ge=0.0, le=1.0)
    notes_amelioration: list[str] = Field(default_factory=list)


class CallSummaryStructured(BaseModel):
    call_id: str = Field(description="Un identifiant unique pour l'appel (à générer s'il n'est pas fourni)")
    patient_nom: str = Field(description="Le nom complet ou partiel du patient")
    motif_appel: str = Field(description="La raison principale de l'appel")
    symptomes_reportes: list[str] = Field(description="Liste des symptômes médicaux formulés par le patient")
    urgency_score: float = Field(ge=0.0, le=1.0, description="Score d'urgence estimé (entre 0.0 et 1.0)")
    urgency_confidence: float = Field(ge=0.0, le=1.0, description="Niveau de confiance dans l'estimation de l'urgence (entre 0.0 et 1.0)")
    orientation: CareType = Field(description="Type de prise en charge recommandé (urgences, generaliste, teleconsultation, pharmacie)")
    rdv_pris: bool = Field(description="Indique par un booléen si un rendez-vous a été planifié (True) ou non (False)")
    doctor_name: str | None = Field(default=None, description="Le nom du docteur si un médecin a été consulté ou si un rendez-vous a été pris")
    resume_libre: str = Field(description="Un résumé précis et rédigé du problème, des actions accomplies et du ressenti observé")

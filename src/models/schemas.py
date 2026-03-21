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


# --- Clinique & Médecins ---


class Specialite(str, Enum):
    GENERALISTE = "generaliste"
    PEDIATRIE = "pediatrie"
    DERMATOLOGIE = "dermatologie"
    CARDIOLOGIE = "cardiologie"
    ORL = "orl"
    GYNECOLOGIE = "gynecologie"
    OPHTALMOLOGIE = "ophtalmologie"


class Doctor(BaseModel):
    id: str
    nom: str
    prenom: str
    specialites: list[Specialite]
    lieu: str
    duree_consultation_min: int = 30


class Clinic(BaseModel):
    id: str
    nom: str
    adresse: str
    telephone: str
    horaires_ouverture: str
    doctors: list[Doctor] = Field(default_factory=list)


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
    call_id: str = Field(description="Identifiant unique de l'appel")
    patient_nom: str = Field(description="Nom complet ou partiel du patient")
    motif_appel: str = Field(description="Raison principale de l'appel")
    symptomes_reportes: list[str] = Field(description="Liste des symptômes médicaux formulés par le patient")
    urgency_score: float = Field(ge=0.0, le=1.0, description="Score d'urgence estimé")
    urgency_confidence: float = Field(ge=0.0, le=1.0, description="Niveau de confiance dans l'estimation de l'urgence")
    orientation: CareType = Field(description="Type de prise en charge recommandé")
    rdv_pris: bool = Field(description="Indique si un rendez-vous a été planifié")
    doctor_name: str | None = Field(default=None, description="Nom du médecin si un RDV a été pris")
    resume_libre: str = Field(description="Résumé rédigé du problème, des actions accomplies et du ressenti observé")


class LeadQualification(BaseModel):
    call_id: str
    patient_nom: str
    est_nouveau_patient: bool
    motif_contact: str
    potentiel_suivi: bool
    source_decouverte: str | None = None


class DailyStats(BaseModel):
    date: str
    total_appels: int
    appels_par_orientation: dict[str, int]
    duree_moyenne_secondes: float
    taux_rdv_pris: float = Field(ge=0.0, le=1.0)
    urgences_detectees: int
    transferts_samu: int
    sentiment_distribution: dict[str, int]
    top_motifs: list[str]


class CallLog(BaseModel):
    session: CallSession
    summary: CallSummaryStructured | None = None
    analysis: CallAnalysis | None = None
    lead: LeadQualification | None = None
    clinical_summary: ClinicalSummary | None = None

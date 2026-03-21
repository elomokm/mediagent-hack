"""Schémas Pydantic — source de vérité pour tous les types MediAgent."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, NaiveDatetime

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

class Medical_unit_type(str, Enum):
    GENERALISTE = "generaliste"
    PEDIATRIE = "pediatrie"
    DERMATOLOGIE = "dermatologie"
    CARDIOLOGIE = "cardiologie"
    ORL = "orl"
    GYNECOLOGIE = "gynecologie"
    OPHTALMOLOGIE = "ophtalmologie"

class Specialite(BaseModel):
    medical_unit : Medical_unit_type

class Doctor(BaseModel):
    name : str
    id : str
    speciality : Medical_unit_type
    place : str

class DoctorSchedule(BaseModel):
    name_doctor : str
    available_slot : list[datetime]
    occuped_slot : list[datetime]

class Clinic(BaseModel):
    nom : str
    adress : str
    doctors : list[Doctor]
    horaire : list[DoctorSchedule]

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
    conversation: list[ConversationTurn] =           Field(default_factory=list)
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
    call_id: str
    patient_nom: str
    motif_appel: str
    symptomes_reportes: list[str]
    urgency_score: float
    urgency_confidence: float
    orientation: CareType
    rdv_pris: bool
    doctor_name: str | None = None
    resume_libre: str

class LeadQualification(BaseModel):
    new_patient = bool
    potential_follow = bool
    motive = str

class DailyStats(BaseModel):
    nb_calls: int = Field(ge=0, le=100000)
    taux_rdv: int = Field(ge=0.0, le=1.0)
    patient_name = str


# | `DailyStats` | Stats agrégées par jour (volume, taux RDV, etc.) |
# | `DailyStats` | Stats agrégées par jour (volume, taux RDV, etc.) |
# 


# | `LeadQualification` | Qualif. lead (nouveau patient, potentiel suivi, motif) |



# | `LeadQualification` | Qualif. lead (nouveau patient, potentiel suivi, motif) |

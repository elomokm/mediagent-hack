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


class ConversationTurn(BaseModel):
    role: str
    message: str
    timestamp: NaiveDatetime


class CallSession(BaseModel):
    conversation: list[ConversationTurn]


class CallSentiment(str, Enum):
    POSITIF = "positif"
    NEUTRE = "neutre"
    NEGATIF = "negatif"
    ANXIEUX = "anxieux"


class CallAnalysis(BaseModel):
    duration: float  # Durée en secondes
    total_turns: int  # Nombre de messages dans la conversation

    @classmethod
    def analyze_session(cls, session: CallSession) -> "CallAnalysis":
        turns = session.conversation

        if not turns:
            return cls(duration=0.0, total_turns=0)

        debut = turns[0].timestamp
        fin = turns[-1].timestamp

        return cls(duration=(fin - debut).total_seconds(), total_turns=len(turns))


class CallSummaryStructured(BaseModel):
    patient_problem: str = Field(
        description="Résumé court du problème ou motif d'appel du patient"
    )
    agent_actions: list[str] = Field(
        description="Liste des actions effectuées par l'agent (ex: orientation, prise de RDV, etc.)"
    )
    patient_overall_feeling: str = Field(
        description="Ressenti global du patient concernant la consultation (ex: rassuré, frustré, confiant, confus)"
    )
    influencing_factors: list[str] = Field(
        description="Éléments de la conversation ayant influencé ce ressenti (ex: clarté des réponses, empathie de l'agent, temps passé)"
    )

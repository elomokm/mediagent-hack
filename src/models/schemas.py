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

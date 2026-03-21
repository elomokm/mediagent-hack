"""Orchestrateur principal du flux d'appel patient."""

from datetime import datetime

from src.agent.conversation import (
    extract_patient_info,
    generate_greeting,
    generate_next_question,
    has_sufficient_info,
)
from src.agent.triage import evaluate_urgency, is_life_threatening
from src.agent.care_router import qualify_care_type
from src.agent.doctor_matcher import match_doctor
from src.models.schemas import CareType, PatientInput

MAX_CONVERSATION_TURNS = 10


class MediAgentPipeline:
    """Orchestre le flux complet d'un appel patient pour une clinique."""

    def __init__(self, clinic_name: str, clinic_address: str, doctors: list[dict]):
        self.clinic_name = clinic_name
        self.clinic_address = clinic_address
        self.doctors = doctors
        self.history: list[str] = []
        self.timestamp_start: datetime | None = None
        self.timestamp_end: datetime | None = None

    def handle_call(self) -> dict:
        """Exécute le flux complet d'un appel. Retourne un résumé de l'appel."""
        self.timestamp_start = datetime.now()

        # 1. Accueil
        self._greet()

        # 2. Collecte des informations patient
        patient = self._collect_info()

        # 3. Triage urgence
        urgency = evaluate_urgency(patient)
        print(f"\n[TRIAGE] Score: {urgency.score} | Confiance: {urgency.confidence}")
        print(f"[TRIAGE] Raison: {urgency.reasoning}")

        if is_life_threatening(urgency):
            return self._handle_samu(patient, urgency)

        # 4. Orientation soin
        care = qualify_care_type(patient, urgency)
        self._agent_says(care.message_patient)

        # 5. Booking si nécessaire
        appointment_info = None
        if care.care_type in (CareType.GENERALISTE, CareType.TELECONSULTATION):
            appointment_info = self._book(patient, care)

        # 6. Clôture
        return self._finalize(patient, urgency, care, appointment_info)

    def _greet(self):
        greeting = generate_greeting(self.clinic_name, self.clinic_address)
        self._agent_says(greeting)

    def _collect_info(self) -> PatientInput:
        patient = PatientInput(
            nom="Inconnu",
            age=0,
            sexe="non précisé",
            symptomes=[],
            duree_symptomes="non précisé",
        )

        for _ in range(MAX_CONVERSATION_TURNS):
            question = generate_next_question(patient, self.history)
            self._agent_says(question)

            response = input("\n> ")
            self.history.append(f"Agent: {question}")
            self.history.append(f"Patient: {response}")

            patient = extract_patient_info(self.history)

            if has_sufficient_info(patient):
                break

        return patient

    def _handle_samu(self, patient, urgency) -> dict:
        self._agent_says(
            "Vos symptômes nécessitent une prise en charge immédiate. "
            "Je vous transfère vers le SAMU (15). Ne raccrochez pas."
        )
        self.timestamp_end = datetime.now()
        return {
            "status": "TRANSFERE_SAMU",
            "patient": patient.model_dump(),
            "urgency": urgency.model_dump(),
            "duration_seconds": (self.timestamp_end - self.timestamp_start).total_seconds(),
        }

    def _book(self, patient, care) -> dict | None:
        doctor_id = match_doctor(patient, care, self.doctors)
        matched = next((d for d in self.doctors if d["id"] == doctor_id), None)

        if matched:
            doctor_name = f"Dr. {matched['prenom']} {matched['nom']}"
            self._agent_says(
                f"Je vous oriente vers {doctor_name}. "
                "Un créneau sera réservé pour vous prochainement."
            )
            # TODO: remplacer par scheduling.find_available_slots + book_slot
            return {"doctor_id": doctor_id, "doctor_name": doctor_name, "booked": False}

        self._agent_says(
            "Je n'ai pas trouvé de médecin disponible pour le moment. "
            "Nous vous recontacterons dès qu'un créneau se libère."
        )
        return None

    def _finalize(self, patient, urgency, care, appointment_info) -> dict:
        self._agent_says(
            "Merci pour votre appel. N'hésitez pas à rappeler si besoin. "
            "En cas de doute, appelez le 15 (SAMU). Bonne journée."
        )
        self.timestamp_end = datetime.now()
        duration = (self.timestamp_end - self.timestamp_start).total_seconds()

        result = {
            "status": "TERMINE",
            "patient": patient.model_dump(),
            "urgency": urgency.model_dump(),
            "care": care.model_dump(),
            "appointment": appointment_info,
            "duration_seconds": duration,
        }

        print("\n" + "=" * 50)
        print(f"  RÉCAP APPEL")
        print(f"  Durée       : {duration:.0f}s")
        print(f"  Orientation : {care.care_type.value}")
        print(f"  Urgence     : {urgency.score}/1.0 (confiance {urgency.confidence})")
        if appointment_info:
            print(f"  Médecin     : {appointment_info['doctor_name']}")
        print("=" * 50)

        return result

    def _agent_says(self, message: str):
        print(f"\n🏥 Agent: {message}")

"""Orchestrateur principal du flux d'appel patient."""

from datetime import datetime

from src.agent.conversation import (
    generate_greeting,
    process_conversation_turn,
    has_sufficient_info,
)
from src.agent.triage import evaluate_urgency, is_life_threatening
from src.agent.care_router import qualify_care_type
from src.agent.doctor_matcher import match_doctor
from src.models.schemas import CareType, PatientInput
from src.tools.scheduling import find_available_slots, find_alternative_doctor, book_slot
from src.agent.post_call import run_post_call_analytics

MAX_CONVERSATION_TURNS = 10


class MediAgentPipeline:
    """Orchestre le flux complet d'un appel patient pour une clinique."""

    def __init__(self, clinic_name: str, clinic_address: str, doctors: list[dict],
                 patient_responses: list[str] | None = None, vocal: bool = False):
        self.clinic_name = clinic_name
        self.clinic_address = clinic_address
        self.doctors = doctors
        self.history: list[str] = []
        self.timestamp_start: datetime | None = None
        self.timestamp_end: datetime | None = None
        self.vocal = vocal
        # Mode démo : réponses pré-remplies
        self._responses = list(patient_responses) if patient_responses else None
        self._response_idx = 0

    def _get_patient_input(self) -> str:
        """Récupère la réponse du patient — input(), vocal ou réponses pré-remplies."""
        if self._responses and self._response_idx < len(self._responses):
            response = self._responses[self._response_idx]
            self._response_idx += 1
            print(f"\n> {response}")
            return response
        if self.vocal:
            from src.tools.voice import speech_to_text
            response = speech_to_text()
            print(f"\n> {response}")
            return response
        return input("\n> ")

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
            # UN SEUL appel emulate() par tour : extraction + question
            history_text = "\n".join(self.history) if self.history else "Début de conversation."
            step = process_conversation_turn(history_text)

            patient = step.patient_info

            if step.info_complete and has_sufficient_info(patient):
                self._agent_says("Merci, j'ai toutes les informations nécessaires. Je vais analyser votre situation.")
                break

            self._agent_says(step.next_question)
            response = self._get_patient_input()
            self.history.append(f"Agent: {step.next_question}")
            self.history.append(f"Patient: {response}")

        return patient

    def _handle_samu(self, patient, urgency) -> dict:
        self._agent_says(
            "Vos symptômes nécessitent une prise en charge immédiate. "
            "Je vous transfère vers le SAMU (15). Ne raccrochez pas."
        )
        self.timestamp_end = datetime.now()
        result = {
            "status": "TRANSFERE_SAMU",
            "patient": patient.model_dump(),
            "urgency": urgency.model_dump(),
            "care_type": "urgences",
            "orientation": "urgences",
            "duration_seconds": (self.timestamp_end - self.timestamp_start).total_seconds(),
            "timestamp_start": self.timestamp_start,
        }

        # Persistence + analytics post-appel
        conversation_text = "\n".join(self.history)
        run_post_call_analytics(result, conversation_text)

        return result

    def _book(self, patient, care) -> dict | None:
        doctor_id = match_doctor(patient, care, self.doctors)

        slots = find_available_slots(doctor_id, self.doctors)

        if not slots:
            alt_id = find_alternative_doctor(doctor_id, self.doctors)
            if alt_id:
                doctor_id = alt_id
                slots = find_available_slots(doctor_id, self.doctors)

        if not slots:
            self._agent_says(
                "Je n'ai pas trouvé de créneau disponible pour le moment. "
                "Nous vous recontacterons dès qu'un créneau se libère."
            )
            return None

        matched = next((d for d in self.doctors if d["id"] == doctor_id), None)
        doctor_name = f"Dr. {matched['prenom']} {matched['nom']}" if matched else "un médecin"

        slot = slots[0]
        date_str = slot.datetime_start.strftime("%d/%m à %Hh%M")
        self._agent_says(
            f"Je vous propose un rendez-vous avec {doctor_name}, "
            f"le {date_str} à {slot.location}. Est-ce que cela vous convient ?"
        )

        response = self._get_patient_input()
        self.history.append(f"Agent: Proposition RDV {doctor_name} le {date_str}")
        self.history.append(f"Patient: {response}")

        appointment = book_slot(slot, patient.nom)
        self._agent_says(
            f"Votre rendez-vous est confirmé. "
            f"Numéro de confirmation : {appointment.confirmation_id}. "
            f"Vous recevrez un SMS de confirmation."
        )

        return {
            "doctor_id": doctor_id,
            "doctor_name": doctor_name,
            "slot": date_str,
            "confirmation_id": appointment.confirmation_id,
            "booked": True,
        }

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
            "timestamp_start": self.timestamp_start,
        }

        print("\n" + "=" * 55)
        print("  RÉCAP APPEL")
        print("=" * 55)
        print(f"  Durée       : {duration:.0f}s")
        print(f"  Orientation : {care.care_type.value}")
        print(f"  Urgence     : {urgency.score}/1.0 (confiance {urgency.confidence})")
        if appointment_info:
            print(f"  Médecin     : {appointment_info['doctor_name']}")
            print(f"  RDV         : {appointment_info['slot']}")
            print(f"  Confirmation: {appointment_info['confirmation_id']}")
        print("=" * 55)

        # Persistence + analytics post-appel
        conversation_text = "\n".join(self.history)
        run_post_call_analytics(result, conversation_text)

        return result

    def _agent_says(self, message: str):
        print(f"\n🏥 Agent: {message}")
        if self.vocal:
            from src.tools.voice import text_to_speech
            text_to_speech(message)

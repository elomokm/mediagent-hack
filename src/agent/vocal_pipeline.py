"""Pipeline vocal — conversation streaming OpenAI + décisions OpenHosta."""

import json
import os
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI

from src.agent.triage import evaluate_urgency, is_life_threatening
from src.agent.care_router import qualify_care_type
from src.agent.doctor_matcher import match_doctor
from src.models.schemas import CareType, PatientInput
from src.tools.scheduling import find_available_slots, find_alternative_doctor, book_slot
from src.tools.voice import text_to_speech, speech_to_text

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENHOSTA_DEFAULT_MODEL_API_KEY"))

SYSTEM_PROMPT = """Tu es l'assistant téléphonique de la clinique {clinic_name}, au {clinic_address}.

STYLE : Sois BREF. 1-2 phrases max par réponse. Chaleureux mais efficace. Pas de jargon médical. Ne fais JAMAIS de diagnostic. Ne mentionne le 15 (SAMU) que si les symptômes sont graves.

COLLECTE : Pose UNE question à la fois. Infos à collecter :
1. Nom
2. Âge
3. Symptômes
4. Depuis quand

Si le patient donne plusieurs infos d'un coup, ne les redemande pas. Dès que tu as nom + âge + symptômes + durée, réponds UNIQUEMENT avec ce JSON (rien d'autre) :
{{"COLLECTE_TERMINEE": true, "nom": "...", "age": ..., "sexe": "non précisé", "symptomes": ["..."], "duree_symptomes": "...", "antecedents": []}}"""

MAX_TURNS = 15


class VocalPipeline:
    """Pipeline vocal fluide — streaming OpenAI pour la conversation, OpenHosta pour les décisions."""

    def __init__(self, clinic_name: str, clinic_address: str, doctors: list[dict]):
        self.clinic_name = clinic_name
        self.clinic_address = clinic_address
        self.doctors = doctors
        self.messages = [
            {"role": "system", "content": SYSTEM_PROMPT.format(
                clinic_name=clinic_name, clinic_address=clinic_address
            )}
        ]
        self.timestamp_start: datetime | None = None
        self.timestamp_end: datetime | None = None

    def handle_call(self) -> dict:
        """Flux complet d'un appel vocal."""
        self.timestamp_start = datetime.now()

        print("\n🎙️  Appel en cours — parlez après le bip de l'agent\n")

        # Phase 1 : Conversation streaming (collecte infos)
        patient = self._conversation_loop()

        if not patient:
            print("\n[INFO] Pas assez d'informations collectées.")
            return {"status": "ABANDONNE"}

        # Phase 2 : Décisions OpenHosta (typées, fiables)
        print("\n[ANALYSE] Évaluation en cours...")
        urgency = evaluate_urgency(patient)
        print(f"[TRIAGE] Score: {urgency.score} | Confiance: {urgency.confidence}")
        print(f"[TRIAGE] Raison: {urgency.reasoning}")

        if is_life_threatening(urgency):
            msg = ("Vos symptômes nécessitent une prise en charge immédiate. "
                   "Je vous transfère vers le SAMU, le 15. Ne raccrochez pas.")
            self._say(msg)
            self.timestamp_end = datetime.now()
            return {
                "status": "TRANSFERE_SAMU",
                "patient": patient.model_dump(),
                "urgency": urgency.model_dump(),
                "duration_seconds": (self.timestamp_end - self.timestamp_start).total_seconds(),
            }

        care = qualify_care_type(patient, urgency)
        self._say(care.message_patient)

        # Phase 3 : Booking si nécessaire
        appointment_info = None
        if care.care_type in (CareType.GENERALISTE, CareType.TELECONSULTATION):
            appointment_info = self._book(patient, care)

        # Clôture
        self._say("Merci pour votre appel. N'hésitez pas à rappeler si besoin. Bonne journée.")
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

        return result

    def _conversation_loop(self) -> PatientInput | None:
        """Boucle conversationnelle en streaming — retourne PatientInput quand complet."""
        for turn in range(MAX_TURNS):
            # Générer la réponse agent en streaming
            agent_text = self._stream_response()

            # Vérifier si le LLM a renvoyé le JSON de fin de collecte
            if "COLLECTE_TERMINEE" in agent_text:
                return self._parse_patient_json(agent_text)

            # L'agent parle (TTS)
            self._say(agent_text)

            # Le patient répond (STT)
            patient_text = speech_to_text()
            if not patient_text:
                self._say("Je n'ai pas bien entendu, pourriez-vous répéter s'il vous plaît ?")
                patient_text = speech_to_text()
                if not patient_text:
                    continue

            print(f"  Patient: {patient_text}")
            self.messages.append({"role": "user", "content": patient_text})

        return None

    def _stream_response(self) -> str:
        """Appel streaming OpenAI — retourne la réponse complète."""
        stream = client.chat.completions.create(
            model=os.getenv("OPENHOSTA_DEFAULT_MODEL_NAME", "gpt-4o"),
            messages=self.messages,
            stream=True,
        )

        full_response = ""
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                full_response += delta

        self.messages.append({"role": "assistant", "content": full_response})
        return full_response

    def _parse_patient_json(self, text: str) -> PatientInput | None:
        """Parse le JSON de fin de collecte envoyé par le LLM."""
        try:
            # Extraire le JSON de la réponse
            start = text.index("{")
            end = text.rindex("}") + 1
            data = json.loads(text[start:end])

            return PatientInput(
                nom=data.get("nom", "Inconnu"),
                age=data.get("age", 0),
                sexe=data.get("sexe", "non précisé"),
                symptomes=data.get("symptomes", []),
                duree_symptomes=data.get("duree_symptomes", "non précisé"),
                antecedents=data.get("antecedents", []),
            )
        except (ValueError, json.JSONDecodeError, KeyError) as e:
            print(f"[WARN] Parsing JSON patient échoué: {e}")
            return None

    def _book(self, patient, care) -> dict | None:
        """Booking conversationnel — propose des créneaux et laisse le patient choisir."""
        doctor_id = match_doctor(patient, care, self.doctors)
        slots = find_available_slots(doctor_id, self.doctors)

        if not slots:
            alt_id = find_alternative_doctor(doctor_id, self.doctors)
            if alt_id:
                doctor_id = alt_id
                slots = find_available_slots(doctor_id, self.doctors)

        if not slots:
            self._say("Pas de créneau disponible pour le moment. Nous vous rappellerons.")
            return None

        matched = next((d for d in self.doctors if d["id"] == doctor_id), None)
        doctor_name = f"Dr. {matched['prenom']} {matched['nom']}" if matched else "un médecin"

        # Proposer 3 créneaux via le LLM streaming pour un choix naturel
        top_slots = slots[:3]
        slots_text = ", ".join(
            s.datetime_start.strftime("%d/%m à %Hh%M") for s in top_slots
        )

        # Ajouter le contexte booking à la conversation streaming
        self.messages.append({"role": "system", "content": (
            f"Le patient a besoin d'un RDV avec {doctor_name} à {top_slots[0].location}. "
            f"Créneaux disponibles : {slots_text}. "
            "Propose ces créneaux brièvement et demande lequel convient. "
            "Quand le patient choisit, réponds avec ce JSON uniquement : "
            f'{{"RDV_CONFIRME": true, "slot_index": 0}}'
            " (0 pour le 1er créneau, 1 pour le 2ème, 2 pour le 3ème)"
        )})

        # Boucle booking (max 3 échanges)
        chosen_slot = top_slots[0]  # fallback
        for _ in range(3):
            agent_text = self._stream_response()

            if "RDV_CONFIRME" in agent_text:
                try:
                    start = agent_text.index("{")
                    end = agent_text.rindex("}") + 1
                    data = json.loads(agent_text[start:end])
                    idx = data.get("slot_index", 0)
                    if 0 <= idx < len(top_slots):
                        chosen_slot = top_slots[idx]
                except (ValueError, json.JSONDecodeError):
                    pass
                break

            self._say(agent_text)
            response = speech_to_text()
            if response:
                print(f"  Patient: {response}")
                self.messages.append({"role": "user", "content": response})

        appointment = book_slot(chosen_slot, patient.nom)
        date_str = chosen_slot.datetime_start.strftime("%d/%m à %Hh%M")
        self._say(f"C'est noté, rendez-vous le {date_str} avec {doctor_name}. Confirmation numéro {appointment.confirmation_id}.")

        return {
            "doctor_id": doctor_id,
            "doctor_name": doctor_name,
            "slot": date_str,
            "confirmation_id": appointment.confirmation_id,
            "booked": True,
        }

    def _say(self, message: str):
        """L'agent parle — print + TTS."""
        print(f"\n🏥 Agent: {message}")
        text_to_speech(message)

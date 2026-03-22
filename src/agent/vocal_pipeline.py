"""Pipeline vocal — un agent conversationnel autonome gère tout l'appel.

Architecture :
- PENDANT l'appel : gpt-4o-mini en streaming gère la conversation de A à Z
- APRÈS l'appel : OpenHosta fait les analyses typées (triage score, analytics, lead)
"""

import json
import os
from datetime import datetime

from dotenv import load_dotenv
from openai import OpenAI

from src.models.schemas import PatientInput
from src.tools.scheduling import find_available_slots, find_alternative_doctor, book_slot
from src.tools.voice import text_to_speech, speech_to_text
from src.agent.post_call import run_post_call_analytics

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENHOSTA_DEFAULT_MODEL_API_KEY"))

# Modèle rapide pour la conversation (gpt-4o-mini = ~3x plus rapide que gpt-5)
CONV_MODEL = "gpt-4o-mini"

MAX_TURNS = 20


def _build_system_prompt(clinic_name: str, clinic_address: str, doctors: list[dict], slots_info: str) -> str:
    """Construit le system prompt avec tout le contexte dont l'agent a besoin."""

    doctors_text = "\n".join(
        f"  - Dr. {d['prenom']} {d['nom']} ({', '.join(d.get('specialites', []))}) — {d.get('lieu', '')}"
        for d in doctors
    )

    return f"""Tu es l'assistant téléphonique de la clinique {clinic_name}, au {clinic_address}. Tu gères un appel patient du début à la fin.

TON STYLE — tu parles comme un vrai standardiste humain :
- Tu es chaleureux et empathique. Tu reformules ce que le patient dit pour montrer que tu l'écoutes ("Je comprends que ça doit être gênant", "D'accord, je vois").
- Tu utilises le prénom du patient dès que tu le connais.
- Tes réponses font 2-3 phrases : une phrase d'empathie/transition + ta question.
- Tu parles en français naturel et courant, comme au téléphone. Pas de listes, pas de tirets, pas de formulations écrites.
- Tu ne fais JAMAIS de diagnostic médical.
- Tu ne mentionnes le SAMU (15) que si les symptômes sont graves (douleur thoracique, AVC, hémorragie, perte de conscience).

MÉDECINS DISPONIBLES :
{doctors_text}

CRÉNEAUX DISPONIBLES :
{slots_info}

TON TRAVAIL — dans cet ordre :

1. ACCUEIL : "Bonjour, clinique {clinic_name}, je vous écoute." Simple et naturel.
2. COLLECTE : récupère nom, âge, symptômes, depuis quand. UNE question à la fois. Si le patient donne plusieurs infos d'un coup, ne les redemande pas. Enchaîne naturellement.
3. ORIENTATION : selon les symptômes, oriente le patient :
   - Symptômes graves → dis d'appeler le 15 (SAMU) et termine IMMÉDIATEMENT
   - Besoin de consultation → propose un RDV avec le médecin adapté
   - Symptômes légers → conseille la pharmacie. Si le patient insiste pour un RDV, accepte sans discuter.
4. BOOKING (si RDV) : propose 2-3 créneaux de manière naturelle ("J'ai un créneau lundi à 9h, un autre mardi à 14h, lequel vous arrange ?"), laisse choisir, confirme.
5. CLÔTURE : remercie chaleureusement puis termine. Ton PROCHAIN message après l'au revoir DOIT être le JSON ci-dessous.

RÈGLE CRITIQUE — TERMINER L'APPEL :
Après avoir dit au revoir, ton message suivant est UNIQUEMENT ce JSON. Pas de question supplémentaire. L'appel est FINI.

{{"APPEL_TERMINE": true, "nom": "...", "age": 0, "sexe": "non précisé", "symptomes": ["..."], "duree_symptomes": "...", "antecedents": [], "orientation": "generaliste|urgences|pharmacie|teleconsultation", "rdv_pris": false, "doctor_name": null, "slot_choisi": null, "motif": "...", "transfert_samu": false}}"""


class VocalPipeline:
    """Agent conversationnel autonome — un seul modèle gère tout l'appel."""

    def __init__(self, clinic_name: str, clinic_address: str, doctors: list[dict]):
        self.clinic_name = clinic_name
        self.clinic_address = clinic_address
        self.doctors = doctors
        self.timestamp_start: datetime | None = None
        self.timestamp_end: datetime | None = None

        # Pré-calculer les créneaux disponibles pour chaque médecin
        slots_info = self._prepare_slots_info()

        self.messages = [
            {"role": "system", "content": _build_system_prompt(
                clinic_name, clinic_address, doctors, slots_info
            )}
        ]

    def _prepare_slots_info(self) -> str:
        """Prépare un résumé lisible des créneaux pour le system prompt."""
        lines = []
        for doc in self.doctors:
            slots = find_available_slots(doc["id"], self.doctors, days_ahead=3)
            if slots:
                top = slots[:4]
                slots_text = ", ".join(s.datetime_start.strftime("%d/%m %Hh%M") for s in top)
                lines.append(f"  Dr. {doc['prenom']} {doc['nom']} : {slots_text}")
        return "\n".join(lines) if lines else "  Aucun créneau disponible"

    def handle_call(self) -> dict:
        """Exécute l'appel — l'agent gère tout, on récupère le résultat à la fin."""
        self.timestamp_start = datetime.now()
        print("\n🎙️  Appel en cours\n")

        call_result = self._conversation_loop()
        self.timestamp_end = datetime.now()
        duration = (self.timestamp_end - self.timestamp_start).total_seconds()

        if not call_result:
            return {"status": "ABANDONNE", "duration_seconds": duration}

        # Booking réel si l'agent a proposé un RDV
        appointment_info = None
        if call_result.get("rdv_pris") and call_result.get("doctor_name"):
            appointment_info = self._finalize_booking(call_result)

        # Construire le patient pour les analyses post-appel
        patient = PatientInput(
            nom=call_result.get("nom", "Inconnu"),
            age=call_result.get("age", 0),
            sexe=call_result.get("sexe", "non précisé"),
            symptomes=call_result.get("symptomes", []),
            duree_symptomes=call_result.get("duree_symptomes", "non précisé"),
            antecedents=call_result.get("antecedents", []),
        )

        status = "TRANSFERE_SAMU" if call_result.get("transfert_samu") else "TERMINE"

        result = {
            "status": status,
            "patient": patient.model_dump(),
            "orientation": call_result.get("orientation", "inconnu"),
            "appointment": appointment_info,
            "duration_seconds": duration,
            "motif": call_result.get("motif", ""),
            "timestamp_start": self.timestamp_start,
        }

        # Récap terminal
        print("\n" + "=" * 55)
        print("  RÉCAP APPEL")
        print("=" * 55)
        print(f"  Durée       : {duration:.0f}s")
        print(f"  Patient     : {patient.nom}, {patient.age} ans")
        print(f"  Orientation : {call_result.get('orientation', '?')}")
        print(f"  Motif       : {call_result.get('motif', '?')}")
        if appointment_info:
            print(f"  Médecin     : {appointment_info['doctor_name']}")
            print(f"  RDV         : {appointment_info['slot']}")
            print(f"  Confirmation: {appointment_info['confirmation_id']}")
        if status == "TRANSFERE_SAMU":
            print("  ⚠️  TRANSFERT SAMU")
        print("=" * 55)

        # Persistence + analytics post-appel
        conversation_text = "\n".join(
            f"{m['role'].capitalize()}: {m['content']}"
            for m in self.messages if m["role"] in ("user", "assistant")
        )
        run_post_call_analytics(result, conversation_text)

        return result

    _GOODBYE_SIGNALS = ["bonne journée", "au revoir", "merci pour votre appel", "à bientôt", "prenez soin"]

    def _is_goodbye(self, text: str) -> bool:
        """Détecte si l'agent est en train de clôturer l'appel."""
        lower = text.lower()
        return any(signal in lower for signal in self._GOODBYE_SIGNALS)

    def _conversation_loop(self) -> dict | None:
        """L'agent gère la conversation — retourne le JSON de fin d'appel."""
        goodbye_said = False

        for _ in range(MAX_TURNS):
            agent_text = self._stream_response()

            # L'agent a terminé l'appel → JSON de résultat
            if "APPEL_TERMINE" in agent_text:
                return self._parse_result_json(agent_text)

            # L'agent parle
            self._say(agent_text)

            # Détection au revoir — forcer le JSON au prochain tour
            if self._is_goodbye(agent_text):
                if goodbye_said:
                    # Déjà dit au revoir une fois, on force la fin
                    self.messages.append({"role": "user", "content": "Au revoir."})
                    continue
                goodbye_said = True
                # Injecter un message pour forcer le JSON
                self.messages.append({"role": "user", "content": "Merci, au revoir !"})
                continue

            # Le patient répond
            patient_text = speech_to_text()
            if not patient_text:
                self._say("Pardon, je n'ai pas entendu. Pouvez-vous répéter ?")
                patient_text = speech_to_text()
                if not patient_text:
                    continue

            print(f"  Patient: {patient_text}")
            self.messages.append({"role": "user", "content": patient_text})

        return None

    def _stream_response(self) -> str:
        """Appel streaming — retourne la réponse complète."""
        stream = client.chat.completions.create(
            model=CONV_MODEL,
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

    def _parse_result_json(self, text: str) -> dict | None:
        """Parse le JSON de fin d'appel."""
        try:
            start = text.index("{")
            end = text.rindex("}") + 1
            return json.loads(text[start:end])
        except (ValueError, json.JSONDecodeError) as e:
            print(f"[WARN] Parsing JSON résultat échoué: {e}")
            return None

    def _finalize_booking(self, call_result: dict) -> dict | None:
        """Confirme le RDV dans le système de scheduling — respecte le choix du patient."""
        doctor_name = call_result.get("doctor_name", "")
        matched = next(
            (d for d in self.doctors if f"Dr. {d['prenom']} {d['nom']}" == doctor_name or d['nom'] in doctor_name),
            None
        )
        if not matched:
            return None

        slots = find_available_slots(matched["id"], self.doctors)
        if not slots:
            return None

        # Essayer de matcher le créneau choisi par le patient
        slot_choisi = call_result.get("slot_choisi", "")
        chosen_slot = None
        if slot_choisi:
            for s in slots:
                slot_str = s.datetime_start.strftime("%d/%m à %Hh%M")
                # Matching souple : comparer l'heure
                if slot_choisi in slot_str or slot_str in slot_choisi:
                    chosen_slot = s
                    break
                # Matcher aussi sur l'heure seule (ex: "10h30")
                hour_str = s.datetime_start.strftime("%Hh%M")
                if hour_str in slot_choisi or slot_choisi.replace(":", "h") in hour_str:
                    chosen_slot = s
                    break

        if not chosen_slot:
            chosen_slot = slots[0]  # fallback sur le premier

        appointment = book_slot(chosen_slot, call_result.get("nom", "Inconnu"))
        date_str = chosen_slot.datetime_start.strftime("%d/%m à %Hh%M")

        return {
            "doctor_id": matched["id"],
            "doctor_name": f"Dr. {matched['prenom']} {matched['nom']}",
            "slot": date_str,
            "confirmation_id": appointment.confirmation_id,
            "booked": True,
        }

    def _say(self, message: str):
        """L'agent parle — print + TTS."""
        print(f"\n🏥 Agent: {message}")
        text_to_speech(message)

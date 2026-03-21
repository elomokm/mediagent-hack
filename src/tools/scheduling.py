"""Gestion des créneaux et réservation — logique pure."""

import uuid
from datetime import datetime, timedelta

from src.models.schemas import TimeSlot, Appointment


def _generate_slots_for_doctor(doctor: dict, days_ahead: int = 3) -> list[TimeSlot]:
    """Génère des créneaux de 30min pour un médecin sur les prochains jours."""
    slots = []
    now = datetime.now()
    start_date = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)

    morning = [(9, 0), (9, 30), (10, 0), (10, 30), (11, 0), (11, 30)]
    afternoon = [(14, 0), (14, 30), (15, 0), (15, 30), (16, 0), (16, 30), (17, 0), (17, 30)]
    all_hours = morning + afternoon

    for day_offset in range(days_ahead):
        day = start_date + timedelta(days=day_offset)
        if day.weekday() >= 5:  # skip weekend
            continue
        for hour, minute in all_hours:
            slot_start = day.replace(hour=hour, minute=minute)
            slot_end = slot_start + timedelta(minutes=doctor.get("duree_consult", 30))
            slots.append(TimeSlot(
                datetime_start=slot_start,
                datetime_end=slot_end,
                doctor_name=f"Dr. {doctor.get('prenom', '')} {doctor.get('nom', '')}",
                location=doctor.get("lieu", ""),
            ))

    return slots


def find_available_slots(doctor_id: str, doctors: list[dict], days_ahead: int = 3) -> list[TimeSlot]:
    """Retourne les créneaux disponibles pour un médecin donné."""
    doctor = next((d for d in doctors if d["id"] == doctor_id), None)
    if not doctor:
        return []
    return _generate_slots_for_doctor(doctor, days_ahead)


def find_alternative_doctor(original_doctor_id: str, doctors: list[dict]) -> str | None:
    """Cherche un médecin avec la même spécialité qui a des créneaux."""
    original = next((d for d in doctors if d["id"] == original_doctor_id), None)
    if not original:
        return None

    original_specs = set(original.get("specialites", []))

    for doctor in doctors:
        if doctor["id"] == original_doctor_id:
            continue
        doctor_specs = set(doctor.get("specialites", []))
        if original_specs & doctor_specs:  # intersection non vide
            slots = find_available_slots(doctor["id"], doctors)
            if slots:
                return doctor["id"]

    return None


def book_slot(slot: TimeSlot, patient_name: str) -> Appointment:
    """Réserve un créneau et retourne un RDV confirmé."""
    return Appointment(
        slot=slot,
        patient_name=patient_name,
        confirmed=True,
        confirmation_id=str(uuid.uuid4())[:8],
    )

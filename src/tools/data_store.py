import sqlite3
import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "mediagent.db")

def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clinics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT,
            adresse TEXT,
            telephone TEXT,
            horaires TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS doctors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clinic_id INTEGER,
            nom TEXT,
            prenom TEXT,
            specialites TEXT, -- JSON blob
            lieu TEXT,
            duree_consult INTEGER,
            FOREIGN KEY (clinic_id) REFERENCES clinics(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id INTEGER,
            date DATE,
            slots TEXT, -- JSON blob
            FOREIGN KEY (doctor_id) REFERENCES doctors(id)
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clinic_id INTEGER,
            timestamp_start DATETIME,
            timestamp_end DATETIME,
            status TEXT,
            duration_sec INTEGER,
            care_type TEXT,
            urgency_score REAL,      -- queryable pour stats
            urgency_confidence REAL, -- queryable pour stats
            patient TEXT, -- JSON blob
            conversation TEXT, -- JSON blob
            urgency TEXT, -- JSON blob
            summary TEXT, -- JSON blob
            analysis TEXT, -- JSON blob
            lead TEXT, -- JSON blob
            FOREIGN KEY (clinic_id) REFERENCES clinics(id)
        )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_calls_status ON calls(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_calls_duration_sec ON calls(duration_sec)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_calls_care_type ON calls(care_type)')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            call_id INTEGER,
            doctor_id INTEGER,
            patient_name TEXT,
            slot_start DATETIME,
            slot_end DATETIME,
            confirmed BOOLEAN,
            confirmation_id TEXT,
            FOREIGN KEY (call_id) REFERENCES calls(id),
            FOREIGN KEY (doctor_id) REFERENCES doctors(id)
        )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_appointments_slot_start ON appointments(slot_start)')

    conn.commit()
    conn.close()
    print("Base de données initialisée avec succès ! Les tables sont prêtes.")

def save_call(call_result: dict) -> int:
    """Sauvegarde un appel complet en BDD. Retourne l'id de l'appel."""
    conn = get_connection()
    cursor = conn.cursor()

    # Extraire les champs queryables — compatible pipeline texte ET vocal
    urgency = call_result.get("urgency", {})
    if isinstance(urgency, str):
        urgency = {}

    care = call_result.get("care", {})
    if isinstance(care, str):
        care = {}

    # care_type : depuis care.care_type (texte) ou orientation (vocal)
    care_type = care.get("care_type", call_result.get("orientation", ""))

    # duration : arrondir
    duration = int(round(call_result.get("duration_seconds", 0)))

    # timestamp : formater proprement pour SQLite
    ts_start = call_result.get("timestamp_start")
    if isinstance(ts_start, datetime):
        ts_start = ts_start.strftime("%Y-%m-%d %H:%M:%S")
    else:
        ts_start = str(ts_start) if ts_start else ""

    appointment = call_result.get("appointment")

    cursor.execute('''
        INSERT INTO calls (
            timestamp_start, timestamp_end, status, duration_sec, care_type,
            urgency_score, urgency_confidence,
            patient, conversation, urgency, summary, analysis, lead
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        ts_start,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        call_result.get("status", "TERMINE"),
        duration,
        care_type,
        urgency.get("score", 0) if isinstance(urgency, dict) else 0,
        urgency.get("confidence", 0) if isinstance(urgency, dict) else 0,
        json.dumps(call_result.get("patient", {}), ensure_ascii=False, default=str),
        json.dumps(call_result.get("conversation", []), ensure_ascii=False, default=str),
        json.dumps(urgency, ensure_ascii=False, default=str),
        json.dumps(call_result.get("summary", {}), ensure_ascii=False, default=str),
        json.dumps(call_result.get("analysis", {}), ensure_ascii=False, default=str),
        json.dumps(call_result.get("lead", {}), ensure_ascii=False, default=str),
    ))

    call_id = cursor.lastrowid

    # Sauvegarder le RDV si présent
    if appointment and isinstance(appointment, dict) and appointment.get("booked"):
        patient_data = call_result.get("patient", {})
        patient_nom = patient_data.get("nom", "Inconnu") if isinstance(patient_data, dict) else "Inconnu"
        save_appointment(
            cursor, call_id,
            appointment.get("doctor_id", ""),
            patient_nom,
            appointment.get("slot", ""),
            appointment.get("confirmation_id", ""),
        )

    conn.commit()
    conn.close()
    print(f"[BDD] Appel #{call_id} sauvegardé.")
    return call_id


def save_appointment(cursor, call_id: int, doctor_id: str, patient_name: str,
                     slot: str, confirmation_id: str):
    """Insère un RDV dans la table appointments."""
    cursor.execute('''
        INSERT INTO appointments (call_id, doctor_id, patient_name, slot_start, confirmed, confirmation_id)
        VALUES (?, ?, ?, ?, 1, ?)
    ''', (call_id, doctor_id, patient_name, slot, confirmation_id))


def update_call_analytics(call_id: int, analysis: dict | None = None, lead: dict | None = None):
    """Met à jour les champs analytics d'un appel existant."""
    conn = get_connection()
    cursor = conn.cursor()

    if analysis:
        cursor.execute('UPDATE calls SET analysis = ? WHERE id = ?',
                        (json.dumps(analysis, ensure_ascii=False), call_id))
    if lead:
        cursor.execute('UPDATE calls SET lead = ? WHERE id = ?',
                        (json.dumps(lead, ensure_ascii=False), call_id))

    conn.commit()
    conn.close()


def get_calls_by_date(date: str) -> list[dict]:
    """Récupère tous les appels d'une date (format YYYY-MM-DD)."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM calls WHERE DATE(timestamp_start) = ?
    ''', (date,))

    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        r = dict(row)
        # Dé-sérialiser les JSON blobs
        for key in ["patient", "conversation", "urgency", "summary", "analysis", "lead"]:
            if r.get(key):
                try:
                    r[key] = json.loads(r[key])
                except (json.JSONDecodeError, TypeError):
                    pass
        results.append(r)

    return results


def get_all_calls() -> list[dict]:
    """Récupère tous les appels."""
    conn = get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM calls ORDER BY timestamp_start DESC')
    rows = cursor.fetchall()
    conn.close()

    results = []
    for row in rows:
        r = dict(row)
        for key in ["patient", "conversation", "urgency", "summary", "analysis", "lead"]:
            if r.get(key):
                try:
                    r[key] = json.loads(r[key])
                except (json.JSONDecodeError, TypeError):
                    pass
        results.append(r)

    return results


if __name__ == "__main__":
    init_db()

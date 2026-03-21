import sqlite3
import json
import os
from datetime import datetime

# Chemin vers le fichier de la base de données
# On sécurise le chemin pour qu'il trouve toujours le dossier "data" à la racine du projet
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, "data", "mediagent.db")

def get_connection():
    """Retourne une connexion à la base de données et s'assure que le dossier existe."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH)

def init_db():
    """Initialise la base de données et crée les tables au premier lancement."""
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Table clinics
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clinics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT,
            adresse TEXT,
            telephone TEXT,
            horaires TEXT
        )
    ''')

    # 2. Table doctors
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

    # 3. Table schedules
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS schedules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            doctor_id INTEGER,
            date DATE,
            slots TEXT, -- JSON blob
            FOREIGN KEY (doctor_id) REFERENCES doctors(id)
        )
    ''')

    # 4. Table calls
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS calls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            clinic_id INTEGER,
            timestamp_start DATETIME,
            timestamp_end DATETIME,
            status TEXT,
            duration_sec INTEGER,
            care_type TEXT,
            patient TEXT, -- JSON blob
            conversation TEXT, -- JSON blob
            urgency TEXT, -- JSON blob
            summary TEXT, -- JSON blob
            analysis TEXT, -- JSON blob
            lead TEXT, -- JSON blob
            FOREIGN KEY (clinic_id) REFERENCES clinics(id)
        )
    ''')
    
    # Création des index pour la table calls
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_calls_status ON calls(status)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_calls_duration_sec ON calls(duration_sec)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_calls_care_type ON calls(care_type)')

    # 5. Table appointments
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
    
    # Création de l'index pour la table appointments
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_appointments_slot_start ON appointments(slot_start)')

    conn.commit()
    conn.close()
    print("Base de données initialisée avec succès ! Les tables sont prêtes.")

def save_call(clinic_id, timestamp_start, timestamp_end, status, duration_sec, care_type, patient_dict, conversation_dict, urgency_dict, summary_dict, analysis_dict, lead_dict):
    """Sauvegarde la trace d'un appel terminé dans la base de données."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO calls (clinic_id, timestamp_start, timestamp_end, status, duration_sec, care_type, patient, conversation, urgency, summary, analysis, lead)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        clinic_id, timestamp_start, timestamp_end, status, duration_sec, care_type,
        json.dumps(patient_dict) if patient_dict else None,
        json.dumps(conversation_dict) if conversation_dict else None,
        json.dumps(urgency_dict) if urgency_dict else None,
        json.dumps(summary_dict) if summary_dict else None,
        json.dumps(analysis_dict) if analysis_dict else None,
        json.dumps(lead_dict) if lead_dict else None
    ))
    conn.commit()
    call_id = cursor.lastrowid
    conn.close()
    return call_id

def save_appointment(call_id, doctor_id, patient_name, slot_start, slot_end, confirmed=False, confirmation_id=None):
    """Enregistre un nouveau rendez-vous bloqué par le système."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO appointments (call_id, doctor_id, patient_name, slot_start, slot_end, confirmed, confirmation_id)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (call_id, doctor_id, patient_name, slot_start, slot_end, confirmed, confirmation_id))
    conn.commit()
    appointment_id = cursor.lastrowid
    conn.close()
    return appointment_id

def get_daily_stats():
    """Calcule toutes les statistiques agrégées (pour le terminal de fin de session)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Nombre d'appels total
    cursor.execute('SELECT COUNT(*) FROM calls')
    total_calls = cursor.fetchone()[0]
    
    # Nombre de transferts SAMU
    cursor.execute('SELECT COUNT(*) FROM calls WHERE care_type = "urgences"')
    samu_calls = cursor.fetchone()[0]
    
    # Nombre de RDV pris dans les bases
    cursor.execute('SELECT COUNT(*) FROM appointments')
    total_appointments = cursor.fetchone()[0]
    
    # Durée moyenne des appels
    cursor.execute('SELECT AVG(duration_sec) FROM calls')
    avg_duration = cursor.fetchone()[0]
    avg_duration = round(avg_duration) if avg_duration else 0
        
    conn.close()
    
    return {
        "total_calls": total_calls,
        "samu_calls": samu_calls,
        "total_appointments": total_appointments,
        "avg_duration": avg_duration
    }

if __name__ == "__main__":
    # Test : ce code s'exécute uniquement si on lance directement python data_store.py
    init_db()

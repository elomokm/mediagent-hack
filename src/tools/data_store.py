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

if __name__ == "__main__":
    init_db()

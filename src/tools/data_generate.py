import os
import sqlite3
import json
from dotenv import load_dotenv
from OpenHosta import emulate
from src.tools.data_store import get_connection, init_db

# Charger les variables d'environnement (comme OPENAI_API_KEY) depuis le fichier .env
load_dotenv()

def generate_data() -> dict:
    """
    Crée des fausses données médicales avec la structure stricte suivante (dictionnaire Python valide uniquement) :
    {
      "clinique": {
        "nom": "MediSanté",
        "adresse": "123 Rue de la Santé, Paris",
        "telephone": "0123456789",
        "horaires": "Lundi-Vendredi 8h-20h"
      },
      "medecins": [
        {
          "nom": "Dupont",
          "prenom": "Jean",
          "specialites": ["Généraliste"],
          "lieu": "Cabinet 1",
          "duree_consult": 30
        } 
      ], // (5 medecins au total : 2 généralistes, 1 cardiologue, 1 dermatologue, 1 pédiatre)
      "plannings": [
        {
          "doctor_index": 0, 
          "date": "2026-03-24",
          "slots": [{"start": "09:00", "end": "09:30", "status": "free"}, {"start": "09:30", "end": "10:00", "status": "booked"}]
        }
      ] // (Créneaux de 30min entre 9h-12h et 14h-18h, ~30% réservés. Faire cela sur 7 jours pour chaque index de médecin existant.)
    }
    """
    return emulate()

def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ ERREUR : La variable d'environnement OPENAI_API_KEY n'est pas définie dans le fichier .env")
        print("Veuillez rajouter votre clé API dans le fichier .env avant d'exécuter ce script.")
        return

    print("⏳ Génération des données en cours via OpenHosta... (Cela peut prendre environ 30 secondes à 1 minute)")
    data = generate_data()
    
    if not isinstance(data, dict):
        print("❌ ERREUR : Les données générées ne sont pas un dictionnaire Python valide.")
        print(data)
        return
        
    print("✅ Données générées avec succès ! Injection dans la base de données SQLite...")
    
    # 0. S'assurer que les tables existent
    init_db()
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # 1. Insertion de la clinique
    clinique = data.get("clinique", {})
    cursor.execute('''
        INSERT INTO clinics (nom, adresse, telephone, horaires)
        VALUES (?, ?, ?, ?)
    ''', (
        clinique.get("nom", "MediSanté"), 
        clinique.get("adresse", ""), 
        clinique.get("telephone", ""), 
        clinique.get("horaires", "")
    ))
    clinic_id = cursor.lastrowid
    
    # 2. Insertion des médecins
    medecins = data.get("medecins", [])
    doctor_ids = []
    for med in medecins:
        cursor.execute('''
            INSERT INTO doctors (clinic_id, nom, prenom, specialites, lieu, duree_consult)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            clinic_id, 
            med.get("nom", "Inconnu"), 
            med.get("prenom", ""), 
            json.dumps(med.get("specialites", [])),
            med.get("lieu", ""),
            med.get("duree_consult", 30)
        ))
        doctor_ids.append(cursor.lastrowid)

    # 3. Insertion des plannings
    plannings = data.get("plannings", [])
    for plan in plannings:
        doc_idx = plan.get("doctor_index", 0)
        # Assurer que l'index n'est pas "out of bound" si l'IA s'est trompée
        if doc_idx < len(doctor_ids):
            doc_id = doctor_ids[doc_idx]
        else:
            doc_id = doctor_ids[0] if doctor_ids else 1
            
        cursor.execute('''
            INSERT INTO schedules (doctor_id, date, slots)
            VALUES (?, ?, ?)
        ''', (
            doc_id,
            plan.get("date", "2026-03-24"),
            json.dumps(plan.get("slots", []))
        ))
        
    conn.commit()
    conn.close()
    
    print("🎉 Merveilleux ! Les données ont été insérées avec succès dans `data/mediagent.db` !")

if __name__ == "__main__":
    main()

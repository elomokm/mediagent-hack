"""Orientation du patient vers le type de soin adapté."""

from OpenHosta import emulate

from src.models.schemas import PatientInput, UrgencyScore, CareRecommendation


def qualify_care_type(patient: PatientInput, urgency: UrgencyScore) -> CareRecommendation:
    """Détermine le type de soin adapté pour le patient selon son urgence et ses symptômes.

    Règles d'orientation :
    - URGENCES : score d'urgence > 0.6, ou symptômes nécessitant une prise en charge
      hospitalière immédiate (fracture, plaie profonde, fièvre très élevée)
    - GENERALISTE : symptômes persistants ou chroniques nécessitant un examen physique
      (maux de tête récurrents, douleurs articulaires, fatigue prolongée)
    - TELECONSULTATION : suivi de routine, renouvellement d'ordonnance, question médicale
      simple ne nécessitant pas d'examen physique
    - PHARMACIE : symptômes bénins gérables avec des médicaments sans ordonnance
      (rhume léger, maux de gorge, petite allergie saisonnière)

    Le message_patient doit être en français, clair, rassurant et sans jargon médical.
    Ceci n'est PAS un diagnostic. En cas de doute, orienter vers le 15 (SAMU).
    """
    return emulate()

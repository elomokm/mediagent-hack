"""Gestion de la conversation téléphonique avec le patient."""

from OpenHosta import emulate

from src.models.schemas import PatientInput


def generate_greeting(clinic_name: str, clinic_address: str) -> str:
    """Génère un message d'accueil téléphonique pour la clinique.

    Tu es l'assistant téléphonique de la clinique {clinic_name}, située au {clinic_address}.
    Génère un accueil professionnel, chaleureux et court (2-3 phrases max).
    Présente-toi, nomme la clinique, et demande comment tu peux aider.
    Ton empathique et rassurant. Pas de jargon médical.
    """
    return emulate()


def extract_patient_info(conversation_text: str) -> PatientInput:
    """Extrait les informations structurées du patient à partir du texte de la conversation.

    Le texte contient des lignes au format :
    Agent: <message de l'agent>
    Patient: <réponse du patient>

    Extrais TOUTES les informations mentionnées par le patient :
    - nom : le nom complet du patient. Si le patient dit "Je suis Elom" ou "Elom OKOUMASSOUN", extrais ce nom.
    - age : l'âge en nombre entier. Si le patient dit "j'ai 35 ans", extrais 35.
    - sexe : "homme", "femme" ou "non précisé"
    - symptomes : liste de TOUS les symptômes médicaux décrits par le patient
    - duree_symptomes : depuis quand (ex: "2 semaines", "3 jours")
    - antecedents : antécédents médicaux mentionnés

    Valeurs par défaut si l'information n'est PAS dans la conversation :
    - nom: "Inconnu", age: 0, sexe: "non précisé", symptomes: [], duree_symptomes: "non précisé"
    """
    return emulate()


def generate_next_question(
    patient_partial: PatientInput,
    conversation_history: list[str],
) -> str:
    """Génère la prochaine question à poser au patient pour compléter les informations manquantes.

    Informations déjà collectées : {patient_partial}
    Historique de la conversation : {conversation_history}

    Priorité des questions :
    1. Nom du patient (si inconnu)
    2. Âge (si 0)
    3. Symptômes principaux (si liste vide)
    4. Depuis quand les symptômes sont présents (si non précisé)
    5. Antécédents médicaux

    Pose UNE SEULE question à la fois. Ton empathique, professionnel, sans jargon médical.
    Si toutes les infos essentielles sont collectées, demande si le patient a autre chose à ajouter.
    """
    return emulate()


def has_sufficient_info(patient: PatientInput) -> bool:
    """Vérifie que les informations minimales sont collectées pour le triage."""
    return (
        patient.nom != "Inconnu"
        and patient.age > 0
        and len(patient.symptomes) > 0
        and patient.duree_symptomes != "non précisé"
    )

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


def extract_patient_info(conversation_history: list[str]) -> PatientInput:
    """Extrait les informations structurées du patient à partir de la conversation.

    Analyse l'historique de conversation et remplis les champs du PatientInput :
    - nom : nom du patient (si mentionné)
    - age : âge du patient (si mentionné)
    - sexe : sexe du patient (si mentionné)
    - symptomes : liste des symptômes décrits
    - duree_symptomes : depuis quand les symptômes sont présents
    - antecedents : antécédents médicaux mentionnés

    Si une information n'est pas mentionnée, utilise une valeur par défaut raisonnable :
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

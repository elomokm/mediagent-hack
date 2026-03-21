"""Gestion de la conversation téléphonique avec le patient."""

from pydantic import BaseModel, Field

from OpenHosta import emulate

from src.models.schemas import PatientInput


class ConversationStep(BaseModel):
    """Résultat d'un tour de conversation — extraction + prochaine question en un seul appel."""

    patient_info: PatientInput = Field(description="Informations patient extraites de toute la conversation jusqu'ici")
    next_question: str = Field(description="Prochaine question à poser au patient")
    info_complete: bool = Field(description="True si on a nom, âge, symptômes et durée. False sinon.")


def generate_greeting(clinic_name: str, clinic_address: str) -> str:
    """Génère un message d'accueil téléphonique pour la clinique.

    Tu es l'assistant téléphonique de la clinique {clinic_name}, située au {clinic_address}.
    Génère un accueil professionnel, chaleureux et court (2-3 phrases max).
    Présente-toi, nomme la clinique, et demande comment tu peux aider.
    Ton empathique et rassurant. Pas de jargon médical.
    """
    return emulate()


def process_conversation_turn(conversation_text: str) -> ConversationStep:
    """Analyse la conversation et produit en UN SEUL appel : les infos patient extraites + la prochaine question.

    Le texte contient des lignes au format :
    Agent: <message de l'agent>
    Patient: <réponse du patient>

    ÉTAPE 1 — Extraction des infos patient :
    Parcourir TOUTE la conversation et extraire :
    - nom : nom complet du patient. Ex: "Je suis Elom" → nom = "Elom". "Elom OKOUMASSOUN" → nom = "Elom OKOUMASSOUN"
    - age : âge en nombre entier. Ex: "j'ai 35 ans" → age = 35
    - sexe : "homme", "femme" ou "non précisé"
    - symptomes : liste de TOUS les symptômes médicaux. Ex: "maux de tête et nausées" → ["maux de tête", "nausées"]
    - duree_symptomes : depuis quand. Ex: "depuis 2 semaines" → "2 semaines"
    - antecedents : liste des antécédents médicaux. TOUJOURS une liste. Ex: ["hypertension", "diabète"]. Si aucun antécédent → liste vide []

    Valeurs par défaut si NON mentionné : nom="Inconnu", age=0, sexe="non précisé", symptomes=[], duree_symptomes="non précisé", antecedents=[]
    IMPORTANT : antecedents doit TOUJOURS être une liste (jamais un string). Pas d'antécédent = []

    ÉTAPE 2 — Prochaine question :
    Poser UNE SEULE question pour obtenir la prochaine info manquante.
    Priorité : 1) nom 2) âge 3) symptômes 4) durée des symptômes 5) antécédents
    Si tout est collecté, demander si le patient a autre chose à ajouter.
    Ton empathique, professionnel, sans jargon médical.

    ÉTAPE 3 — info_complete :
    True si nom != "Inconnu" ET age > 0 ET symptomes non vide ET duree_symptomes != "non précisé"
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

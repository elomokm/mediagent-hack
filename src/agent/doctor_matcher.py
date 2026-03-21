"""Matching symptômes patient → médecin adapté dans le parc de la clinique."""

from OpenHosta import emulate

from src.models.schemas import PatientInput, CareRecommendation


def match_doctor(
    patient: PatientInput,
    care_recommendation: CareRecommendation,
    available_doctors: list[dict],
) -> str:
    """Choisit le médecin le plus adapté pour ce patient parmi les médecins disponibles.

    Critères de sélection :
    - Spécialité du médecin correspondant aux symptômes du patient
    - Type de soin recommandé (généraliste, téléconsultation, etc.)
    - En cas de doute ou d'absence de spécialiste, orienter vers le généraliste

    available_doctors est une liste de dictionnaires avec les champs :
    - id, nom, prenom, specialites, lieu

    Retourne l'id du médecin le plus adapté.
    Ceci n'est PAS un diagnostic. Le médecin fera sa propre évaluation.
    """
    return emulate()

"""Génération de résumé structuré d'un appel patient.

Basé sur le travail de Chedli (chedli/dev).
"""

from OpenHosta import emulate

from src.models.schemas import CallSummaryStructured


def generate_call_summary(text: str) -> CallSummaryStructured:
    """Analyse une conversation téléphonique et produit un résumé structuré.

    À partir du texte brut de la conversation entre l'agent et le patient,
    extraire :
    - Le nom du patient
    - Le motif principal de l'appel
    - Les symptômes médicaux mentionnés
    - Le score d'urgence estimé (0.0 à 1.0)
    - La confiance dans cette estimation (0.0 à 1.0)
    - L'orientation recommandée (urgences, generaliste, teleconsultation, pharmacie)
    - Si un RDV a été pris et avec quel médecin
    - Un résumé libre du problème, des actions et du ressenti

    Ceci n'est PAS un diagnostic médical.
    """
    return emulate()

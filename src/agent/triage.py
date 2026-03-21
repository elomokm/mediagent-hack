"""Évaluation de l'urgence médicale et décision de transfert SAMU."""

from OpenHosta import emulate

from src.models.schemas import PatientInput, UrgencyScore


URGENCY_LIFE_THREATENING_SCORE = 0.8
URGENCY_LIFE_THREATENING_CONFIDENCE = 0.9


def evaluate_urgency(patient: PatientInput) -> UrgencyScore:
    """Évalue le niveau d'urgence médicale d'un patient à partir de ses symptômes.

    Règles d'évaluation :
    - Score 0.9-1.0 : urgence vitale (douleur thoracique, AVC, détresse respiratoire,
      hémorragie, perte de conscience, réaction allergique sévère)
    - Score 0.6-0.8 : urgence relative (fièvre élevée persistante, douleur intense,
      traumatisme modéré)
    - Score 0.3-0.5 : consultation recommandée (symptômes persistants, gêne quotidienne)
    - Score 0.0-0.2 : faible urgence (symptômes légers, conseil pharmacie suffisant)

    La confiance doit refléter la certitude de l'évaluation.
    Si les symptômes sont ambigus ou insuffisants, la confiance doit être basse.

    Ceci n'est PAS un diagnostic médical. En cas de doute, orienter vers le 15 (SAMU).
    """
    return emulate()


def is_life_threatening(urgency: UrgencyScore) -> bool:
    """Détermine si l'urgence nécessite un transfert immédiat vers le SAMU (15)."""
    return (
        urgency.score >= URGENCY_LIFE_THREATENING_SCORE
        and urgency.confidence >= URGENCY_LIFE_THREATENING_CONFIDENCE
    )

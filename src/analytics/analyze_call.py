from OpenHosta import emulate
from pydantic import BaseModel, Field

from models.schemas import CallAnalysis, CallSentiment


# --- Internal Classes for Granular Inference ---
class _AnalyticalInsights(BaseModel):
    """Internal schema for supplementary analytical insights."""

    themes_principaux: list[str] = Field(
        description="Sujets majeurs abordés pendant la conversation."
    )
    qualite_interaction: float = Field(
        ge=0.0, le=1.0, description="Score de qualité de l'échange (0.0 à 1.0)."
    )
    notes_amelioration: list[str] = Field(
        default_factory=list, description="Suggestions d'amélioration."
    )


# --- Inference Layer (Specialized AI Functions) ---


def _extract_call_sentiment(text: str) -> CallSentiment:
    """
    Extrait le sentiment global de l'appel.

    CONSIGNES STRICTES :
    - Retourner uniquement l'une des valeurs : 'positif', 'neutre', 'negatif', 'anxieux'.
    """
    return emulate()


def _extract_analytical_insights(text: str) -> _AnalyticalInsights:
    """
    Analyse les thèmes, la qualité et les pistes d'amélioration.

    Exemple de sortie :
    {
        "themes_principaux": ["prise de rdv", "douleur"],
        "qualite_interaction": 0.9,
        "notes_amelioration": ["parler plus lentement"]
    }
    """
    return emulate()


# --- Orchestration Layer (Public Functions) ---


def analyze_call(text: str, call_id: str, duree: float) -> CallAnalysis:
    """
    Effectue une analyse complète de l'appel en combinant sentiment et insights techniques.
    """
    # 1. Extractions spécialisées
    sentiment = _extract_call_sentiment(text)
    insights = _extract_analytical_insights(text)

    # 2. Assemblage final de l'objet CallAnalysis
    return CallAnalysis(
        call_id=call_id,
        duree_secondes=duree,
        sentiment_global=sentiment,
        **insights.model_dump(),
    )

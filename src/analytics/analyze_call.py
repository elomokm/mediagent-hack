from OpenHosta import emulate

from models.schemas import CallAnalysis, CallAnalysisGenerated


def extract_ai_analysis(text: str) -> CallAnalysisGenerated:
    """Analyse le texte et renvoie un dictionnaire d'insights.
    Exemple de format attendu :
    {
        "sentiment_global": "positif",
        "themes_principaux": ["sujet 1", "sujet 2"],
        "qualite_interaction": 0.9,
        "notes_amelioration": ["note 1"]
    }"""
    return emulate()


def analyze_call(text: str, call_id: str, duree: float) -> CallAnalysis:
    # 1. On laisse l'IA générer uniquement l'inférence
    ai_result = extract_ai_analysis(text)
    # 2. On reconstruit l'objet complet avec nos valeurs sûres et pré-remplies
    return CallAnalysis(
        call_id=call_id,
        duree_secondes=duree,
        **ai_result.model_dump(),  # On injecte tout ce que l'IA a trouvé
    )

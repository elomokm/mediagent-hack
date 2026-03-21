"""Analyses post-appel — OpenHosta pour les décisions typées après la conversation."""

from src.models.schemas import PatientInput
from src.agent.triage import evaluate_urgency
from src.analytics.analyze_call import analyze_call
from src.analytics.lead_qualifier import qualify_lead
from src.tools.data_store import save_call, update_call_analytics


def run_post_call_analytics(call_result: dict, conversation_text: str) -> dict:
    """Lance toutes les analyses post-appel et persiste en BDD.

    1. Sauvegarde l'appel en BDD
    2. Score de triage OpenHosta (si pas déjà fait)
    3. Analyse de l'appel (sentiment, thèmes, qualité)
    4. Qualification lead (nouveau patient, potentiel suivi)
    5. Met à jour l'appel en BDD avec les résultats analytics

    Retourne les résultats enrichis.
    """
    print("\n[POST-APPEL] Sauvegarde en BDD...")
    call_id = save_call(call_result)

    # Construire le PatientInput pour le triage
    patient_data = call_result.get("patient", {})
    patient = PatientInput(
        nom=patient_data.get("nom", "Inconnu"),
        age=patient_data.get("age", 0),
        sexe=patient_data.get("sexe", "non précisé"),
        symptomes=patient_data.get("symptomes", []),
        duree_symptomes=patient_data.get("duree_symptomes", "non précisé"),
        antecedents=patient_data.get("antecedents", []),
    )

    # Triage typé OpenHosta (si pas déjà dans le résultat)
    urgency_data = call_result.get("urgency")
    if not urgency_data or not urgency_data.get("score"):
        print("[POST-APPEL] Triage OpenHosta...")
        urgency = evaluate_urgency(patient)
        urgency_data = urgency.model_dump()

    # Analyse de l'appel
    print("[POST-APPEL] Analyse de l'appel...")
    duration = call_result.get("duration_seconds", 0)
    try:
        analysis = analyze_call(conversation_text, call_id=str(call_id), duree=duration)
        analysis_data = analysis.model_dump()
        print(f"[POST-APPEL] Sentiment: {analysis.sentiment_global} | Qualité: {analysis.qualite_interaction}")
    except Exception as e:
        print(f"[POST-APPEL] Analyse échouée: {e}")
        analysis_data = None

    # Qualification lead
    print("[POST-APPEL] Qualification lead...")
    try:
        lead = qualify_lead(conversation_text, call_id=str(call_id), patient_nom=patient.nom)
        lead_data = lead.model_dump()
        print(f"[POST-APPEL] Nouveau patient: {lead.est_nouveau_patient} | Suivi: {lead.potentiel_suivi}")
    except Exception as e:
        print(f"[POST-APPEL] Qualification lead échouée: {e}")
        lead_data = None

    # Mettre à jour en BDD
    update_call_analytics(call_id, analysis=analysis_data, lead=lead_data)
    print(f"[POST-APPEL] Analytics sauvegardées pour appel #{call_id}")

    return {
        "call_id": call_id,
        "urgency": urgency_data,
        "analysis": analysis_data,
        "lead": lead_data,
    }

"""Point d'entrée MediAgent — lance le pipeline de pré-tri médical."""

import sys
from datetime import datetime

from src.config import MOCK_CLINIC_NAME, MOCK_CLINIC_ADDRESS, MOCK_DOCTORS
from src.agent.pipeline import MediAgentPipeline
from src.analytics.stats import compute_daily_stats, format_stats_terminal
from src.tools.data_store import init_db


# --- 3 scénarios de démo ---

DEMO_SCENARIOS = [
    {
        "name": "URGENCE VITALE — Transfert SAMU",
        "responses": [
            "Je m'appelle Marie Lefèvre, j'ai 65 ans",
            "J'ai une douleur très forte dans la poitrine depuis 30 minutes, j'arrive plus à respirer, c'est de pire en pire",
            "J'ai de l'hypertension et du diabète",
        ],
    },
    {
        "name": "RDV GÉNÉRALISTE — Booking complet",
        "responses": [
            "Bonjour, je suis Jean Dupont, j'ai 35 ans",
            "J'ai des petits maux de tête de temps en temps et je me sens fatigué, depuis environ 5 jours",
            "Oui, ce créneau me convient parfaitement",
        ],
    },
    {
        "name": "CONSEIL PHARMACIE — Orientation sans RDV",
        "responses": [
            "Je suis Sophie Martin, 28 ans",
            "J'ai le nez qui coule un peu et la gorge légèrement irritée depuis hier soir, rien de méchant",
            "Non rien du tout",
        ],
    },
]


def run_interactive(vocal: bool = False):
    """Mode interactif — conversation texte ou vocale avec le patient."""
    mode = "vocal (micro + haut-parleur)" if vocal else "conversation interactive"
    print("=" * 55)
    print(f"  MediAgent — {MOCK_CLINIC_NAME}")
    print(f"  {MOCK_CLINIC_ADDRESS}")
    print("=" * 55)
    print(f"  Mode : {mode}")
    if not vocal:
        print("  Tapez vos réponses comme si vous étiez le patient.")
    else:
        print("  Parlez dans le micro quand vous voyez [Parlez...]")
    print("  Ctrl+C pour quitter.\n")

    pipeline = MediAgentPipeline(
        clinic_name=MOCK_CLINIC_NAME,
        clinic_address=MOCK_CLINIC_ADDRESS,
        doctors=MOCK_DOCTORS,
        vocal=vocal,
    )

    try:
        result = pipeline.handle_call()
    except KeyboardInterrupt:
        print("\n\nAppel interrompu.")
        return

    print(f"\n[STATUS] Appel terminé — statut : {result['status']}")


def run_demo():
    """Mode démo — 3 scénarios automatiques + stats à la fin."""
    print("=" * 55)
    print(f"  MediAgent — DÉMO AUTOMATIQUE")
    print(f"  {MOCK_CLINIC_NAME} — {MOCK_CLINIC_ADDRESS}")
    print("=" * 55)
    print(f"  {len(DEMO_SCENARIOS)} scénarios vont défiler automatiquement.\n")

    all_results = []

    for i, scenario in enumerate(DEMO_SCENARIOS, 1):
        print("\n" + "#" * 55)
        print(f"  SCÉNARIO {i}/{len(DEMO_SCENARIOS)} : {scenario['name']}")
        print("#" * 55)

        pipeline = MediAgentPipeline(
            clinic_name=MOCK_CLINIC_NAME,
            clinic_address=MOCK_CLINIC_ADDRESS,
            doctors=MOCK_DOCTORS,
            patient_responses=scenario["responses"],
        )

        try:
            result = pipeline.handle_call()
            all_results.append(result)
        except Exception as e:
            print(f"\n[ERREUR] Scénario {i} échoué : {e}")
            continue

    # Stats agrégées
    if all_results:
        today = datetime.now().strftime("%Y-%m-%d")
        stats = compute_daily_stats(all_results, today)
        print(format_stats_terminal(stats))


def run_vocal():
    """Mode vocal — conversation streaming OpenAI + décisions OpenHosta."""
    from src.agent.vocal_pipeline import VocalPipeline

    print("=" * 55)
    print(f"  MediAgent — {MOCK_CLINIC_NAME}")
    print(f"  {MOCK_CLINIC_ADDRESS}")
    print("=" * 55)
    print("  Mode : vocal (micro + haut-parleur)")
    print("  Parlez dans le micro quand vous voyez [Parlez...]")
    print("  Ctrl+C pour quitter.\n")

    pipeline = VocalPipeline(
        clinic_name=MOCK_CLINIC_NAME,
        clinic_address=MOCK_CLINIC_ADDRESS,
        doctors=MOCK_DOCTORS,
    )

    try:
        result = pipeline.handle_call()
    except KeyboardInterrupt:
        print("\n\nAppel interrompu.")
        return

    print(f"\n[STATUS] Appel terminé — statut : {result['status']}")


def run_stats():
    """Affiche les KPIs du jour depuis la BDD."""
    from src.analytics.stats import get_daily_kpis, format_stats_terminal

    date = None
    for i, arg in enumerate(sys.argv):
        if arg == "--stats" and i + 1 < len(sys.argv) and not sys.argv[i + 1].startswith("--"):
            date = sys.argv[i + 1]

    stats = get_daily_kpis(date)
    print(format_stats_terminal(stats))

    # Détail par appel
    from src.tools.data_store import get_calls_by_date
    calls = get_calls_by_date(date or datetime.now().strftime("%Y-%m-%d"))
    if calls:
        print(f"\n  Détail des {len(calls)} appels :")
        for c in calls:
            patient = c.get("patient", {})
            nom = patient.get("nom", "?") if isinstance(patient, dict) else "?"
            print(f"    #{c['id']} | {nom} | {c.get('care_type', '?')} | {c.get('duration_sec', 0)}s | {c.get('status', '?')}")


def main():
    init_db()

    if "--demo" in sys.argv:
        run_demo()
    elif "--vocal" in sys.argv:
        run_vocal()
    elif "--stats" in sys.argv:
        run_stats()
    else:
        run_interactive()


if __name__ == "__main__":
    main()

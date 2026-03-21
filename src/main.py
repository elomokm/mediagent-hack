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
            "Je m'appelle Marie Lefèvre",
            "J'ai 65 ans",
            "J'ai une douleur très forte dans la poitrine, j'arrive plus à respirer, ça fait très mal",
            "Ça a commencé il y a 30 minutes, c'est de pire en pire",
            "J'ai de l'hypertension et du diabète",
        ],
    },
    {
        "name": "RDV GÉNÉRALISTE — Booking complet",
        "responses": [
            "Bonjour, je suis Jean Dupont",
            "J'ai 35 ans",
            "J'ai des maux de tête très forts depuis 2 semaines, et parfois des vertiges",
            "Depuis 2 semaines exactement",
            "Non, pas d'antécédents particuliers",
            "Oui, c'est parfait",
        ],
    },
    {
        "name": "CONSEIL PHARMACIE — Orientation sans RDV",
        "responses": [
            "Je suis Sophie Martin",
            "28 ans",
            "J'ai un petit rhume, le nez qui coule et un peu mal à la gorge",
            "Depuis 2 jours",
            "Non rien de particulier",
        ],
    },
]


def run_interactive():
    """Mode interactif — conversation texte avec le patient."""
    print("=" * 55)
    print(f"  MediAgent — {MOCK_CLINIC_NAME}")
    print(f"  {MOCK_CLINIC_ADDRESS}")
    print("=" * 55)
    print("  Mode : conversation interactive")
    print("  Tapez vos réponses comme si vous étiez le patient.")
    print("  Ctrl+C pour quitter.\n")

    pipeline = MediAgentPipeline(
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


def main():
    init_db()

    if "--demo" in sys.argv:
        run_demo()
    else:
        run_interactive()


if __name__ == "__main__":
    main()

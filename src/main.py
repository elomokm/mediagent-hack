"""Point d'entrée MediAgent — lance le pipeline de pré-tri médical."""

import sys

from src.config import MOCK_CLINIC_NAME, MOCK_CLINIC_ADDRESS, MOCK_DOCTORS
from src.agent.pipeline import MediAgentPipeline
from src.tools.data_store import init_db


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


def main():
    init_db()

    if "--demo" in sys.argv:
        print("Mode démo pas encore implémenté. Lancement en mode interactif.\n")

    run_interactive()


if __name__ == "__main__":
    main()

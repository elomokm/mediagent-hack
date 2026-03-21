import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from agent.summary import generate_clinical_summary


def test_generate_clinical_summary():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    file_path = os.path.join(
        base_dir, "mockup_data", "analytics", "fake_conversation.txt"
    )

    # 1. Ouvrir et lire le fichier
    with open(file_path, "r", encoding="utf-8") as f:
        conversation_text = f.read()

    # 2. Passer ce texte à la fonction
    clinical_summary = generate_clinical_summary(conversation_text)

    # 3. Afficher le résultat pour vérifier
    print("\n" + "=" * 50)
    print("👨‍⚕️ RÉSUMÉ CLINIQUE GÉNÉRÉ")
    print("=" * 50)
    print(clinical_summary.model_dump_json(indent=2))
    print("=" * 50 + "\n")


if __name__ == "__main__":
    test_generate_clinical_summary()

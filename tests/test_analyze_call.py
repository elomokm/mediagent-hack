import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from analytics.analyze_call import analyze_call


def test_analyze_call():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    file_path = os.path.join(
        base_dir, "mockup_data", "analytics", "fake_conversation.txt"
    )

    # 1. Ouvrir et lire le fichier
    with open(file_path, "r", encoding="utf-8") as f:
        conversation_text = f.read()

    # 2. Passer ce texte à votre fonction avec les nouveaux paramètres
    summary = analyze_call(conversation_text, call_id="TEST-1234", duree=324.5)

    # 3. Afficher le résultat proprement (en JSON indenté)
    print("\n" + "=" * 50)
    print("🔬 ANALYSE DÉTAILLÉE DE L'APPEL")
    print("=" * 50)
    print(summary.model_dump_json(indent=2))
    print("=" * 50 + "\n")


if __name__ == "__main__":
    test_analyze_call()

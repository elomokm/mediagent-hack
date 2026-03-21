import os
import sys

# Ajout du dossier "src" au chemin pour permettre l'import du module "analytics"
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from analytics.analyze_call import analyze_call

# def analyze_call(text: str, call_id: str, duree: float) -> CallAnalysis:
def test_analyze_call():
    # -----------------
    # Exemple d'utilisation
    # -----------------

    # (Astuce: trouver le chemin depuis la racine du projet)
    base_dir = os.path.dirname(os.path.dirname(__file__))
    file_path = os.path.join(
        base_dir, "mockup_data", "analytics", "fake_conversation.txt"
    )

    # 1. Ouvrir et lire le fichier
    with open(file_path, "r", encoding="utf-8") as f:
        conversation_text = f.read()

    # 2. Passer ce texte à votre fonction avec les nouveaux paramètres
    summary = analyze_call(conversation_text, call_id="TEST-1234", duree=324.5)

    # 3. Afficher le résultat pour vérifier
    print("Analyse de l'appel terminée :")
    print(summary)


if __name__ == "__main__":
    test_analyze_call()

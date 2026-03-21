import os

from analytics.generate_call_summary import generate_call_summary


def test_generate_call_summary():

    # -----------------
    # Exemple d'utilisation
    # -----------------

    # (Astuce: trouver le chemin depuis la racine du projet, quelle que soit la méthode de lancement)
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    file_path = os.path.join(
        base_dir, "mockup_data", "analytics", "fake_conversation.txt"
    )

    # 1. Ouvrir et lire le fichier
    with open(file_path, "r", encoding="utf-8") as f:
        conversation_text = f.read()

    # 2. Passer ce texte à votre fonction
    summary = generate_call_summary(conversation_text)

    # 3. Afficher le résultat pour vérifier
    print("Analyse de l'appel terminée :")
    print(summary)

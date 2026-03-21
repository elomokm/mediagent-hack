"""Test de generate_call_summary — basé sur le travail de Chedli."""

import os

from src.analytics.call_summarizer import generate_call_summary


def test_generate_call_summary():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    file_path = os.path.join(base_dir, "data", "mock", "fake_conversation.txt")

    with open(file_path, "r", encoding="utf-8") as f:
        conversation_text = f.read()

    summary = generate_call_summary(conversation_text)

    print("Analyse de l'appel terminée :")
    print(summary)

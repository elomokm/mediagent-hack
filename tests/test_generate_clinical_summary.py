"""Test generate_clinical_summary."""

import os

from src.agent.summary import generate_clinical_summary


def test_generate_clinical_summary():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    file_path = os.path.join(base_dir, "data", "mock", "fake_conversation.txt")

    with open(file_path, "r", encoding="utf-8") as f:
        conversation_text = f.read()

    clinical_summary = generate_clinical_summary(conversation_text)

    print("\n" + "=" * 50)
    print("RÉSUMÉ CLINIQUE GÉNÉRÉ")
    print("=" * 50)
    print(clinical_summary.model_dump_json(indent=2))
    print("=" * 50 + "\n")


if __name__ == "__main__":
    test_generate_clinical_summary()

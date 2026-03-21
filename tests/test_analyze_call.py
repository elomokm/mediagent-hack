"""Test analyze_call."""

import os

from src.analytics.analyze_call import analyze_call


def test_analyze_call():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    file_path = os.path.join(base_dir, "data", "mock", "fake_conversation.txt")

    with open(file_path, "r", encoding="utf-8") as f:
        conversation_text = f.read()

    summary = analyze_call(conversation_text, call_id="TEST-1234", duree=324.5)

    print("\n" + "=" * 50)
    print("ANALYSE DÉTAILLÉE DE L'APPEL")
    print("=" * 50)
    print(summary.model_dump_json(indent=2))
    print("=" * 50 + "\n")


if __name__ == "__main__":
    test_analyze_call()

"""Module vocal — TTS (OpenAI) + STT (Whisper)."""

import io
import os
import tempfile

import numpy as np
import sounddevice as sd
import soundfile as sf
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENHOSTA_DEFAULT_MODEL_API_KEY"))

SAMPLE_RATE = 16000
SILENCE_THRESHOLD = 0.02
SILENCE_DURATION = 1.5  # secondes de silence avant de couper


def text_to_speech(text: str, voice: str = "nova"):
    """Convertit du texte en parole et le joue via le haut-parleur.

    Voix disponibles : alloy, echo, fable, onyx, nova, shimmer
    'nova' — féminine, naturelle, professionnelle
    """
    response = client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text,
    )

    # Lire l'audio depuis les bytes
    audio_bytes = io.BytesIO(response.content)
    data, samplerate = sf.read(audio_bytes)
    sd.play(data, samplerate)
    sd.wait()


def speech_to_text() -> str:
    """Enregistre depuis le micro jusqu'au silence, puis transcrit via Whisper.

    Détecte automatiquement la fin de parole (1.5s de silence).
    """
    print("  [🎙️ Parlez...]")

    frames = []
    silence_frames = 0
    max_silence = int(SILENCE_DURATION * SAMPLE_RATE / 1024)
    recording = True
    started = False

    def callback(indata, frame_count, time_info, status):
        nonlocal silence_frames, started, recording
        volume = np.abs(indata).mean()

        if volume > SILENCE_THRESHOLD:
            started = True
            silence_frames = 0
        elif started:
            silence_frames += 1

        if started and silence_frames > max_silence:
            recording = False
            raise sd.CallbackStop()

        if started:
            frames.append(indata.copy())

    with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, blocksize=1024,
                        dtype="float32", callback=callback):
        while recording:
            sd.sleep(100)

    if not frames:
        return ""

    audio_data = np.concatenate(frames)

    # Sauvegarder en fichier temp WAV pour Whisper
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        sf.write(tmp.name, audio_data, SAMPLE_RATE)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="fr",
            )
        return transcript.text
    finally:
        os.unlink(tmp_path)

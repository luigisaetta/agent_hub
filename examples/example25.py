"""
Author: L. Saetta
Last modified: 2026-04-13
License: MIT

Description:
    Example script that classifies the mood of a WAV audio file
    using Responses API and google.gemini-2.5-pro.
"""

import base64
from pathlib import Path

from common import get_inference_client, print_example_summary, print_runtime_config

MODEL_ID = "google.gemini-2.5-pro"
TEMPERATURE = 0.0
INPUT_WAV_DIR = "input_wav"
MOOD_LABELS = [
    "calm",
    "happy",
    "energetic",
    "sad",
    "angry",
    "suspenseful",
    "romantic",
    "neutral",
]


def encode_wav(audio_path: Path) -> str:
    """Read a WAV file and return base64-encoded content."""
    with open(audio_path, "rb") as audio_file:
        return base64.b64encode(audio_file.read()).decode("utf-8")


def find_first_wav_file(root_dir: Path) -> Path | None:
    """Return the first WAV file from <root>/input_wav, if available."""
    input_dir = root_dir / INPUT_WAV_DIR
    wav_files = sorted(input_dir.glob("*.wav"))
    if not wav_files:
        return None
    return wav_files[0]


def extract_label(raw_output: str) -> str:
    """Extract a valid mood label from model output."""
    cleaned_output = raw_output.strip().lower()
    if cleaned_output in MOOD_LABELS:
        return cleaned_output

    for label in MOOD_LABELS:
        if label in cleaned_output:
            return label

    return "unknown"


def build_prompt() -> str:
    """Build the mood classification prompt in English."""
    labels = ", ".join(MOOD_LABELS)
    return (
        "You are given a WAV audio clip. "
        f"Classify its overall emotional mood using exactly one label from this list: {labels}. "
        "Return only the label in lowercase, with no punctuation and no extra words."
    )


def main() -> None:
    """Classify audio mood from a WAV file in input_wav/."""
    print_runtime_config()
    print("")
    print_example_summary("Classify WAV audio mood with Gemini 2.5 Pro.")
    print("")
    print(f"Model: {MODEL_ID}")
    print("")

    root_dir = Path(__file__).resolve().parents[1]
    audio_path = find_first_wav_file(root_dir)

    if audio_path is None:
        print(f"No .wav files found in '{INPUT_WAV_DIR}/'.")
        print(
            "Add at least one WAV file under repository root "
            f"'{INPUT_WAV_DIR}/' and run again."
        )
        return

    base64_audio = encode_wav(audio_path)
    prompt = build_prompt()

    client = get_inference_client()
    response = client.responses.create(
        model=MODEL_ID,
        temperature=TEMPERATURE,
        input=[
            {
                # Gemini does not allow system role in this context.
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {
                        "type": "input_audio",
                        "audio": base64_audio,
                        "format": "wav",
                    },
                ],
            }
        ],
    )

    predicted_mood = extract_label(response.output_text or "")

    print(f"Audio file: {audio_path.name}")
    print(f"Allowed labels: {MOOD_LABELS}")
    print(f"Predicted mood: {predicted_mood}")
    print(f"Raw output: {response.output_text}")
    print("")


if __name__ == "__main__":
    main()

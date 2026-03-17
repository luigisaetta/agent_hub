"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    Example script that sends a simple prompt to an OCI-hosted OpenAI-compatible endpoint
    and prints the response.
     This example shows how to use the text_format parameter to parse the response
     into a structured format
"""

from pathlib import Path
import sys

from pydantic import BaseModel

from openai import OpenAI

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from config import BASE_URL
from config_private import KEY1, PROJECT_ID

MODEL_ID = "openai.gpt-5.2"
TEMPERATURE = 0.0


class CalendarEvent(BaseModel):
    """
    This class defines the structure of a calendar event, with fields for the event name,
    date, and participants.
    """

    name: str
    date: str
    participants: list[str]


def main() -> None:
    """Parse unstructured text into a typed calendar event object."""
    client = OpenAI(
        base_url=BASE_URL,
        api_key=KEY1,
        project=PROJECT_ID,
    )

    response = client.responses.parse(
        model="openai.gpt-4.1",
        input=[
            {"role": "system", "content": "Extract the event information."},
            {
                "role": "user",
                "content": "Alice and Bob are going to a science fair on Friday.",
            },
        ],
        store=False,
        text_format=CalendarEvent,
    )

    event = response.output_parsed
    print(event)


if __name__ == "__main__":
    main()

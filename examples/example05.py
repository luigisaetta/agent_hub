"""
Author: L. Saetta
Last modified: 2026-03-16
License: MIT

Description:
    Example script that shows how to save the conversation platform side.
    This one use conversation API. Using conversation API we can use streaming.
"""

from openai import OpenAI
from common import print_streamed_output

from config import BASE_URL
from config_private import KEY1, PROJECT_ID

MODEL_ID = "openai.gpt-5.2"
TEMPERATURE = 0.0


def main() -> None:
    """Create a conversation and stream two context-linked turns."""
    client = OpenAI(
        base_url=BASE_URL,
        api_key=KEY1,
        project=PROJECT_ID,
    )

    # 1. create a conversation
    conversation = client.conversations.create(metadata={"topic": "demo"})
    print("Conversation ID: ", conversation.id)
    print("")

    request = "Tell me something about Giorgio Parisi?"

    # 2. first request
    response1 = client.responses.create(
        model=MODEL_ID,
        temperature=TEMPERATURE,
        input=request,
        # link to the conversation
        conversation=conversation.id,
        stream=True,
    )
    print("Request:", request)
    print_streamed_output(response1)
    print("")

    # 3. second turn, chaining to the first turn
    request = "Tell me something about his work on Spin glasses."
    response2 = client.responses.create(
        model=MODEL_ID,
        temperature=TEMPERATURE,
        input=request,
        conversation=conversation.id,
        stream=True,
    )
    print("\nRequest:", request)
    print_streamed_output(response2)
    print("")


if __name__ == "__main__":
    main()

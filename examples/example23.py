"""
Author: L. Saetta
Last modified: 2026-03-28
License: MIT

Description:
    Example script that demonstrates custom function tool calling with the
    Responses API, including iterative tool execution until a final answer.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Callable

from common import (
    get_inference_client,
    get_sampling_kwargs,
    print_example_summary,
    print_runtime_config,
)
from config import MODEL_ID

TEMPERATURE = 0.0
MAX_TOOL_ROUNDS = 5


def get_weather(city: str, unit: str = "celsius") -> dict[str, Any]:
    """Return simulated weather data for a city."""
    weather_data = {
        "rome": {"temperature_c": 18, "condition": "sunny"},
        "milan": {"temperature_c": 15, "condition": "cloudy"},
        "new york": {"temperature_c": 11, "condition": "rain"},
        "london": {"temperature_c": 9, "condition": "windy"},
    }

    key = city.strip().lower()
    item = weather_data.get(key, {"temperature_c": 20, "condition": "unknown"})
    temperature_c = item["temperature_c"]

    if unit == "fahrenheit":
        temperature = round((temperature_c * 9 / 5) + 32, 1)
        temp_key = "temperature_f"
    else:
        temperature = temperature_c
        temp_key = "temperature_c"

    return {
        "city": city,
        temp_key: temperature,
        "condition": item["condition"],
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "source": "simulated_weather_service",
    }


TOOL_FUNCTIONS: dict[str, Callable[..., dict[str, Any]]] = {
    "get_weather": get_weather,
}

TOOLS = [
    {
        "type": "function",
        "name": "get_weather",
        "description": "Get current weather conditions for a city.",
        "parameters": {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name, for example Rome or New York.",
                },
                "unit": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "Temperature unit.",
                },
            },
            "required": ["city"],
            "additionalProperties": False,
        },
    }
]


def _extract_function_calls(response: Any) -> list[Any]:
    """Return function-call items from a Responses API response object."""
    output_items = getattr(response, "output", None) or []
    return [
        item for item in output_items if getattr(item, "type", "") == "function_call"
    ]


def _execute_function_call(call_item: Any) -> dict[str, Any]:
    """Execute a single function call emitted by the model."""
    function_name = getattr(call_item, "name", "")

    if function_name not in TOOL_FUNCTIONS:
        return {
            "ok": False,
            "error": f"Unknown function: {function_name}",
        }

    raw_arguments = getattr(call_item, "arguments", "") or "{}"

    try:
        arguments = json.loads(raw_arguments)
    except json.JSONDecodeError as exc:
        return {
            "ok": False,
            "error": f"Invalid JSON arguments: {exc}",
            "raw_arguments": raw_arguments,
        }

    try:
        result = TOOL_FUNCTIONS[function_name](**arguments)
    except TypeError as exc:
        return {
            "ok": False,
            "error": f"Invalid tool arguments: {exc}",
            "arguments": arguments,
        }

    return {
        "ok": True,
        "result": result,
    }


def main() -> None:
    """Run a complete tool-calling loop with Responses API."""
    print_runtime_config()
    print("")
    print_example_summary("Custom function tool calling with iterative loop.")
    print("")

    client = get_inference_client()

    request = (
        "Compare today's weather in Rome and New York in celsius, "
        "then suggest what to wear in each city."
    )

    response = client.responses.create(
        model=MODEL_ID,
        **get_sampling_kwargs(MODEL_ID, temperature=TEMPERATURE),
        input=request,
        tools=TOOLS,
    )

    round_index = 1
    while round_index <= MAX_TOOL_ROUNDS:
        function_calls = _extract_function_calls(response)
        if not function_calls:
            break

        print(
            f"Tool round {round_index}: model requested {len(function_calls)} call(s)."
        )

        tool_outputs = []
        for call_item in function_calls:
            function_name = getattr(call_item, "name", "")
            call_id = getattr(call_item, "call_id", "")
            execution_result = _execute_function_call(call_item)

            print(f"- Executed {function_name} (call_id={call_id})")

            tool_outputs.append(
                {
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": json.dumps(execution_result),
                }
            )

        response = client.responses.create(
            model=MODEL_ID,
            **get_sampling_kwargs(MODEL_ID, temperature=TEMPERATURE),
            previous_response_id=response.id,
            input=tool_outputs,
            tools=TOOLS,
        )
        round_index += 1

    if round_index > MAX_TOOL_ROUNDS:
        print("Reached MAX_TOOL_ROUNDS before completion.")

    print("")
    print("Request:", request)
    print("")
    print("Final answer:")
    print(response.output_text)
    print("")


if __name__ == "__main__":
    main()

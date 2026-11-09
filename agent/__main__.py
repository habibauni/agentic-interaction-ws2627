import os
import sys
import json
import uuid
import re
from pathlib import Path
from datetime import datetime, timezone, date

import requests
from dotenv import load_dotenv
from openai import OpenAI

# Load configuration

load_dotenv(override=False)

api_key = os.getenv("OPENAI_API_KEY")
base_url = os.getenv("OPENAI_BASE_URL")
model = os.getenv("MODEL")
data_base_url = os.getenv("DATA_BASE_URL")

if not all([api_key, base_url, model, data_base_url]):
    raise ValueError("Missing configuration. Please check your .env file.")

client = OpenAI(
    api_key=api_key,
    base_url=base_url
)

# Create a logging function

run_id = str(uuid.uuid4())
Path("logs").mkdir(exist_ok=True)
log_file = Path("logs") / f"run_{run_id}.jsonl"

def write_log(event, tool=None, args=None, ok=None, duration_ms=None):

    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "run_id": run_id,
        "event": event,
        "tool": tool,
        "args": args,
        "ok": ok,
        "model": model,
        "duration_ms": duration_ms
    }

    with open(log_file, "a", encoding="utf-8") as file:
        file.write(json.dumps(entry, ensure_ascii=False) + "\n")

# Create the calendar tool

def get_calendar(date_string):

    # Check the date format and validity
    try:
        datetime.strptime(date_string, "%Y-%m-%d")
    except ValueError:
        return {
            "error": "Invalid date. Use YYYY-MM-DD."
        }

    # Build the URL
    url = f"{data_base_url.rstrip('/')}/calendar/{date_string}.json"

    try:
        response = requests.get(url, timeout=15)

        # No calendar data for this day
        if response.status_code == 404:
            return {
                "found": False,
                "message": f"No calendar data available for {date_string}."
            }

        response.raise_for_status()

        return {
            "found": True,
            "date": date_string,
            "appointments": response.json()
        }

    except requests.RequestException as error:
        return {
            "error": f"Could not retrieve calendar data: {error}"
        }

    except ValueError:
        return {
            "error": "The calendar endpoint returned invalid JSON."
        }

# Define the tool for the AI model

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_calendar",
            "description": (
                "Retrieve all calendar appointments for one specific day. "
                "Use this tool whenever the user asks about calendar "
                "appointments on a date."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format."
                    }
                },
                "required": ["date"],
                "additionalProperties": False
            }
        }
    }
]

# Run the AI agent


def main():

    if len(sys.argv) < 2:
        print('Usage: python -m agent "Your question"')
        return 1

    user_task = " ".join(sys.argv[1:])

    write_log(
        event="user_task",
        args={"task": user_task},
        ok=True
    )

    system_prompt = """
    You are a helpful calendar assistant.

    The user asks questions about calendar appointments.

    You MUST use the get_calendar tool to retrieve calendar
    information before answering questions about appointments.

    Never invent calendar appointments.

    If no calendar data is available, explain this to the user.
    Answer in the same language as the user.
    """

    try:
        # First model call: The model decides to use the tool
        start = datetime.now(timezone.utc)

        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_task}
            ],
            tools=tools,
            tool_choice="required"
        )

        model_duration = (
            datetime.now(timezone.utc) - start
        ).total_seconds() * 1000

        message = response.choices[0].message

        if not message.tool_calls:
            raise RuntimeError("The model did not call the calendar tool.")

        # Add the model's tool call to the conversation
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_task},
            message
        ]

        # Execute the requested tool
        for tool_call in message.tool_calls:

            if tool_call.function.name != "get_calendar":
                raise RuntimeError("Unknown tool requested.")

            arguments = json.loads(tool_call.function.arguments)

            write_log(
                event="tool_call",
                tool="get_calendar",
                args=arguments,
                ok=True,
                duration_ms=model_duration
            )

            tool_start = datetime.now(timezone.utc)

            result = get_calendar(arguments["date"])

            tool_duration = (
                datetime.now(timezone.utc) - tool_start
            ).total_seconds() * 1000

            write_log(
                event="tool_result",
                tool="get_calendar",
                args=result,
                ok="error" not in result,
                duration_ms=tool_duration
            )

            # Send the tool result back to the model
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(
                    result,
                    ensure_ascii=False
                )
            })

        # Second model call: Generate the final answer
        start = datetime.now(timezone.utc)

        final_response = client.chat.completions.create(
            model=model,
            messages=messages
        )

        final_duration = (
            datetime.now(timezone.utc) - start
        ).total_seconds() * 1000

        answer = final_response.choices[0].message.content

        write_log(
            event="final",
            args={"answer": answer},
            ok=True,
            duration_ms=final_duration
        )

        print(answer)
        return 0

    except Exception as error:

        write_log(
            event="error",
            args={"error": str(error)},
            ok=False
        )

        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

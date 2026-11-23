
import json
from typing import Literal

from openai import OpenAI, APIStatusError
from pydantic import BaseModel, ConfigDict, Field

from config import config


client = OpenAI(
    api_key=config.api_key,
    base_url=config.base_url,
    timeout=60,
    max_retries=2
)


class Action(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal[
        "move",
        "click",
        "type",
        "press",
        "scroll",
        "wait",
        "done",
        "ask_user"
    ]

    reasoning: str = Field(max_length=1000)
    x: int | None = Field(default=None, ge=0)
    y: int | None = Field(default=None, ge=0)
    text: str | None = Field(default=None, max_length=5000)
    key: str | None = Field(default=None, max_length=50)
    button: Literal["left", "right", "middle"] = "left"
    amount: int | None = Field(default=None, ge=-10, le=10)
    seconds: float | None = Field(default=None, ge=0, le=10)


SYSTEM_PROMPT = """
You are the reasoning engine of Absolut, an autonomous desktop agent.

Your objective is to complete the user's task by interacting with their desktop.

You receive:
- The user's objective.
- A screenshot of the current desktop.
- OCR results.
- Screen dimensions.
- Previous actions.
- Relevant experiences from previous tasks.

Return exactly one JSON object describing the next action.

Available actions:

move:
Move the mouse to x and y.

click:
Click at x and y. Button can be left, right or middle.

type:
Type the supplied text.

press:
Press a key or shortcut such as CTRL+L or ENTER.

scroll:
Scroll using amount. Positive means up, negative means down.

wait:
Wait for the specified number of seconds.

ask_user:
Ask the user for clarification or confirmation.

done:
Indicate that the task is completed.

Rules:

1. Never invent coordinates.
2. Coordinates must refer to the supplied screenshot's actual displayed dimensions.
3. Perform one action at a time.
4. Observe the desktop after every action.
5. Never assume an action succeeded without checking.
6. Learn from previous successful and failed experiences.
7. Do not blindly repeat previously failed strategies.
8. Prefer reliable, reversible actions.
9. Never execute terminal commands or arbitrary code.
10. Never access passwords, API keys or other secrets.
11. Never purchase, send messages, delete files or change security settings without user confirmation.
12. If the task is ambiguous, ask the user.
13. Do not claim completion without visual verification.
14. Use the available OCR results to locate interface elements.
15. Use the screenshot to understand the context, not just the OCR text.

Return JSON only.
"""


def plan(task, observation, history, experiences):
    context = {
        "objective": task,
        "screen": {
            "width": observation["width"],
            "height": observation["height"],
            "image_width": observation["image_width"],
            "image_height": observation["image_height"],
            "platform": observation["platform"]
        },
        "ocr": observation["ocr"],
        "previous_actions": history[-10:],
        "relevant_experiences": experiences
    }

    content = [
        {
            "type": "text",
            "text": json.dumps(context, ensure_ascii=False)
        },
        {
            "type": "image_url",
            "image_url": {
                "url": (
                    "data:image/jpeg;base64,"
                    + observation["image"]
                ),
                "detail": "high"
            }
        }
    ]

    try:
        response = client.chat.completions.create(
            model=config.model,
            messages=[
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                {
                    "role": "user",
                    "content": content
                }
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=500
        )

    except APIStatusError as error:
        body = error.response.text[:2000]

        raise RuntimeError(
            f"AI API returned HTTP {error.status_code}: {body}"
        ) from error

    message = response.choices[0].message.content

    if not message:
        raise RuntimeError("The AI returned an empty response")

    return Action.model_validate_json(message)

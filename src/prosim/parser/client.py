"""Claude API client for structured workflow extraction via tool_use."""

from __future__ import annotations

import os

import anthropic

from prosim.parser.prompts import SYSTEM_PROMPT, WORKFLOW_TOOL


def generate_workflow_raw(
    domain_description: str,
    model: str | None = None,
) -> dict:
    """Call Claude API to generate a structured workflow from a domain description.

    Uses tool_use to extract structured JSON output. Returns the raw tool
    input dict from Claude's response.

    Requires ANTHROPIC_API_KEY environment variable.
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "ANTHROPIC_API_KEY environment variable is required. "
            "Set it in your environment or .env file."
        )

    model = model or os.environ.get("PROSIM_MODEL", "claude-sonnet-4-5-20250929")

    client = anthropic.Anthropic(api_key=api_key)

    message = client.messages.create(
        model=model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        tools=[WORKFLOW_TOOL],
        tool_choice={"type": "tool", "name": "generate_workflow"},
        messages=[
            {
                "role": "user",
                "content": f"Generate a detailed workflow model for the following process:\n\n{domain_description}",
            }
        ],
    )

    # Extract tool use result
    for block in message.content:
        if block.type == "tool_use" and block.name == "generate_workflow":
            return block.input

    raise RuntimeError("Claude did not return a tool_use response for workflow generation")

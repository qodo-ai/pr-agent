"""
Provider-agnostic push outputs relay for Slack

This FastAPI service receives generic PR-Agent push outputs (from [push_outputs]) and relays them
as Slack Incoming Webhook messages.

Usage
-----
1) Run the relay (choose one):
   - uvicorn pr_agent.servers.push_outputs_relay:app --host 0.0.0.0 --port 8000
   - python -m pr_agent.servers.push_outputs_relay

2) Configure the destination Slack webhook:
   - Set environment variable SLACK_WEBHOOK_URL to your Slack Incoming Webhook URL.

3) Point PR-Agent to the relay:
   In your configuration (e.g., .pr_agent.toml or central config), enable generic push outputs:

   [push_outputs]
   enable = true
   channels = ["webhook"]
   webhook_url = "http://localhost:8000/relay"  # adjust host/port if needed
   presentation = "markdown"

Security
--------
- Keep the relay private or place it behind an auth gateway if exposed externally.
- You can also wrap this service with a reverse proxy that enforces authentication and rate limits.

Notes
-----
- The relay is intentionally Slack-specific while living outside the provider-agnostic core.
- If record['markdown'] is present, it will be used as Slack message text. Otherwise, a JSON fallback
  is generated from record['payload'].
- Slack supports basic Markdown (mrkdwn). Complex HTML/GitGFM sections may not render perfectly.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict

import requests
from fastapi import FastAPI, HTTPException

app = FastAPI(title="PR-Agent Push Outputs Relay (Slack)")


def _to_slack_text(record: Dict[str, Any]) -> str:
    """
    Prefer full review markdown; otherwise fallback to a compact JSON of the payload.
    """
    markdown = record.get("markdown")
    if isinstance(markdown, str) and markdown.strip():
        return markdown

    payload = record.get("payload") or {}
    try:
        return "```\n" + json.dumps(payload, ensure_ascii=False, indent=2) + "\n```"
    except Exception:
        return str(payload)


@app.post("/relay")
async def relay(record: Dict[str, Any]):
    slack_url = os.environ.get("SLACK_WEBHOOK_URL", "").strip()
    if not slack_url:
        raise HTTPException(status_code=500, detail="SLACK_WEBHOOK_URL environment variable is not set")

    text = _to_slack_text(record)

    # If using a Slack Workflow "triggers" URL, the workflow expects top-level fields
    # that match the configured variables in the Workflow (e.g., "markdown", "payload").
    # Otherwise, for Incoming Webhooks ("services" URL), use the standard {text, mrkdwn}.
    if "hooks.slack.com/triggers/" in slack_url:
        body = {
            # Map our computed text to the workflow variable named "markdown"
            "markdown": text,
            # Provide original payload if the workflow defines a variable for it
            "payload": record.get("payload", {}),
        }
    else:
        body = {
            "text": text,
            "mrkdwn": True,
        }

    try:
        resp = requests.post(slack_url, json=body, timeout=8)
        if resp.status_code >= 300:
            raise HTTPException(status_code=resp.status_code, detail=f"Slack webhook error: {resp.text}")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to post to Slack: {e}")

    return {"status": "ok"}


if __name__ == "__main__":
    # Allow running directly: python -m pr_agent.servers.push_outputs_relay
    import uvicorn

    port = int(os.environ.get("PORT", "8000"))
    uvicorn.run("pr_agent.servers.push_outputs_relay:app", host="0.0.0.0", port=port, reload=False)

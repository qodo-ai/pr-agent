#!/bin/bash
export PYTHONUNBUFFERED=1

if [ -n "$GITEA_EVENT_NAME" ] || [ "$GITEA_ACTIONS" == "true" ]; then
    python /app/pr_agent/servers/gitea_action_runner.py
else
    python /app/pr_agent/servers/github_action_runner.py
fi


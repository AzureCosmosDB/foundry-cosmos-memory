#!/bin/sh
set -eu

printf '\n=== [postprovision] Setting up Python environment ===\n'
python3 -m venv .venv
# shellcheck disable=SC1091
. .venv/bin/activate
python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt --pre

printf '\n=== [postprovision] Creating Foundry PromptAgent ===\n'
AGENT_OUT="$(python -m src.create_agent)"
printf '%s\n' "$AGENT_OUT"
AGENT_NAME="$(printf '%s\n' "$AGENT_OUT" | sed -n 's/^FOUNDRY_AGENT_NAME=//p' | tail -1)"
AGENT_VERSION="$(printf '%s\n' "$AGENT_OUT" | sed -n 's/^FOUNDRY_AGENT_VERSION=//p' | tail -1)"

if [ -z "$AGENT_NAME" ] || [ -z "$AGENT_VERSION" ]; then
  echo "Foundry agent creation did not return a name and version." >&2
  exit 1
fi

azd env set FOUNDRY_AGENT_NAME "$AGENT_NAME" >/dev/null
azd env set FOUNDRY_AGENT_VERSION "$AGENT_VERSION" >/dev/null
export FOUNDRY_AGENT_NAME="$AGENT_NAME"
export FOUNDRY_AGENT_VERSION="$AGENT_VERSION"

printf '\n=== [postprovision] Proving cross-conversation Cosmos memory ===\n'
python -m src.run_memory_test

printf '\nDeployment and memory test succeeded. See README.md to start the browser chat.\n'

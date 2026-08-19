"""Shared configuration loaded from environment (populated by azd or .env)."""

from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


def require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise SystemExit(
            f"ERROR: environment variable {name} is required.\n"
            "Run `azd up` first, then export the azd environment to .env, or copy "
            ".env.example to .env and fill in values for existing resources."
        )
    return value


COSMOS_ENDPOINT = require("COSMOS_ENDPOINT")
COSMOS_DATABASE = os.getenv("COSMOS_DATABASE", "ai_memory")

FOUNDRY_ENDPOINT = require("FOUNDRY_ENDPOINT")
FOUNDRY_PROJECT_ENDPOINT = os.getenv("FOUNDRY_PROJECT_ENDPOINT", FOUNDRY_ENDPOINT)
CHAT_MODEL = os.getenv("CHAT_MODEL", "gpt-4o-mini")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-large")
FOUNDRY_AGENT_NAME = os.getenv("FOUNDRY_AGENT_NAME", "cosmos-memory-sample-agent")

AGENT_INSTRUCTIONS = (
    "You are a helpful assistant with long-term memory about the user. "
    "When you remember facts about the user, use them naturally to personalize "
    "your answers. If you don't remember something, say so instead of guessing."
)

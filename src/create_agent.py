"""Create a new version of the configured PromptAgent in Foundry Agent Service."""

from __future__ import annotations

import asyncio

from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition
from azure.identity.aio import DefaultAzureCredential

from . import config


async def create_agent_version() -> tuple[str, str]:
    credential = DefaultAzureCredential()
    async with credential, AIProjectClient(
        endpoint=config.FOUNDRY_PROJECT_ENDPOINT,
        credential=credential,
    ) as client:
        created = await client.agents.create_version(
            agent_name=config.FOUNDRY_AGENT_NAME,
            definition=PromptAgentDefinition(
                model=config.CHAT_MODEL,
                instructions=config.AGENT_INSTRUCTIONS,
            ),
        )
        version = str(created.version)
        print(f"Created agent '{config.FOUNDRY_AGENT_NAME}' (version {version}).")
        return config.FOUNDRY_AGENT_NAME, version


async def main() -> None:
    name, version = await create_agent_version()
    print(f"FOUNDRY_AGENT_NAME={name}")
    print(f"FOUNDRY_AGENT_VERSION={version}")


if __name__ == "__main__":
    asyncio.run(main())

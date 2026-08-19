"""Create or reuse the configured PromptAgent in Foundry Agent Service."""

from __future__ import annotations

import asyncio

from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import PromptAgentDefinition
from azure.core.exceptions import ResourceNotFoundError
from azure.identity.aio import DefaultAzureCredential

from . import config


async def create_or_get_agent() -> tuple[str, str]:
    credential = DefaultAzureCredential()
    async with credential, AIProjectClient(
        endpoint=config.FOUNDRY_PROJECT_ENDPOINT,
        credential=credential,
    ) as client:
        try:
            await client.agents.get(config.FOUNDRY_AGENT_NAME)
            async for existing in client.agents.list_versions(
                config.FOUNDRY_AGENT_NAME,
                limit=1,
            ):
                version = str(existing.version)
                print(f"Reusing existing agent '{config.FOUNDRY_AGENT_NAME}' (version {version}).")
                return config.FOUNDRY_AGENT_NAME, version
        except ResourceNotFoundError:
            pass

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
    name, version = await create_or_get_agent()
    print(f"FOUNDRY_AGENT_NAME={name}")
    print(f"FOUNDRY_AGENT_VERSION={version}")


if __name__ == "__main__":
    asyncio.run(main())

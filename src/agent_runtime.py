"""Shared Foundry Agent Service and Cosmos memory runtime."""

from __future__ import annotations

import os
from contextlib import AsyncExitStack
from dataclasses import dataclass, field

from agent_framework.foundry import FoundryAgent
from agent_framework_azure_cosmos_memory import CosmosMemoryContextProvider
from azure.identity.aio import DefaultAzureCredential

from . import config


@dataclass
class AgentRuntime:
    agent: FoundryAgent
    memory: CosmosMemoryContextProvider
    credential: DefaultAzureCredential
    _stack: AsyncExitStack = field(default_factory=AsyncExitStack, init=False)

    async def __aenter__(self) -> "AgentRuntime":
        await self._stack.enter_async_context(self.credential)
        await self._stack.enter_async_context(self.agent)
        await self._stack.enter_async_context(self.memory)
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self._stack.__aexit__(exc_type, exc_value, traceback)

    def create_session(self, user_id: str):
        session = self.agent.create_session()
        session.state.setdefault(self.memory.source_id, {})["user_id"] = user_id
        return session


def create_runtime(*, extract_every_turn: bool = False) -> AgentRuntime:
    credential = DefaultAzureCredential()
    provider_options = {}
    if extract_every_turn:
        provider_options["processor_config"] = {"FACT_EXTRACTION_EVERY_N": 1}

    memory = CosmosMemoryContextProvider(
        cosmos_endpoint=config.COSMOS_ENDPOINT,
        cosmos_database=config.COSMOS_DATABASE,
        foundry_endpoint=config.FOUNDRY_PROJECT_ENDPOINT,
        embedding_model=config.EMBEDDING_MODEL,
        chat_model=config.CHAT_MODEL,
        credential=credential,
        memory_types=["fact", "procedural", "episodic"],
        **provider_options,
    )
    agent = FoundryAgent(
        project_endpoint=config.FOUNDRY_PROJECT_ENDPOINT,
        agent_name=config.FOUNDRY_AGENT_NAME,
        agent_version=os.getenv("FOUNDRY_AGENT_VERSION"),
        credential=credential,
        context_providers=[memory],
    )
    return AgentRuntime(agent=agent, memory=memory, credential=credential)

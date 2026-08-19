"""Prove Cosmos-backed recall in a new Foundry Agent Service conversation."""

from __future__ import annotations

import asyncio
from uuid import uuid4

from .agent_runtime import create_runtime


async def main() -> None:
    runtime = create_runtime(extract_every_turn=True)
    user_id = f"memory-test-{uuid4()}"

    async with runtime:
        print("\n[Conversation 1] Teaching the agent a durable fact...")
        session = runtime.create_session(user_id)
        first = await runtime.agent.run(
            "I love hiking and I'm allergic to peanuts.",
            session=session,
        )
        print("Assistant:", first.text)

        print("\n[Flush] Waiting for background memory extraction to persist...")
        await runtime.memory.flush()

        print("\n[Conversation 2] New conversation, same user. Asking it to recall...")
        session = runtime.create_session(user_id)
        second = await runtime.agent.run(
            "What should we pack for a trail lunch? Anything I can't eat?",
            session=session,
        )
        print("Assistant:", second.text)

    recalled = "peanut" in (second.text or "").lower()
    print("\n" + "=" * 60)
    print("RESULT")
    print("=" * 60)
    print(f"  Recalled peanut allergy in a NEW conversation: {recalled}")
    if recalled:
        print("  PASS - Cosmos memory was injected into the Foundry agent run.")
    else:
        print("  INCONCLUSIVE - reply did not mention peanuts. See README troubleshooting.")
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())

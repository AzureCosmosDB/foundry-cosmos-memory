"""Interactive browser chat for the Cosmos-backed Foundry agent.

Run:
    python -m chainlit run src/chat.py
"""

from __future__ import annotations

import re

import chainlit as cl

from src.agent_runtime import AgentRuntime, create_runtime

RUNTIME_KEY = "agent_runtime"
SESSION_KEY = "agent_session"
USER_ID_KEY = "memory_user_id"
USER_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


def navigation_actions() -> list[cl.Action]:
    return [
        cl.Action(
            name="new_conversation",
            payload={},
            label="New conversation",
            icon="message-square-plus",
            tooltip="Start a new conversation while keeping this user's memory",
        ),
        cl.Action(
            name="switch_user",
            payload={},
            label="Switch user",
            icon="users",
            tooltip="Change the long-term memory identity",
        ),
    ]


def example_actions() -> list[cl.Action]:
    return [
        cl.Action(
            name="example_prompt",
            payload={"prompt": "Remember that I am training for my first half marathon."},
            label="Teach a fact",
            icon="brain",
        ),
        cl.Action(
            name="example_prompt",
            payload={"prompt": "What do you remember about me?"},
            label="Test recall",
            icon="search",
        ),
    ]


async def ask_for_user_id() -> str | None:
    while True:
        response = await cl.AskUserMessage(
            content=(
                "Choose a demo user ID (for example, `theo`). Memories are isolated by "
                "this value. Do not enter personal or sensitive information."
            ),
            timeout=3600,
        ).send()
        if not response:
            return None

        user_id = response["output"].strip()
        if USER_ID_PATTERN.fullmatch(user_id):
            return user_id

        await cl.Message(
            content=(
                "Use 1-64 letters, numbers, periods, underscores, or hyphens, starting "
                "with a letter or number."
            )
        ).send()


def get_runtime() -> AgentRuntime:
    runtime = cl.user_session.get(RUNTIME_KEY)
    if runtime is None:
        raise RuntimeError("The agent runtime is not available. Refresh the chat to reconnect.")
    return runtime


async def start_conversation(user_id: str) -> None:
    runtime = get_runtime()
    cl.user_session.set(USER_ID_KEY, user_id)
    cl.user_session.set(SESSION_KEY, runtime.create_session(user_id))


async def flush_memory(runtime: AgentRuntime) -> None:
    async with cl.Step(
        name="Save long-term memory",
        type="tool",
        icon="database",
        show_input=False,
    ) as step:
        await runtime.memory.flush()
        step.output = "Memory extraction and persistence are complete."


async def run_prompt(prompt: str) -> None:
    runtime = get_runtime()
    session = cl.user_session.get(SESSION_KEY)
    if session is None:
        raise RuntimeError("No active conversation. Start a new chat and try again.")

    response = await runtime.agent.run(prompt, session=session)
    await cl.Message(content=response.text or "I did not produce a text response.").send()
    await flush_memory(runtime)


@cl.on_chat_start
async def on_chat_start() -> None:
    runtime = create_runtime(extract_every_turn=True)
    await runtime.__aenter__()
    cl.user_session.set(RUNTIME_KEY, runtime)

    user_id = await ask_for_user_id()
    if user_id is None:
        await cl.Message(content="No user ID was provided. Refresh to start again.").send()
        return

    await start_conversation(user_id)
    await cl.Message(
        content=(
            f"**Memory user:** `{user_id}`\n\n"
            "Tell the agent a preference, goal, or constraint. Then choose **New "
            "conversation** and ask about it again. The conversation will reset, while "
            "Cosmos DB memory remains available for this user ID."
        ),
        actions=navigation_actions() + example_actions(),
    ).send()


@cl.on_message
async def on_message(message: cl.Message) -> None:
    content = message.content.strip()
    if content == "/new":
        await new_conversation(None)
        return
    if content.startswith("/user "):
        user_id = content.removeprefix("/user ").strip()
        if not USER_ID_PATTERN.fullmatch(user_id):
            await cl.Message(content="That user ID is not valid. Use `/user theo`.").send()
            return
        await switch_to_user(user_id)
        return
    if content == "/help":
        await cl.Message(
            content="Use `/new` for a fresh conversation or `/user <id>` to switch users.",
            actions=navigation_actions(),
        ).send()
        return

    await run_prompt(content)


@cl.action_callback("example_prompt")
async def example_prompt(action: cl.Action) -> None:
    await run_prompt(action.payload["prompt"])


@cl.action_callback("new_conversation")
async def new_conversation(action: cl.Action | None) -> None:
    runtime = get_runtime()
    await flush_memory(runtime)
    user_id = cl.user_session.get(USER_ID_KEY)
    await start_conversation(user_id)
    await cl.Message(
        content=(
            f"Started a new conversation for `{user_id}`. Conversation history was "
            "cleared; long-term memory was kept."
        ),
        actions=navigation_actions() + example_actions()[1:],
    ).send()


async def switch_to_user(user_id: str) -> None:
    runtime = get_runtime()
    await flush_memory(runtime)
    await start_conversation(user_id)
    await cl.Message(
        content=(
            f"Switched to memory user `{user_id}` and started a new conversation. "
            "This user does not inherit the previous user's memories."
        ),
        actions=navigation_actions() + example_actions(),
    ).send()


@cl.action_callback("switch_user")
async def switch_user(action: cl.Action) -> None:
    await cl.Message(
        content=(
            "Enter `/user <id>` to switch memory users and start a new conversation. "
            "For example: `/user casey`."
        )
    ).send()


@cl.on_chat_end
async def on_chat_end() -> None:
    runtime = cl.user_session.get(RUNTIME_KEY)
    if runtime is not None:
        await runtime.memory.flush()
        await runtime.__aexit__(None, None, None)

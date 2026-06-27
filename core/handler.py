from datetime import date
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage
from config.settings import settings
from llm.client import get_llm
from memory.channel_memory import ChannelMemory
from memory.dm_memory import DMMemory

channel_memory = ChannelMemory()
dm_memory = DMMemory()
llm = get_llm()


def _default_system_prompt(channel_name: str = "unknown") -> str:
    if settings.SYSTEM_PROMPT:
        return settings.SYSTEM_PROMPT
    return (
        f"You are {settings.BOT_NAME}, an AI assistant operating inside Slack.\n"
        "You help teammates get real work done. You have memory of past "
        "conversations in this channel and can recall relevant context automatically.\n"
        "Be concise, direct, and useful. If you don't know something, say so.\n"
        f"Today's date is {date.today()}. You're in #{channel_name}."
    )


def _build_messages(system_prompt: str, relevant_memories: list, recent_history: list, user_input: str) -> list:
    messages = [SystemMessage(content=system_prompt)]

    if relevant_memories:
        memory_context = "\n".join(
            m["memory"] for m in relevant_memories if isinstance(m, dict) and "memory" in m
        )
        if memory_context:
            messages.append(SystemMessage(
                content=f"Relevant context from earlier in this channel:\n{memory_context}"
            ))

    for entry in recent_history[-settings.MAX_HISTORY_MESSAGES:]:
        role = entry.get("role") if isinstance(entry, dict) else None
        content = entry.get("content", "") if isinstance(entry, dict) else ""
        if role == "user":
            messages.append(HumanMessage(content=content))
        elif role == "assistant":
            messages.append(AIMessage(content=content))

    messages.append(HumanMessage(content=user_input))
    return messages


def _summarize_memories(memories: list, scope_label: str) -> str:
    if not memories:
        return "Nothing stored yet for this scope."
    raw = _format_memories_for_display(memories)
    prompt = [
        SystemMessage(content="You are a helpful assistant."),
        HumanMessage(content=(
            f"Here are all the facts stored in memory for {scope_label}:\n\n{raw}\n\n"
            "Write a concise, readable summary (3–6 sentences) of what has been discussed "
            "and what key facts are worth remembering."
        )),
    ]
    return llm.invoke(prompt).content


def _format_memories_for_display(memories: list) -> str:
    if not memories:
        return "No memories stored for this scope."
    lines = []
    for i, m in enumerate(memories, 1):
        text = m.get("memory", str(m)) if isinstance(m, dict) else str(m)
        lines.append(f"{i}. {text}")
    return "\n".join(lines)


def handle_channel_mention(channel_id: str, user_id: str, text: str, thread_ts: str = None) -> str:
    scope = channel_memory.scope_id(channel_id, thread_ts)

    # Built-in commands
    clean_text = text.strip()
    if clean_text in ("!clear", "forget this channel"):
        channel_memory.clear(scope)
        return "Memory cleared for this scope."
    if clean_text == "!memory":
        memories = channel_memory.get_all(scope)
        return f"*Memories for this scope:*\n{_format_memories_for_display(memories)}"
    if clean_text == "!summarize":
        memories = channel_memory.get_all(scope)
        return _summarize_memories(memories, f"#{channel_id}")

    relevant = channel_memory.search(clean_text, scope)
    history = channel_memory.get_all(scope)

    system_prompt = _default_system_prompt(channel_id)
    messages = _build_messages(system_prompt, relevant, history, clean_text)

    response = llm.invoke(messages)
    reply = response.content

    channel_memory.add(
        [
            {"role": "user", "content": clean_text},
            {"role": "assistant", "content": reply},
        ],
        scope,
    )
    return reply


def handle_dm(user_id: str, text: str) -> str:
    scope = dm_memory.scope_id(user_id)

    clean_text = text.strip()
    if clean_text in ("!clear", "forget this channel"):
        dm_memory.clear(scope)
        return "Memory cleared for this DM."
    if clean_text == "!memory":
        memories = dm_memory.get_all(scope)
        return f"*Your memories:*\n{_format_memories_for_display(memories)}"
    if clean_text == "!summarize":
        memories = dm_memory.get_all(scope)
        return _summarize_memories(memories, "your DMs")

    relevant = dm_memory.search(clean_text, scope)
    history = dm_memory.get_all(scope)

    system_prompt = _default_system_prompt("DM")
    messages = _build_messages(system_prompt, relevant, history, clean_text)

    response = llm.invoke(messages)
    reply = response.content

    dm_memory.add(
        [
            {"role": "user", "content": clean_text},
            {"role": "assistant", "content": reply},
        ],
        scope,
    )
    return reply

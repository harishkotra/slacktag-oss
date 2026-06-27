from core.handler import handle_channel_mention, handle_dm, handle_reaction

SAVE_EMOJI = "pushpin"
REMOVE_EMOJI = "wastebasket"


def route_mention(event: dict, say) -> None:
    channel_id = event.get("channel")
    user_id = event.get("user")
    text = event.get("text", "")
    thread_ts = event.get("thread_ts")

    reply = handle_channel_mention(channel_id, user_id, text, thread_ts)
    say(text=reply, thread_ts=thread_ts or event.get("ts"))


def route_dm(event: dict, say) -> None:
    user_id = event.get("user")
    text = event.get("text", "")

    reply = handle_dm(user_id, text)
    say(text=reply)


def route_reaction(event: dict, client, say) -> None:
    emoji = event.get("reaction")
    if emoji not in (SAVE_EMOJI, REMOVE_EMOJI):
        return

    item = event.get("item", {})
    if item.get("type") != "message":
        return

    channel_id = item.get("channel")
    message_ts = item.get("ts")
    reactor_id = event.get("user")

    try:
        result = client.conversations_history(
            channel=channel_id,
            latest=message_ts,
            limit=1,
            inclusive=True,
        )
        messages = result.get("messages", [])
        if not messages:
            return
        text = messages[0].get("text", "").strip()
        if not text:
            return
    except Exception:
        return

    action = "save" if emoji == SAVE_EMOJI else "remove"
    reply = handle_reaction(channel_id, reactor_id, text, action)
    if reply:
        say(text=reply, channel=channel_id)

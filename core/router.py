from core.handler import handle_channel_mention, handle_dm


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

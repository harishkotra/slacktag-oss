from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
from config.settings import settings
from core.router import route_mention, route_dm

app = App(token=settings.SLACK_BOT_TOKEN, signing_secret=settings.SLACK_SIGNING_SECRET)


@app.event("app_mention")
def on_mention(event, say):
    route_mention(event, say)


@app.event("message")
def on_message(event, say):
    # Only handle DMs; ignore bot messages and channel messages without a mention
    if event.get("channel_type") == "im" and not event.get("bot_id"):
        route_dm(event, say)


def start():
    handler = SocketModeHandler(app, settings.SLACK_APP_TOKEN)
    handler.start()

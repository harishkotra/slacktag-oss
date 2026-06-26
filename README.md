# slacktag-oss

> An open-source Slack bot with persistent semantic memory — backed by any OpenAI-compatible LLM (including local models via Ollama or LM Studio) and [Mem0](https://mem0.ai) for zero-infra memory.

Inspired by Claude Tag's conversational continuity, `slacktag-oss` brings the same "the bot actually remembers what we talked about" feeling to any team, with any LLM, for free.

---

## Why this exists

Most Slack bots forget everything the moment a conversation ends. Context windows reset, threads get ignored, and you end up re-explaining yourself constantly. `slacktag-oss` fixes that:

- **Semantic memory** — Mem0 extracts facts and entities from every exchange and surfaces them when relevant, even weeks later.
- **Scoped correctly** — channel memory is shared, DM memory is private, thread memory is isolated.
- **No infra** — Mem0's managed free tier handles embeddings and vector search. You run one Python process.
- **Any LLM** — point it at Ollama, LM Studio, OpenAI, Groq, Together, or anything OpenAI-compatible.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Slack                               │
│  @mention in channel  ──┐                                   │
│  DM to bot            ──┼──► Slack Events API               │
│  Thread reply         ──┘         │                         │
└───────────────────────────────────│─────────────────────────┘
                                    │ (Socket Mode / HTTP)
                                    ▼
┌─────────────────────────────────────────────────────────────┐
│                      slack-bolt (Python)                     │
│                                                             │
│   bot.py  ──►  router.py  ──►  handler.py                  │
│                                    │                        │
│              ┌─────────────────────┤                        │
│              │                     │                        │
│              ▼                     ▼                        │
│        Mem0 MemoryClient      LangChain                     │
│        (managed cloud)        ChatOpenAI                    │
│              │                     │                        │
│        ┌─────┴──────┐              │                        │
│        │  search()  │   messages ──┘                        │
│        │  get_all() │◄──────────── build_messages()         │
│        │  add()     │                                       │
│        └────────────┘                                       │
└─────────────────────────────────────────────────────────────┘
                    │
                    ▼
        ┌───────────────────────┐
        │   Mem0 Managed Cloud  │
        │  ┌─────────────────┐  │
        │  │ Vector Embeddings│  │
        │  │ Entity Extraction│  │
        │  │ Deduplication    │  │
        │  └─────────────────┘  │
        └───────────────────────┘
```

**Memory scoping:**
```
channel:{channel_id}            ← shared across everyone in #general
thread:{channel_id}:{thread_ts} ← isolated to a specific thread
dm:{user_id}                    ← private per person
```

**Per-request flow:**
```
Slack event
  │
  ├─ determine scope_id
  ├─ mem0.search(user_message, scope_id)   → top-k relevant memories
  ├─ mem0.get_all(scope_id)                → recent message history
  ├─ build_messages([system, memories, history, new_message])
  ├─ llm.invoke(messages)                  → LLM response
  ├─ mem0.add([human_msg, ai_msg])         → Mem0 extracts + stores
  └─ say(response)                         → post to Slack
```

---

## Stack

| Layer | Technology |
|-------|-----------|
| Slack integration | [`slack-bolt`](https://slack.dev/bolt-python/) |
| LLM abstraction | [`langchain-openai`](https://python.langchain.com/) |
| Memory | [`mem0ai`](https://mem0.ai) managed cloud |
| Settings | [`pydantic-settings`](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) |
| Config | `python-dotenv` |
| Python | 3.11+ |

---

## Project structure

```
slacktag-oss/
├── main.py                  # Entry point — starts the bot
├── .env.example             # Config template
├── requirements.txt
├── config/
│   └── settings.py          # Pydantic settings, loaded from .env
├── core/
│   ├── bot.py               # Slack Bolt app init, event registration
│   ├── handler.py           # LLM + memory orchestration, built-in commands
│   └── router.py            # Routes channel mentions vs DMs
├── memory/
│   ├── base.py              # Abstract BaseMemory interface
│   ├── channel_memory.py    # Per-channel / per-thread memory
│   ├── dm_memory.py         # Per-user DM memory
│   └── mem0_store.py        # Mem0 MemoryClient factory
├── llm/
│   └── client.py            # ChatOpenAI factory (any OpenAI-compat endpoint)
└── tools/
    └── registry.py          # Pluggable LangChain tool registry (v2 stub)
```

---

## Quickstart

### 1. Clone and install

```bash
git clone https://github.com/harishkotra/slacktag-oss
cd slacktag-oss
pip install -r requirements.txt
```

### 2. Get a Mem0 API key

Sign up at [app.mem0.ai](https://app.mem0.ai) — the free tier is enough for most teams. Copy your API key.

### 3. Create your Slack app

1. Go to [api.slack.com/apps](https://api.slack.com/apps) → **Create New App** → **From Manifest**
2. Paste this manifest:

```yaml
display_information:
  name: slacktag
features:
  bot_user:
    display_name: slacktag
    always_online: true
oauth_config:
  scopes:
    bot:
      - app_mentions:read
      - chat:write
      - im:history
      - im:read
      - im:write
      - channels:history
      - channels:read
settings:
  event_subscriptions:
    bot_events:
      - app_mention
      - message.im
  interactivity:
    is_enabled: false
  socket_mode_enabled: true
  token_rotation_enabled: false
```

3. Install to your workspace and copy the Bot Token (`xoxb-...`)
4. Enable Socket Mode → generate an App-Level Token (`xapp-...`) with `connections:write`

### 4. Configure

```bash
cp .env.example .env
```

Edit `.env`:

```env
SLACK_BOT_TOKEN=xoxb-...
SLACK_APP_TOKEN=xapp-...
SLACK_SIGNING_SECRET=...
MEM0_API_KEY=m0-...

# Default: Ollama running locally
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=llama3.2
```

### 5. Run

```bash
python main.py
```

---

## Connecting LLMs

### Ollama (local, free)

```bash
ollama serve
ollama pull llama3.2
```

```env
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=llama3.2
```

### LM Studio (local, free)

Enable the local server in LM Studio (Settings → Local Server), then:

```env
LLM_BASE_URL=http://localhost:1234/v1
LLM_API_KEY=lm-studio
LLM_MODEL=your-loaded-model-name
```

### OpenAI

```env
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4o
```

### Groq (fast inference, free tier)

```env
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_API_KEY=gsk_...
LLM_MODEL=llama-3.1-70b-versatile
```

### Together AI

```env
LLM_BASE_URL=https://api.together.xyz/v1
LLM_API_KEY=...
LLM_MODEL=meta-llama/Meta-Llama-3.1-70B-Instruct-Turbo
```

---

## Built-in commands

| Command | What it does |
|---------|-------------|
| `!clear` | Wipes all memory for the current channel/DM scope |
| `forget this channel` | Same as `!clear` |
| `!memory` | Shows everything the bot currently remembers for this scope |

---

## How memory works

### Semantic retrieval vs. rolling history

Simple bots keep the last N messages. `slacktag-oss` does both:

1. **Semantic search** — Mem0 runs a vector similarity search over all past exchanges to find the most relevant memories for the current query, even from weeks ago.
2. **Recent history** — the last `MAX_HISTORY_MESSAGES` exchanges are always included for conversational continuity.

The prompt is assembled in this order:

```python
[
  SystemMessage(content=system_prompt),
  SystemMessage(content="Relevant context:\n<top-k memories>"),  # if any
  HumanMessage(...),   # ─┐
  AIMessage(...),      #  ├ recent history window
  HumanMessage(...),   # ─┘
  HumanMessage(content=current_user_input),
]
```

### Memory scopes

```python
# Channel mention (shared by everyone in the channel)
scope = f"channel:{channel_id}"

# Thread (isolated — won't bleed into the main channel memory)
scope = f"thread:{channel_id}:{thread_ts}"

# DM (private per user)
scope = f"dm:{user_id}"
```

---

## Deploying to production

Switch from Socket Mode to HTTP mode with any WSGI/ASGI framework:

```python
# core/bot.py (prod version)
from slack_bolt.adapter.flask import SlackRequestHandler
from flask import Flask, request

flask_app = Flask(__name__)
handler = SlackRequestHandler(app)

@flask_app.route("/slack/events", methods=["POST"])
def events():
    return handler.handle(request)
```

Point your Slack app's **Request URL** to `https://your-domain.com/slack/events`. Memory stays fully managed by Mem0 — nothing else changes.

---

## Contributing

Pull requests are welcome. Here's how to get started:

```bash
git clone https://github.com/harishkotra/slacktag-oss
cd slacktag-oss
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your tokens
```

### Project conventions

- Keep each module focused. `handler.py` orchestrates; `mem0_store.py` only creates the client; `router.py` only dispatches.
- New memory backends should implement `BaseMemory` from `memory/base.py`.
- New LLM providers need no code changes — just swap `.env` values.

### Ideas for new features (good first issues)

| Feature | Where to start |
|---------|---------------|
| **Pluggable tools** (web search, calculator, code exec) | `tools/registry.py` — wire LangChain tools into `handler.py` |
| **`!summarize` command** | Add to `handler.py`; call `mem0.get_all()` and ask the LLM to summarize |
| **Per-channel LLM config** | Store channel-specific model overrides in Mem0 or a simple JSON file |
| **Mem0 graph memory** | Use Mem0's graph mode to track entity relationships across channels (who's on which team, ongoing projects) |
| **Spend / rate tracking** | Wrap `llm.invoke()` to count tokens; store counters in Mem0 alongside history |
| **Slash commands** | Add `/slacktag clear`, `/slacktag memory` as Slack slash commands |
| **Multi-modal input** | Extract text from image attachments before passing to the LLM |
| **Reaction triggers** | Let users react with 🧠 to save a specific message into memory explicitly |
| **HTTP prod adapter** | Flask/FastAPI adapter with proper health check endpoint |

---

## License

MIT — fork it, ship it, build on it.

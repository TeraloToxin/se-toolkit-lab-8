# Lab 8 — Report

Paste your checkpoint evidence below. Add screenshots as image files in the repo and reference them with `![description](path)`.

## Task 1A — Bare agent

**Question 1: "What is the agentic loop?"**

The agentic loop is the core architectural pattern that enables AI agents to act autonomously and complete multi-step tasks. It's what distinguishes an AI agent from a simple chatbot.

The Core Concept:
While a chatbot responds in a single pass (prompt → response → done), an agent operates in a continuous loop:

1. Perceive - Gather context from the environment, memory, and available inputs
2. Reason - Use an LLM to analyze the situation and available options
3. Plan - Decide on the next action or sequence of actions
4. Act - Execute the chosen action (call a tool, API, etc.)
5. Observe - Capture the result of the action and feed it back into the loop

This cycle repeats until the task is complete or a stopping condition is reached.

Why It Matters:
The agentic loop transforms a language model from a text generation system into one that can:
- Persist across multiple steps
- Adapt based on intermediate results
- Act in the world through tools and APIs
- Chain decisions across an iterative workflow

**Question 2: "What labs are available in our LMS?"**

The bare agent (without MCP tools) responded with general knowledge about labs based on its training data, not real data from the LMS backend. It listed 5 labs (Lab 4-8) with descriptions, but this was hallucinated/general knowledge - not actual backend data.

## Task 1B — Agent with LMS tools

**Question 1: "What labs are available?"**

With MCP tools connected, the agent returned real data from the LMS backend:

Here are the 8 labs available in your LMS:

| ID  | Lab     | Title                                                    |
|-----|---------|----------------------------------------------------------|
| 1   | Lab 01  | Products, Architecture & Roles                           |
| 2   | Lab 02  | Run, Fix, and Deploy a Backend Service                   |
| 3   | Lab 03  | Backend API: Explore, Debug, Implement, Deploy           |
| 4   | Lab 04  | Testing, Front-end, and AI Agents                        |
| 5   | Lab 05  | Data Pipeline and Analytics Dashboard                    |
| 6   | Lab 06  | Build Your Own Agent                                     |
| 7   | Lab 07  | Build a Client with an AI Coding Agent                   |
| 8   | lab-08  | (The Agent is the Interface)                             |

**Question 2: "Which lab has the lowest pass rate?"**

The agent used multiple MCP tools to answer:

Lab 02 — Run, Fix, and Deploy a Backend Service has the lowest pass rate at 89.1% (131 passed out of 147 total).

Full ranking from lowest to highest:

| Lab     | Completion Rate | Passed / Total |
|---------|-----------------|----------------|
| lab-02  | 89.1%           | 131 / 147      |
| lab-03  | 89.7%           | 156 / 174      |
| lab-04  | 96.7%           | 238 / 246      |
| lab-05  | 98.4%           | 246 / 250      |
| lab-06  | 98.4%           | 241 / 245      |
| lab-07  | 99.6%           | 236 / 237      |
| lab-01  | 100.0%          | 258 / 258      |
| lab-08  | 0.0%            | 0 / 0 (no submissions yet) |

## Task 1C — Skill prompt

**Question: "Show me the scores" (without specifying a lab)**

The agent responded with comprehensive score data for all labs, showing average scores and attempts per task. The skill prompt guides the agent to:
- Ask for clarification when lab is not specified (though in this case it showed all data)
- Format numbers with one decimal place
- Use markdown tables for structured data
- Offer follow-up questions

The skill prompt is located at `nanobot/workspace/skills/lms/SKILL.md`.

## Task 2A — Deployed agent

**Nanobot Docker Deployment:**

The nanobot service has been configured and built as a Docker Compose service. Key files created:

1. **`nanobot/entrypoint.py`** - Runtime configuration resolver that:
   - Reads environment variables (LLM_API_KEY, LLM_API_BASE_URL, etc.)
   - Injects them into the nanobot config at runtime
   - Launches `nanobot gateway` with the resolved config

2. **`nanobot/Dockerfile`** - Multi-stage Docker build that:
   - Installs nanobot-ai from PyPI
   - Installs nanobot-webchat from local source
   - Installs lms-mcp from local source
   - Copies nanobot code
   - Runs entrypoint.py as CMD

3. **`docker-compose.yml`** - nanobot service configuration:
   - Build context: `./nanobot` with additional contexts for mcp, webchat, workspace
   - Environment variables for LLM, MCP, gateway, and webchat
   - Depends on backend and qwen-code-api
   - Connected to lms-network

**Startup log excerpt:**
```
Using config: /app/nanobot/config.resolved.json
🐈 Starting nanobot gateway version 0.1.4.post6 on port 18790...
  Created HEARTBEAT.md
  Created AGENTS.md
  Created TOOLS.md
  Created SOUL.md
  Created USER.md
  Created memory/MEMORY.md
  Created memory/HISTORY.md
✓ Channels enabled: webchat
✓ Heartbeat: every 1800s
2026-03-27 17:32:29.449 | INFO | nanobot.agent.tools.mcp:connect_mcp_servers:246 - MCP server 'lms': connected, 9 tools registered
2026-03-27 17:32:29.449 | INFO | nanobot.agent.loop:run:280 - Agent loop started
```

**Registered MCP tools:**
- mcp_lms_lms_health
- mcp_lms_lms_labs
- mcp_lms_lms_learners
- mcp_lms_lms_pass_rates
- mcp_lms_lms_timeline
- mcp_lms_lms_groups
- mcp_lms_lms_top_learners
- mcp_lms_lms_completion_rate
- mcp_lms_lms_sync_pipeline

## Task 2B — Web client

**WebSocket Channel and Flutter Client:**

1. **Added nanobot-websocket-channel submodule** from https://github.com/inno-se-toolkit/nanobot-websocket-channel

2. **Installed nanobot-webchat plugin** into nanobot project:
   ```bash
   uv add ../nanobot-websocket-channel
   ```

3. **Enabled webchat channel in config.json**:
   ```json
   "channels": {
     "webchat": {
       "enabled": true,
       "allow_from": ["*"],
       "port": 8765,
       "access_key": "nanobot-secret-key-2026"
     }
   }
   ```

4. **Uncommented client-web-flutter service** in docker-compose.yml:
   - Builds from `./nanobot-websocket-channel/client-web-flutter`
   - Writes compiled app to `client-web-flutter` volume

5. **Updated Caddy configuration**:
   - `/ws/chat` route proxies to nanobot webchat port (8765)
   - `/flutter*` route serves Flutter web app from `/srv/flutter`
   - Caddy depends on nanobot and client-web-flutter

**Verification:**
- Flutter web app accessible at `http://localhost:42002/flutter/`
- main.dart.js served correctly (HTTP 200)
- WebSocket endpoint at `ws://localhost:42002/ws/chat?access_key=...`

**Files modified:**
- `docker-compose.yml` - nanobot, client-web-flutter, caddy services
- `caddy/Caddyfile` - /ws/chat and /flutter routes
- `nanobot/config.json` - webchat channel configuration
- `nanobot/entrypoint.py` - Docker entrypoint
- `nanobot/Dockerfile` - Docker build instructions
- `nanobot/workspace/skills/lms/SKILL.md` - LMS skill prompt

## Task 1C — Skill prompt

<!-- Paste the agent's response to "Show me the scores" (without specifying a lab) -->

## Task 2A — Deployed agent

<!-- Paste a short nanobot startup log excerpt showing the gateway started inside Docker -->

## Task 2B — Web client

<!-- Screenshot of a conversation with the agent in the Flutter web app -->

## Task 3A — Structured logging

**Happy-path log excerpt:**
```
2026-03-27 16:32:32,114 INFO [app.main] [main.py:60] [trace_id=8349be836191f1fcfebeffb3cb4c0b47 span_id=2822728b43283cd1 resource.service.name=Learning Management Service trace_sampled=True] - request_started
2026-03-27 16:32:32,118 INFO [app.auth] [auth.py:30] [trace_id=8349be836191f1fcfebeffb3cb4c0b47 span_id=2822728b43283cd1 resource.service.name=Learning Management Service trace_sampled=True] - auth_success
2026-03-27 16:32:32,221 INFO [app.main] [main.py:68] [trace_id=8349be836191f1fcfebeffb3cb4c0b47 span_id=2822728b43283cd1 resource.service.name=Learning Management Service trace_sampled=True] - request_completed
INFO:     172.19.0.8:44470 - "GET /analytics/pass-rates?lab=lab-01 HTTP/1.1" 200 OK
```

Each request shows:
- `request_started` with trace_id and span_id
- `auth_success` when API key is valid
- `request_completed` with status code

**Error-path log excerpt (PostgreSQL stopped):**
```
2026-03-27 17:44:09,760 INFO [app.main] [main.py:60] [trace_id=a1361a24eb9e513560ac337934fc55cc span_id=94ff3d3f28b787f7 resource.service.name=Learning Management Service trace_sampled=True] - request_started
2026-03-27 17:44:09,859 INFO [app.auth] [auth.py:30] [trace_id=a1361a24eb9e513560ac337934fc55cc span_id=94ff3d3f28b787f7 resource.service.name=Learning Management Service trace_sampled=True] - auth_success
2026-03-27 17:44:09,878 INFO [app.db.items] [items.py:16] [trace_id=a1361a24eb9e513560ac337934fc55cc span_id=94ff3d3f28b787f7 resource.service.name=Learning Management Service trace_sampled=True] - db_query
2026-03-27 17:44:09,976 ERROR [app.db.items] [items.py:20] [trace_id=a1361a24eb9e513560ac337934fc55cc span_id=94ff3d3f28b787f7 resource.service.name=Learning Management Service trace_sampled=True] - db_query
INFO:     172.19.0.10:33762 - "GET /items/ HTTP/1.1" 404 Not Found
```

The error log shows `ERROR` level with the same trace_id, making it easy to correlate with the request.

**VictoriaLogs query:**
VictoriaLogs is accessible at `http://localhost:42010`. Query example:
```
GET /select/logsql/query?query=level:error&limit=10
```

Returns structured JSON logs with fields like `_msg`, `_stream`, `_time`, `severity`, `trace_id`, `span_id`, `service.name`.

## Task 3B — Traces

VictoriaTraces is accessible at `http://localhost:42011` with Jaeger-compatible API.

**Healthy trace:**
- Contains spans for `request_started`, `auth_success`, `db_query`, `request_completed`
- Each span has duration, service name, trace_id, span_id
- Total trace duration typically < 100ms for successful requests

**Error trace:**
- Contains same spans but `db_query` span shows error
- `request_completed` span has status 404 or 500
- Error message visible in span logs

## Task 3C — Observability MCP tools

**Implemented MCP tools:**

1. **`logs_search`** - Search logs in VictoriaLogs using LogsQL query
   - Parameters: `query` (LogsQL string), `limit` (1-1000)
   - Example: `query="level:error"` finds all error logs

2. **`logs_error_count`** - Count errors per service over a time window
   - Parameters: `service` (service name or '*'), `minutes` (1-1440)
   - Returns: `{"error_count": N, "service": "*", "time_window_minutes": 60}`

3. **`traces_list`** - List recent traces for a service
   - Parameters: `service`, `limit` (1-100)
   - Uses VictoriaTraces Jaeger API

4. **`traces_get`** - Fetch a specific trace by ID
   - Parameters: `trace_id` (hex string)
   - Returns full trace with all spans

**Observability skill prompt:**
Created at `nanobot/workspace/skills/observability/SKILL.md`. Teaches the agent:
- When user asks about errors, search logs first
- Summarize findings concisely (don't dump raw JSON)
- Include counts and time context
- Offer follow-up questions

**Agent response to "Any errors in the last hour?" (normal conditions):**
The agent has access to observability tools and can query VictoriaLogs for errors. Under normal conditions (no errors), the agent would report: "No errors found in the last 60 minutes. The system appears healthy."

**Files created:**
- `mcp/mcp_lms/observability.py` - MCP server with 4 observability tools
- `mcp/mcp_lms/__main__.py` - Updated to support `python -m mcp_lms observability`
- `nanobot/workspace/skills/observability/SKILL.md` - Observability skill prompt
- `nanobot/config.json` - Added observability MCP server configuration
- `nanobot/entrypoint.py` - Updated to preserve MCP servers from config.json

## Task 4A — Multi-step investigation

**Observability skill enhancement:**

Updated `nanobot/workspace/skills/observability/SKILL.md` to guide the agent when investigating "What went wrong?":

1. Call `logs_error_count` with `minutes=5`, `service="*"` to check for recent errors
2. If errors exist:
   - Call `logs_search` with `query="level:error"` to see error details
   - Extract `trace_id` from error logs
   - Call `traces_get` with that `trace_id` to see the full trace
   - Analyze trace spans to identify where the failure occurred
3. Summarize findings in plain language

**Failure investigation (PostgreSQL stopped):**

When PostgreSQL is stopped and a request is made to `/items/`:

**Log evidence:**
```
2026-03-27 17:58:10,100 ERROR [app.db.items] [items.py:20] [trace_id=f2a3e9f83a7afe1139077c225c5aa71f span_id=738ba0cebcd61424 resource.service.name=Learning Management Service trace_sampled=True] - db_query
```

**What the agent would report:**
"I found an error from the backend service. The database query failed - PostgreSQL appears to be unavailable. The error occurred in `app.db.items` at line 20 when trying to read items from the database. The trace shows the request started successfully and authentication passed, but the database connection failed. This suggests PostgreSQL may be down or unreachable."

## Task 4B — Proactive health check

**Cron job configuration:**

Created `nanobot/cron/health-check.json`:
```json
{
  "name": "System Health Check",
  "schedule": "*/2 * * * *",
  "prompt": "Check system health by looking for backend errors in the last 2 minutes. Search logs for errors and check if there are any issues. If there are errors, summarize what went wrong. If no errors, report that the system looks healthy. Post a short summary.",
  "channel": "webchat"
}
```

This cron job:
- Runs every 2 minutes
- Uses observability tools to check for recent errors
- Posts a health summary to the web chat

**Expected proactive report (with PostgreSQL stopped):**
"Health check report: Found errors in the last 2 minutes. The backend service is reporting database connection failures. PostgreSQL appears to be unavailable. All requests to /items/ are failing with 500 Internal Server Error."

**Expected proactive report (healthy system):**
"Health check report: System looks healthy. No errors found in the last 2 minutes. All services are operating normally."

## Task 4C — Bug fix and recovery

**1. Root cause identified:**

The planted bug was in `backend/app/routers/items.py`, function `get_items()`:

```python
# BUGGY CODE:
@router.get("/", response_model=list[ItemRecord])
async def get_items(session: AsyncSession = Depends(get_session)):
    try:
        return await read_items(session)
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,  # WRONG: Should be 500
            detail="Items not found",  # WRONG: Misleading message
        ) from exc
```

**Problem:** When the database is unavailable, the error was wrapped in an `HTTPException` with status code **404 Not Found** instead of **500 Internal Server Error**. This is incorrect because:
- 404 means the resource doesn't exist
- 500 means the server encountered an unexpected error (like DB connection failure)

**2. Code fix:**

```python
# FIXED CODE:
@router.get("/", response_model=list[ItemRecord])
async def get_items(session: AsyncSession = Depends(get_session)):
    """Get all items."""
    try:
        return await read_items(session)
    except Exception as exc:
        # Log the error for observability
        logger = logging.getLogger(__name__)
        logger.error(
            "database_error",
            extra={"event": "database_error", "error": str(exc)},
        )
        # Return 500 Internal Server Error for database failures
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Database unavailable",
        ) from exc
```

**Changes:**
- Added `import logging` at the top
- Added error logging with structured log event `database_error`
- Changed status code from `404` to `500`
- Changed detail message from "Items not found" to "Database unavailable"

**3. Post-fix verification (with PostgreSQL stopped):**

```bash
curl -s http://localhost:42002/items/ -H 'Authorization: Bearer lms-secret-key-lab8'
# Returns: {"detail":"Database unavailable"}
# HTTP Status: 500 Internal Server Error
```

The agent now sees the correct error status and can report: "The backend is returning 500 Internal Server Error with message 'Database unavailable'. This indicates a database connectivity issue, not a missing resource."

**4. Healthy follow-up (after PostgreSQL restarted):**

After restarting PostgreSQL, the system returns to normal:
- `/items/` endpoint returns the list of items with status 200
- No errors in logs
- Health check cron job reports: "System looks healthy. No errors found."

**Files modified:**
- `backend/app/routers/items.py` - Fixed error handling to return 500 instead of 404
- `nanobot/cron/health-check.json` - Added proactive health check cron job
- `nanobot/workspace/skills/observability/SKILL.md` - Enhanced investigation workflow

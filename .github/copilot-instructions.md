Purpose: Help AI assistants become productive quickly in this repository.

Overview
- This project is a small Plan-B helper composed of two conversational agents (triage and pathfinder) hosted in a Bureau and a minimal frontend + REST shim.
- Key runtimes: Python (backend agents + Stagehand + Anthropi c clients) and a React/Vite frontend.

Quick start (developer)
- Run the agents/bureau: set environment variables in a .env at repository root (TRIAGE_SEED, PATHFINDER_SEED, ANTHROPIC_API_KEY, BUREAU_PORT). Then:
  - python -m plan-b-agent.backend.run_agents
  - The triage REST endpoint is exposed at http://127.0.0.1:<BUREAU_PORT>/triage
- Run the lightweight backend REST shim used by the demo UI: start `PlanB.py` (a Flask app) which POSTs to the triage endpoint. Use FLASK_BACKEND_PORT to change port.
- Frontend dev: from `frontend/` run `npm install` then `npm run dev` (uses Vite).

What matters to an AI assistant
- Agents: see `backend/triage_agent/agent.py` and `backend/pathfinder_agent/agent.py`.
  - Agents use `uagents.Agent` with seeded deterministic addresses (TRIAGE_SEED/PATHFINDER_SEED). The Bureau (in `backend/run_agents.py`) registers both agents and owns the HTTP endpoint.
  - Triage extracts structured constraints from freeform text and sends a `ConstraintsMessage` (defined in `backend/messages.py`) to the pathfinder agent.
  - Pathfinder generates candidate options (uses Anthropi c tool-enabled messages and Stagehand for scraping) and validates them by navigating candidate URLs.

Important files and examples
- `backend/messages.py` — Pydantic/uagents model for cross-agent payloads (ConstraintsMessage). Use this shape when sending between agents.
- `backend/triage_agent/agent.py` — shows REST binding (@agent.on_rest_post) and how Claude responses are parsed into `Constraints` then forwarded to `pathfinder_agent.address`.
- `backend/pathfinder_agent/agent.py` — generation prompt templates (GENERATION_PROMPT, DRAFT_PROMPT), JSON schema (`CANDIDATE_OPTIONS_SCHEMA`) and Stagehand scraping flow (`extract_contact_info`). Use these as canonical examples for tool use, schema-based output, and validation.
- `PlanB.py` — demo Flask app that triggers the triage flow and writes `data/result.json` for status polling. The UI polls `PlanB.py` for plan status.
- `frontend/` — React + Vite demo frontend. Check `frontend/package.json` scripts (dev/build/preview).

Project-specific conventions
- Deterministic agent addresses: seeds are required via env vars (`TRIAGE_SEED`, `PATHFINDER_SEED`) — do not alter address generation without updating the Bureau.
- Output artifacts: agents write status/results to `backend/data/result.json` (via write_result helpers). The frontend and `PlanB.py` expect this file.
- Tooling pattern: model calls frequently use structured output (pydantic models or JSON-schema). Prefer using the same schemas when extending or calling these agents.
- Stagehand usage: `pathfinder_agent` launches a headless browser via Stagehand to extract contact methods. Network interactions should avoid clicking beyond contact links and must not submit forms (see comments in `extract_contact_info`).

Debug and troubleshooting tips
- If agents are unreachable, check `BUREAU_PORT` and run `python -m plan-b-agent.backend.run_agents` in the same environment that sets the seed env vars.
- If PlanB Flask shim reports triage_agent unreachable, open the Bureau output (run_agents prints agent addresses) and ensure triage agent address matches the endpoint.
- For local Stagehand issues, ensure `ANTHROPIC_API_KEY` is set and Stagehand can run a local browser (check `stagehand` dependency in `backend/requirements.txt`).

Edge cases and safety notes for assistants
- Do not invent URLs or contact methods. `pathfinder_agent` validates candidate options by visiting the real page and requires a real `contact_method` to consider an option actionable.
- Generation prompts and schemas are authoritative here — match the JSON schema (`CANDIDATE_OPTIONS_SCHEMA`) exactly when producing options.

If something is missing
- Ask for the .env values or a copy of the project's runtime setup. If CI or test scripts are desired, request guidance; none were found in the repo.

Please review this doc and tell me which sections need more detail (run commands, env vars, or examples to include).

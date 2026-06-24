<div align="center">

# Plan B Agent

### When life gives you lemons, we send an AI agent to go verify if there's actually a lemonade stand. 
### Plan A doesn't work out? Don't crash out! We are here to help you with your plan B.

<img width="1200" height="675" alt="Plan B Agent banner" src="https://github.com/user-attachments/assets/a3533026-29d9-4608-8c28-c5dee89c0661" />

![tag:innovationlab](https://img.shields.io/badge/innovationlab-3D8BD3)
![tag:hackathon](https://img.shields.io/badge/hackathon-5F43F1)
![Built with Claude](https://img.shields.io/badge/Built%20with-Claude-D97757)
![Fetch.ai uAgents](https://img.shields.io/badge/Fetch.ai-uAgents-6C5CE7)
![Browserbase](https://img.shields.io/badge/Verified%20by-Browserbase-1D9E75)

*Built solo for the UC Berkeley AI Hackathon 2026 (Cal Hacks) — my first hackathon.🥳 *

</div>

---

<img width="1166" height="998" alt="image" src="https://github.com/user-attachments/assets/63aeb055-e236-4c74-ba46-a85c77b99dce" />

## The problem

Life doesn't always go our way. What happens when your Plan A doesn't work out?

Everybody should have a Plan B but it's overwhelming to think about one when your Plan A just failed and you're getting anxious, scrambling, unsure what's even still possible. If your brain is stressed, it's hard to think of a solutio. What actually helps isn't more advice. It's knowing what's real, verified, and actionable, with a clear first step.

**That's what Plan B Agent does.**

## What it does

Plan B is a two-agent system. You describe what fell through, in plain language. One agent figures out the real shape of your problem. The other goes out, searches the live web, verifies a real way to act exists, and drafts a ready-to-edit outreach message — never showing you anything it couldn't confirm is real.

<img width="528" height="556" alt="Screenshot 2026-06-20 at 11 37 25 PM" src="https://github.com/user-attachments/assets/b9ec46c3-124a-4fb4-87ce-f377b421c447" />


## Meet the agents

| Agent | Role |
|---|---|
| **Triage** | Reads your description, extracts structured constraints — goal, timeline, blocker, urgency |
| **Pathfinder** | Searches the live web, verifies real options exist, drafts your outreach |

### How it works, step by step

1. **Triage** reads your description and extracts structured constraints: goal, timeline, blocker, urgency.
2. **Triage** hands this off to **Pathfinder** over a real Fetch.ai agent-to-agent message — not a function call, a genuine inter-agent protocol exchange.
3. **Pathfinder** uses Claude with web search to generate concrete candidate options, grounded in real search results, not memorized knowledge.
4. For each candidate, **Pathfinder** opens a real **Browserbase** cloud browser session, navigates to the option's actual page, and looks for a real way to reach out (email, contact form, apply link).
5. If no real, verifiable contact method is found, **the option is dropped** — never shown as a guess. We only give you a solution that's actually solvable. This is enforced in code, not just prompted for.
6. For surviving options, Claude drafts a short, specific outreach email using **only** the verified details extracted from the real page.
7. You see a verified result and a ready-to-edit draft. Nothing is sent automatically until you review and send it yourself.

## Why this isn't a wrapper

Unlike wrappers, these two agents are **independently running agents**, built on Fetch.ai's `uagents` framework, communicating over the real Agent Chat/message protocol, not two prompts to one model dressed up as agents.

Claude's biggest strength is reasoning, so Claude performs **three distinct reasoning jobs** across the system, each scoped to a different agent and a different responsibility:

1. Constraint extraction
2. Search-strategy decisions
3. Grounded evaluation of real results

Unlike regular AI tools that sometimes hallucinate and hand you a "Plan B" that isn't actually an option, Plan B Agent puts the user first so I made one feature mandatory, not optional. That feature is

> **The anti-hallucination filter.** Any candidate without a genuine, Browserbase-verified contact method is discarded before it ever reaches the user. This is a hard rule enforced in code — `is_doable()`, `is_real_candidate()`, `sanitize_contact_method()` — not a hope baked into a prompt.

And it's a real action, not just advice: the system doesn't just suggest, it navigates a real page and produces a usable, specific draft grounded in what it actually found there.

## Tech stack

### Backend (Python)

| Tool | Role |
|---|---|
| **`uagents` (Fetch.ai)** | Multi-agent framework — Triage and Pathfinder run as a `Bureau`, communicate over real agent messaging, registered on Agentverse (`mailbox` + `publish_agent_details`) |
| **Anthropic SDK (`anthropic`, `AsyncAnthropic`)** | Claude calls powering Triage's extraction and Pathfinder's search/evaluation/drafting logic |
| **Stagehand (`AsyncStagehand`) + Browserbase** | Live cloud browser automation — real agentic web actions, not local simulation |
| **Flask + flask-cors** | REST API server bridging the agents to the frontend (`backend/app.py`) |
| **Pydantic** | Message schemas between agents (`messages.py`) |
| **python-dotenv** | Environment config loading |
| `cosmpy`, `bech32`, `ecdsa`, `pycryptodome` | Crypto/wallet dependencies pulled in by `uagents` |

### Frontend (JavaScript)

| Tool | Role |
|---|---|
| **React** | UI |
| **Vite** | Dev server / bundler |
| **ESLint** | Linting |

### Architecture flow

```
React frontend
   |
   v
POST /api/plan  (Flask)
   |
   v
Triage agent (Fetch.ai uAgent, Bureau, Agentverse-registered)
   -> Claude: constraint extraction
   |
   v   (real Fetch.ai agent-to-agent message)
Pathfinder agent (Fetch.ai uAgent)
   -> Claude: search strategy + grounded evaluation
   -> Stagehand / Browserbase: real page verification
   -> Claude: outreach drafting
   |
   v
result.json -> Flask -> React frontend
```

## Agentverse registration

Both agents are registered on Agentverse via `mailbox=True` and `publish_agent_details=True`, confirmed with a live-acquired mailbox access token.

- **Triage agent:** `agent1q2x6qgah36a43gl6xu59xc93j862n02tw5waqfw5kx8m8584jamfgqw28ht`
- **Pathfinder agent:** `agent1qv4t44yqllc74w3ykc5kwhfepnd6ff5akkq90cdr906pluwxlh57kuyxjl2`

<details>
<summary><strong>A note on Chat Protocol (click to expand)</strong></summary>
<br>

Full Agent Chat Protocol (`uagents_core.contrib.protocols.chat`) was implemented following Fetch.ai's official quickstart pattern, but the module is unavailable in any `uagents-core` version compatible with our Python 3.9 environment — confirmed via `pip index versions uagents-core`, no newer version exists.

Given hackathon time constraints, and as a solo hacker, I prioritized a fully working, verified agent pipeline over a last-minute Python version migration. Core Agentverse registration and inter-agent communication are real and fully verified; ASI:One conversational discoverability was not completed in the time available.

</details>

## Running it locally

### Prerequisites

- Python 3.9+
- Node.js
- An Anthropic API key
- A Browserbase API key + Project ID

### Setup

```bash
# clone the repo
git clone https://github.com/YOUR_USERNAME/plan-b-agent.git
cd plan-b-agent
```

```bash
# python environment
python3 -m venv venv
source venv/bin/activate
pip install -r backend/requirements.txt
```

```bash
# environment variables
cp .env.example .env
# then fill in: ANTHROPIC_API_KEY, BROWSERBASE_API_KEY, BROWSERBASE_PROJECT_ID,
# TRIAGE_SEED, PATHFINDER_SEED
```

```bash
# frontend dependencies
cd frontend
npm install
cd ..
```

### Run it (3 terminals)

```bash
# Terminal 1 — agents
cd backend
source ../venv/bin/activate
python3 run_agents.py
```

```bash
# Terminal 2 — Flask API
cd backend
source ../venv/bin/activate
python3 app.py
```

```bash
# Terminal 3 — frontend
cd frontend
npm run dev
```

Open **`http://localhost:5173`** and describe a plan that fell through.

## What's next

- [ ] Expand from 1 candidate option to 2–3
- [ ] Full ASI:One Chat Protocol support once migrated off Python 3.9
- [ ] Give Pathfinder agent the ability to take more real-world actions, not just draft
- [ ] To make the actions automatical.

---

<div align="center">

Built solo by **Lily Maung** 

A Software Engineering student at SJSU, first time hacker for UC Berkeley AI Hackathon 2026.

</div>








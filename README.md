# PlanB-Agent


<img width="1200" height="675" alt="image" src="https://github.com/user-attachments/assets/a3533026-29d9-4608-8c28-c5dee89c0661" />

As my first time hacking in AI hackathon hosted by Cal hacks, I have decided to build PlanB-Agent!

Problem

Life doesn't always go our way. What happens when your Plan A doesn't work out? 

Everybody should have their "Plan B", I know it could be overwhelming to 
think about Plan B when your Plan A fails and you are getting anxious and 
nervous. What helps is knowing what's actually still possible, backed by 
something real, with a clear first step to take. That's why Plan B Agent is 
here to guide you a new path/solution for your problem.

What it does?

Plan B is a two-agent system. You describe what fell through in plain
language. One agent figures out the real shape of the problem. The other goes
out, searches the live web, verifies a real way to act exists, and drafts a 
ready-to-edit outreach message, never showing you anything it couldn't 
confirm is real.

Workflow

Let me introduce you to our two agents called Triage and Pathfinder.

1.Triage agent reads your description and extracts structured constraints: goal, timeline, blocker, urgency.

2.Triage hands this off to Pathfinder agent over a real Fetch.ai agent-to-agent message, not a function call, a genuine inter-agent protocol exchange.

3.Pathfinder uses Claude with web search to generate concrete candidate options grounded in real search results, not memorized knowledge.

4.For each candidate, Pathfinder opens a real Browserbase cloud browser session, navigates to the option's actual page, and looks for a real way to reach out (email, contact form, apply link).

5.If no real, verifiable contact method is found, the option is dropped and never shown as a guess(We will give you solution that is solvable). This is enforced in code, not just prompted for.

6.For surviving options, Claude drafts a short, specific outreach email using only the verified details extracted from the real page.

7.You see a verified result and a ready-to-edit draft. Nothing is sent automatically until you review and send it yourself to confirm.

Unlike wrappers, these two Agents are INDEPENDENTLY running agents and built on Fetch.ai's uagents framework, communicating over the real Agent Chat/message protocol, not two prompts to one model dressed up as agents.

One of Claude's qualities is giving excellent reasoning therefore 
Claude's role is to perform three distinct reasoning jobs across the system:

1.Constraint extraction

2.Search-strategy decisions

3.Grounded evaluation of real results, each scoped to a different agent and a different responsibility.

Unlike regular AI tools or wrappers that is sometimes hallucinating and give you Plan B that is not an option or a solution, PlanB Agent prioritizes the user(the customer)in helping figure out the right possible solution. That's why I implemented one of the features as mandatory.

That one of the features is a real anti-hallucination filter, any candidate without a genuine, Browserbase-verified contact method is discarded before it ever reaches the user.

This is a hard rule enforced in code (is_doable(), is_real_candidate(), sanitize_contact_method()), not a hope baked into a prompt.

A real action, not just advice: the system doesn't just suggest, it navigates a real page and produces a usable, specific draft grounded in what it actually found there.

<img width="1000" height="700" alt="image" src="https://github.com/user-attachments/assets/5399d35b-fe53-4cf1-b8ce-425016e62904" />

Tech Stack

Fetch.ai (uagents) - both agents built with Claude reasoning, real inter-agent message protocol, registered on Agentverse (mailbox authentication)

Anthropic Claude — reasoning engine for constraint extraction, search strategy, result evaluation, and outreach drafting

Browserbase + Stagehand — live cloud browser sessions for real page navigation and contact verification

Flask — backend API bridging the agents to the frontend

React + Vite — frontend UI

Agentverse registration

Both agents are registered on Agentverse via mailbox=True and publish_agent_details=True, confirmed with a live-acquired mailbox access token.


Triage agent: agent1q2x6qgah36a43gl6xu59xc93j862n02tw5waqfw5kx8m8584jamfgqw28ht

Pathfinder agent: agent1qv4t44yqllc74w3ykc5kwhfepnd6ff5akkq90cdr906pluwxlh57kuyxjl2

Note on Chat Protocol:
Full Agent Chat Protocol (uagents_core.contrib.protocols.chat) was implemented following Fetch.ai's official quickstart pattern, but the module is unavailable in any uagents-core version compatible with our Python 3.9 environment (confirmed via pip index versions uagents-core, no newer version exists). Given hackathon time constraints and being a solo hacker, I prioritized a fully working, verified agent pipeline over a last minute Python version migration. Core Agentverse registration and inter-agent communication are real and fully verified; ASI:One conversational discoverability was not completed in the time available.

Running it locally,

Prerequisites

Python 3.9+
Node.js
An Anthropic API key
A Browserbase API key + Project ID

Setup

# clone the repo

git clone https://github.com/YOUR_USERNAME/plan-b-agent.git

cd plan-b-agent

# python environment

python3 -m venv venv

source venv/bin/activate

pip install -r backend/requirements.txt

# environment variables

cp .env.example .env

# then fill in: ANTHROPIC_API_KEY, BROWSERBASE_API_KEY, BROWSERBASE_PROJECT_ID,

# TRIAGE_SEED, PATHFINDER_SEED

# frontend dependencies

cd frontend

npm install

cd ..

Run (3 terminals)

# Terminal 1 — agents

cd backend

source ../venv/bin/activate

python3 run_agents.py

# Terminal 2 — Flask API

cd backend

source ../venv/bin/activate

python3 app.py

# Terminal 3 — frontend

cd frontend

npm run dev

Open http://localhost:5173 and describe a plan that fell through.

Built solo by Lily Maung,  a Software Engineering student at SJSU and first time hackathon participant, as part of UC Berkeley AI Hackathon 2026.

Next steps in mind after the Hackathon

Increase the coordinates from 1 to 2 or 3 

Full ASI:One Chat Protocol support once migrated off Python 3.9

Making the pathfinder agent to be able to do more actions.























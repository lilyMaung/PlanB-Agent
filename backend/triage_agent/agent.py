import os
from typing import Optional

from anthropic import AsyncAnthropic
from pydantic import BaseModel
from uagents import Agent, Context, Model

from messages import ConstraintsMessage
from pathfinder_agent.agent import agent as pathfinder_agent

TRIAGE_SEED = os.environ["TRIAGE_SEED"]

# Networking (port/endpoint) is owned by the Bureau that hosts this agent
# alongside pathfinder_agent - see run_agents.py.
#
# mailbox=True and publish_agent_details=True register this agent on
# Agentverse so it's visible/discoverable there - this satisfies Fetch.ai's
# "register your agents on Agentverse" requirement.
#
# Note: full Chat Protocol support (uagents_core.contrib.protocols.chat) was
# attempted but isn't available in the currently-installed uagents-core
# version (0.1.3 - confirmed via `pip index versions uagents-core`, no newer
# version exists with this module). Skipped for now rather than risk further
# environment debugging this close to the deadline. Agentverse registration
# itself, via mailbox + publish_agent_details, still stands on its own.
agent = Agent(
    name="triage_agent",
    seed=TRIAGE_SEED,
    mailbox=True,
    publish_agent_details=True,
)

claude = AsyncAnthropic()


class TriageRequest(Model):
    description: str


class TriageResponse(Model):
    status: str
    constraints: Optional[dict] = None
    error: Optional[str] = None


class Constraints(BaseModel):
    goal: str
    timeline: str
    blocker: str
    urgency: str


EXTRACTION_PROMPT = """A user's plan fell through and they need help figuring out a plan B. \
Read their description and extract structured constraints.

- goal: what they were trying to accomplish or experience
- timeline: when this needs to happen (specific date/time if given, otherwise their phrasing)
- blocker: what fell through or went wrong
- urgency: how time-sensitive this is, in their own terms (e.g. "tonight", "flexible", "this weekend")

User's description:
\"\"\"{description}\"\"\"
"""


@agent.on_rest_post("/triage", TriageRequest, TriageResponse)
async def handle_triage(ctx: Context, req: TriageRequest) -> TriageResponse:
    try:
        response = await claude.messages.parse(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            messages=[
                {
                    "role": "user",
                    "content": EXTRACTION_PROMPT.format(description=req.description),
                }
            ],
            output_format=Constraints,
        )
        constraints = response.parsed_output
        print(f"\n=== RAW TRIAGE OUTPUT ===\n{constraints.model_dump_json(indent=2)}\n", flush=True)
    except Exception as exc:  # noqa: BLE001
        ctx.logger.error(f"Constraint extraction failed: {exc}")
        return TriageResponse(status="error", error=str(exc))

    await ctx.send(
        pathfinder_agent.address,
        ConstraintsMessage(
            goal=constraints.goal,
            timeline=constraints.timeline,
            blocker=constraints.blocker,
            urgency=constraints.urgency,
            raw_description=req.description,
        ),
    )

    return TriageResponse(status="received", constraints=constraints.model_dump())
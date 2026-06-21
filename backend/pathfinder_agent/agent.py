import asyncio
import json
import os
import re
from typing import Optional

from anthropic import AsyncAnthropic
from stagehand import AsyncStagehand
from uagents import Agent, Context

from messages import ConstraintsMessage

PATHFINDER_SEED = os.environ["PATHFINDER_SEED"]

# Networking (port/endpoint) is owned by the Bureau that hosts this agent
# alongside triage_agent - see run_agents.py.
agent = Agent(name="pathfinder_agent", seed=PATHFINDER_SEED)

claude = AsyncAnthropic()
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
BROWSERBASE_API_KEY = os.environ["BROWSERBASE_API"].strip()
BROWSERBASE_PROJECT_ID = os.environ["BROWSERBASE_PROJECT_ID"].strip()

RESULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "result.json")

CANDIDATE_OPTIONS_SCHEMA = {
    "type": "object",
    "properties": {
        "options": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Short name for this plan B option"},
                    "description": {
                        "type": "string",
                        "description": "2-3 sentence description of the plan",
                    },
                    "why_it_works": {
                        "type": "string",
                        "description": "One sentence on why this fits their constraints",
                    },
                    "url": {
                        "type": "string",
                        "description": (
                            "A real URL from your web search results that a person could visit for "
                            "this option (the venue/program/service's actual page). Must be a URL "
                            "that actually appeared in your search results, never invented."
                        ),
                    },
                },
                "required": ["title", "description", "why_it_works", "url"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["options"],
    "additionalProperties": False,
}

GENERATION_PROMPT = """A plan fell through for someone. Propose 2 concrete, realistic alternative \
plans that fit the constraints below.

Goal: {goal}
Timeline: {timeline}
What fell through: {blocker}
Urgency: {urgency}
Their own description: "{raw_description}"

Rules:
1. Use the web_search tool before answering - do not rely on memorized knowledge.
2. Each url must be that venue's own official site, never a directory/roundup/listicle page.
3. Return exactly 2 options in "options" - never an empty list, even if no option seems perfect.
4. The 2 options must be genuinely different from each other, not variations on the same idea.

Respond with ONLY this JSON shape (no other text):
{{"options": [{{"title": "...", "description": "...", "why_it_works": "...", "url": "..."}}]}}
"""

EXTRACT_SCHEMA = {
    "type": "object",
    "properties": {
        "contact_name": {"type": "string"},
        "contact_method": {"type": "string"},
        "deadline": {"type": "string"},
    },
}

DRAFT_PROMPT = """Draft a short, specific outreach message for the situation below.

The ONLY facts you may state about the destination are the VERIFIED DETAILS listed below, extracted \
moments ago directly from their real page. Do not mention any contact name, phone number, email, \
address, or deadline other than what's given here - even if you think you know one, even if a \
more specific-sounding detail occurs to you. If a field says "(not available)", write around it \
naturally instead of guessing or filling it in.

Place: {title}

VERIFIED DETAILS (the ONLY contact specifics you are allowed to use):
- Contact name: {contact_name}
- Contact method (email / contact form / apply link): {contact_method}
- Deadline mentioned: {deadline}

The person's situation: "{raw_description}"
Their goal: {goal}

Write a short email (3-5 sentences): a greeting using the contact name if given, why they're reaching \
out (tied to their actual situation), and a clear, specific ask. Do not state any phone number, \
address, or identifying detail beyond what's explicitly given above. No subject line, no signature \
block - just the message body. Plain text only.
"""


def write_result(data: dict) -> None:
    os.makedirs(os.path.dirname(RESULT_PATH), exist_ok=True)
    with open(RESULT_PATH, "w") as f:
        json.dump(data, f, indent=2)


EMAIL_RE = re.compile(r"[^@\s]+@[^@\s]+\.[^@\s]+")
URL_RE = re.compile(r"https?://", re.IGNORECASE)


def sanitize_contact_method(value) -> str:
    """A real contact method is an email, a URL (contact form/apply link), or
    a phone number with enough digits to actually be one. Anything else -
    e.g. a truncated fragment like '0-671' - is garbled/invalid and treated
    as missing rather than trusted.
    """
    value = (value or "").strip()
    if not value:
        return ""
    if EMAIL_RE.search(value):
        return value
    if URL_RE.search(value):
        return value
    digit_count = sum(ch.isdigit() for ch in value)
    if digit_count >= 7:
        return value
    return ""


async def extract_contact_info(ctx: Context, url: str) -> dict:
    """Navigate to a candidate option's real page and try to find an actual
    way to reach out (contact name, contact method, deadline) via Stagehand's
    act()/extract(). Returns whatever was found - empty fields if nothing
    visible. Never submits/clicks-through anything beyond finding a contact
    link.
    """
    async with AsyncStagehand(
        server="remote",
        browserbase_api_key=BROWSERBASE_API_KEY,
        browserbase_project_id=BROWSERBASE_PROJECT_ID,
        model_api_key=ANTHROPIC_API_KEY,
    ) as stagehand_client:
        session = await stagehand_client.sessions.start(
            model_name="anthropic/claude-sonnet-4-6",
            browser={"type": "browserbase"},
        )
        try:
            await stagehand_client.sessions.navigate(id=session.id, url=url)
            await stagehand_client.sessions.act(
                id=session.id,
                input=(
                    "If there is a visible 'Contact', 'Apply', 'Catering', or 'Get in touch' link "
                    "or button, click it. Otherwise do nothing."
                ),
            )
            extract_response = await stagehand_client.sessions.extract(
                id=session.id,
                instruction=(
                    "Extract the program or business contact name, any visible contact method "
                    "(email address, contact form URL, or an apply link - check header, footer, "
                    "and any contact page), and any deadline mentioned on this page. Leave a field "
                    "blank if it isn't visible."
                ),
                schema=EXTRACT_SCHEMA,
            )
        finally:
            await stagehand_client.sessions.end(id=session.id)

    result = extract_response.data.result or {}
    raw_contact_method = result.get("contact_method", "")
    result["contact_method"] = sanitize_contact_method(raw_contact_method)
    if raw_contact_method and not result["contact_method"]:
        ctx.logger.info(f"Discarding garbled contact_method: {raw_contact_method!r}")
    return result


def is_doable(extracted: dict) -> bool:
    """An option only counts as actionable if we found a real way to reach
    out - a contact name alone isn't enough to act on.
    """
    return bool(extracted.get("contact_method", "").strip())


async def validate_candidate(ctx: Context, option: dict, msg: ConstraintsMessage) -> Optional[dict]:
    """Check whether a candidate option is actually doable (has a real, found
    contact method), and if so draft outreach for it. Returns None if the
    option doesn't survive validation.
    """
    try:
        extracted = await extract_contact_info(ctx, option["url"])
    except Exception as exc:  # noqa: BLE001
        ctx.logger.error(f"Validation failed for {option['url']}: {exc}")
        return None

    ctx.logger.info(f"Extracted from {option['url']}: {extracted}")

    if not is_doable(extracted):
        ctx.logger.info(f"Dropping non-doable option: {option['title']}")
        return None

    draft_response = await claude.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        messages=[
            {
                "role": "user",
                "content": DRAFT_PROMPT.format(
                    title=option["title"],
                    contact_name=extracted.get("contact_name") or "(not available)",
                    contact_method=extracted.get("contact_method") or "(not available)",
                    deadline=extracted.get("deadline") or "(not available)",
                    raw_description=msg.raw_description,
                    goal=msg.goal,
                ),
            }
        ],
    )
    draft_text = next((b.text for b in draft_response.content if b.type == "text"), "")
    print(f"\n=== RAW DRAFT OUTPUT ({option['title']}) ===\n{draft_text}\n", flush=True)

    return {
        **option,
        "outreach": {
            "label": "Ready-to-edit draft - review before sending. Nothing has been sent.",
            "extracted": extracted,
            "email_draft": draft_text.strip(),
        },
    }


GRACEFUL_NO_OPTION_MESSAGE = (
    "We're having trouble finding a specific, verified option right now - try rephrasing your "
    "situation with a bit more detail (location, timing, or what you need)."
)

PLACEHOLDER_VALUES = {"placeholder", "...", "tbd", "todo", "n/a", "example", "example.com"}


def is_real_candidate(option: dict) -> bool:
    """Reject candidates where Claude echoed the JSON schema's own example
    values (e.g. title/url literally "placeholder") instead of doing real
    work - a parsed JSON object isn't the same as a real answer.
    """
    for field in ("title", "description", "why_it_works", "url"):
        value = (option.get(field) or "").strip().lower()
        if not value or value in PLACEHOLDER_VALUES:
            return False
    url = option.get("url", "").strip().lower()
    if not (url.startswith("http://") or url.startswith("https://")):
        return False
    if "placeholder" in url or "example.com" in url:
        return False
    return True


async def generate_candidates(ctx: Context, msg: ConstraintsMessage) -> list:
    """One attempt at generating candidates: search, handle any pause_turn
    continuations, and parse the result. Returns a list (possibly empty) -
    callers decide how to handle an empty result.
    """
    prompt = GENERATION_PROMPT.format(
        goal=msg.goal,
        timeline=msg.timeline,
        blocker=msg.blocker,
        urgency=msg.urgency,
        raw_description=msg.raw_description,
    )
    MAX_CONTINUATIONS = 6
    messages = [{"role": "user", "content": prompt}]

    response = await claude.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=12000,
        tools=[{"type": "web_search_20260209", "name": "web_search"}],
        output_config={"format": {"type": "json_schema", "schema": CANDIDATE_OPTIONS_SCHEMA}},
        messages=messages,
    )
    continuations = 0
    while response.stop_reason == "pause_turn" and continuations < MAX_CONTINUATIONS:
        continuations += 1
        ctx.logger.info(f"Generation paused (pause_turn) - continuing, attempt {continuations}")
        messages = messages + [{"role": "assistant", "content": response.content}]
        response = await claude.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=12000,
            tools=[{"type": "web_search_20260209", "name": "web_search"}],
            container=response.container.id if response.container else None,
            output_config={"format": {"type": "json_schema", "schema": CANDIDATE_OPTIONS_SCHEMA}},
            messages=messages,
        )

    text = next((b.text for b in response.content if b.type == "text"), None)
    search_queries = [
        b.input.get("query") for b in response.content
        if b.type == "server_tool_use" and b.name == "web_search" and isinstance(b.input, dict)
    ]
    search_calls = len(search_queries)
    print(
        f"\n=== RAW PATHFINDER GENERATION OUTPUT "
        f"(search calls: {search_calls}, stop_reason: {response.stop_reason}, "
        f"continuations used: {continuations}) ===\n"
        f"SEARCH QUERIES: {search_queries}\n{text}\n",
        flush=True,
    )
    result = json.loads(text) if text else {"options": []}
    return result.get("options", [])


@agent.on_message(model=ConstraintsMessage)
async def handle_constraints(ctx: Context, sender: str, msg: ConstraintsMessage) -> None:
    try:
        await asyncio.wait_for(_handle_constraints_inner(ctx, msg), timeout=240)
    except asyncio.TimeoutError:
        ctx.logger.error("handle_constraints timed out after 240s")
        write_result({
            "status": "error",
            "error": "This is taking longer than expected, likely due to high API load. Please try again.",
        })


async def _handle_constraints_inner(ctx: Context, msg: ConstraintsMessage) -> None:
    ctx.logger.info(f"Generating plan candidates for: {msg.goal}")

    MAX_GENERATION_ATTEMPTS = 2
    candidates = []
    for attempt in range(1, MAX_GENERATION_ATTEMPTS + 1):
        try:
            raw_candidates = await generate_candidates(ctx, msg)
            candidates = [c for c in raw_candidates if is_real_candidate(c)]
            if raw_candidates and not candidates:
                ctx.logger.info(f"Attempt {attempt} returned placeholder/junk values: {raw_candidates}")
        except Exception as exc:  # noqa: BLE001
            ctx.logger.error(f"Plan generation failed (attempt {attempt}): {exc}")
            candidates = []

        if candidates:
            break
        ctx.logger.info(f"Generation attempt {attempt} returned no usable candidates.")

    if not candidates:
        write_result({"status": "error", "error": GRACEFUL_NO_OPTION_MESSAGE})
        return

    ctx.logger.info(f"Validating {len(candidates)} candidates for real contact info...")
    validated = await asyncio.gather(
        *(validate_candidate(ctx, c, msg) for c in candidates), return_exceptions=True
    )
    options = [v for v in validated if isinstance(v, dict)]

    if not options:
        write_result({"status": "error", "error": GRACEFUL_NO_OPTION_MESSAGE})
        return

    write_result({"status": "done", "options": options})
from uagents import Model


class ConstraintsMessage(Model):
    goal: str
    timeline: str
    blocker: str
    urgency: str
    raw_description: str

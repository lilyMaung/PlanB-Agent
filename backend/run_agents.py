import os

from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

from uagents import Bureau  # noqa: E402


from triage_agent.agent import agent as triage_agent  # noqa: E402
from pathfinder_agent.agent import agent as pathfinder_agent  # noqa: E402

BUREAU_PORT = int(os.environ.get("BUREAU_PORT", 8000))

bureau = Bureau(port=BUREAU_PORT, endpoint=f"http://127.0.0.1:{BUREAU_PORT}/submit")
bureau.add(triage_agent)
bureau.add(pathfinder_agent)

if __name__ == "__main__":
    print(f"triage_agent address:     {triage_agent.address}")
    print(f"pathfinder_agent address: {pathfinder_agent.address}")
    print(f"REST endpoint:            http://127.0.0.1:{BUREAU_PORT}/triage")
    bureau.run()

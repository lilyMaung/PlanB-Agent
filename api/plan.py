import json
import os

# Your pre-saved real result — paste your demo_result.json content here directly
DEMO_RESULT = {
    "status": "done",
    "options": [
        {
            "title": "Join the Meeting Virtually via Zoom",
            "description": "Contact your meeting organizer immediately to explain your situation and request to attend remotely via Zoom. Most business meetings can be adapted to a hybrid or fully virtual format on short notice, letting you participate in real time from wherever you are without needing to travel at all.",
            "why_it_works": "A virtual meeting eliminates travel entirely, making it the fastest and most reliable solution when transportation falls through unexpectedly.",
            "url": "https://zoom.us/meetings",
            "outreach": {
                "label": "Ready-to-edit draft - review before sending. Nothing has been sent.",
                "extracted": {
                    "contact_name": "Zoom Sales",
                    "contact_method": "https://zoom.us/contactsales",
                    "deadline": ""
                },
                "email_draft": "Hi Zoom Sales,\n\nMy flight to Chicago has been cancelled and I have an important meeting there that I cannot miss. I'd like to explore joining the meeting virtually via Zoom so I can still participate without being physically present. Could you help me get set up quickly, referencing case number 15-24641, so I can attend remotely without disruption?\n\nThank you"
            }
        }
    ]
}

def handler(request):
    if request.method == "POST":
        # User submitted a scenario - return processing status
        # (result is already "ready" - status endpoint will return it)
        return {
            "status": 200,
            "body": json.dumps({"status": "processing"}),
            "headers": {"Content-Type": "application/json"}
        }
    return {
        "status": 405,
        "body": json.dumps({"error": "Method not allowed"}),
        "headers": {"Content-Type": "application/json"}
    }
import os
import requests


TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": message
        },
        timeout=30
    )

    response.raise_for_status()


message = """🌊 OCG Opportunity Radar

TEST SUCCESSFUL ✅

Your Telegram connection is working.

Next, we will build the opportunity-search engine.

It will look for:
• Oceanography
• GIS / Remote Sensing
• Climate & Environment
• Research
• Internships
• Competitions
• Hackathons
• Scholarships
• Fellowships
• Summer/Winter Schools
• Remote opportunities

Status: Connected successfully.
"""

send_telegram(message)

print("Telegram message sent successfully!")• GIS opportunities
• Oceanography opportunities
• Climate opportunities
• Remote opportunities

Status: Telegram connection test successful ✅
"""

send_telegram(message)

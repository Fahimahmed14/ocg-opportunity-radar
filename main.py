import os
import requests

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = "6289716583"

if not TOKEN:
    print("ERROR: TELEGRAM_BOT_TOKEN is missing from GitHub Secrets.")
    raise SystemExit(1)

print("Telegram token found.")
print("Chat ID:", CHAT_ID)

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

message = """🌊 OCG Opportunity Radar

TEST SUCCESSFUL ✅

Your Telegram bot is connected.

Next step:
AI Opportunity Finder 🚀

It will search for:
• Oceanography
• GIS / Remote Sensing
• Climate
• Environment
• Research
• Internships
• Competitions
• Hackathons
• Scholarships
• Fellowships
• Summer/Winter Schools
• Remote opportunities
"""

try:
    response = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": message
        },
        timeout=30
    )

    print("Telegram API status:", response.status_code)
    print("Telegram API response:", response.text)

    response.raise_for_status()

    print("SUCCESS: Telegram message sent!")

except Exception as e:
    print("ERROR:", str(e))
    raise

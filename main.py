import os
import requests

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = "6289716583"

url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

message = """🌊 OCG Opportunity Radar

TEST SUCCESSFUL ✅

Telegram connection is working!

Next, we will build the AI opportunity finder for:
• Oceanography
• GIS & Remote Sensing
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

response = requests.post(
    url,
    data={
        "chat_id": CHAT_ID,
        "text": message
    },
    timeout=30
)

response.raise_for_status()

print("Telegram message sent successfully!")• Internships
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

import os
import json
import requests

from sources import collect_opportunities


TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
CHAT_ID = "6289716583"


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


with open("profile.json", "r", encoding="utf-8") as file:
    profile = json.load(file)


print("Starting opportunity search...")

opportunities = collect_opportunities()

print(f"Collected {len(opportunities)} results.")


message = f"""🌊 OCG OPPORTUNITY RADAR

🔎 Search completed

Potential results found: {len(opportunities)}

Your profile:
🎓 {profile["education"]["degree"]}
🌍 {profile["education"]["country"]}

Main interests:
• Oceanography
• GIS
• Remote Sensing
• Climate
• Environment
• Research
• Data Science

🤖 AI filtering will be added next.
"""


send_telegram(message)

print("Telegram report sent!")

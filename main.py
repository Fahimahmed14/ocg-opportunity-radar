import os
import requests


TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"

    response = requests.post(
        url,
        data={
            "chat_id": os.environ["TELEGRAM_CHAT_ID"],
            "text": message
        },
        timeout=30
    )

    response.raise_for_status()


message = """🌊 OCG Opportunity Radar

Bot successfully connected!

Your daily opportunity radar is being built.

It will eventually search for:
• Internships
• Research opportunities
• Competitions
• Hackathons
• Scholarships
• Fellowships
• Summer/Winter schools
• GIS opportunities
• Oceanography opportunities
• Climate opportunities
• Remote opportunities

Status: Telegram connection test successful ✅
"""

send_telegram(message)

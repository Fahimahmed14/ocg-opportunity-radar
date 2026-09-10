import os
import json
import requests

from sources import collect_opportunities
from ai_filter import rank_opportunity


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


print("Searching for opportunities...")

opportunities = collect_opportunities()

print(f"Found {len(opportunities)} candidate results.")


ranked = []

for opportunity in opportunities[:20]:

    try:
        result = rank_opportunity(opportunity, profile)

        opportunity["score"] = result["score"]
        opportunity["category"] = result["category"]
        opportunity["eligibility"] = result["eligibility"]
        opportunity["reason"] = result["reason"]
        opportunity["priority"] = result["priority"]

        ranked.append(opportunity)

        print(
            opportunity["score"],
            opportunity["title"]
        )

    except Exception as error:
        print("AI filtering failed:", error)


ranked.sort(
    key=lambda x: x.get("score", 0),
    reverse=True
)


top = ranked[:5]


message = "🌊 OCG OPPORTUNITY RADAR\n\n"

if not top:
    message += "No suitable opportunities found today."
else:

    message += "🔥 TOP OPPORTUNITIES\n\n"

    for i, opportunity in enumerate(top, 1):

        message += (
            f"{i}. {opportunity['title'][:100]}\n"
            f"⭐ Match: {opportunity['score']}/100\n"
            f"📂 {opportunity['category']}\n"
            f"🎯 {opportunity['priority']}\n"
            f"📝 {opportunity['reason'][:200]}\n"
            f"🔗 {opportunity['url']}\n\n"
        )


send_telegram(message)

print("AI opportunity report sent!")

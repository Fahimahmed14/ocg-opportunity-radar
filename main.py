import os
import json
import requests

from sources import collect_opportunities

from ai_filter import (
    rank_opportunities,
    apply_rankings
)


TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

CHAT_ID = "6289716583"


def send_telegram(message):

    url = (
        f"https://api.telegram.org/"
        f"bot{TOKEN}/sendMessage"
    )

    response = requests.post(
        url,

        data={
            "chat_id": CHAT_ID,
            "text": message
        },

        timeout=30
    )

    response.raise_for_status()


def split_message(
    message,
    max_length=4000
):

    if len(message) <= max_length:
        return [message]

    parts = []

    current = ""

    for line in message.split("\n"):

        if (
            len(current)
            + len(line)
            + 1
            > max_length
        ):

            if current:
                parts.append(current)

            current = line

        else:

            current += "\n" + line

    if current:
        parts.append(current)

    return parts


def build_report(
    results,
    profile
):

    top_results = [
        result
        for result in results
        if result.get(
            "score",
            0
        ) >= 60
    ]

    top_results = top_results[:10]

    message = (
        "🌊 OCG OPPORTUNITY RADAR\n\n"
        "🔥 TOP OPPORTUNITIES\n\n"
    )

    if not top_results:

        message += (
            "No strong opportunities "
            "found today.\n\n"

            "The radar searched multiple "
            "opportunity categories and "
            "filtered the results using AI.\n\n"

            "Try again tomorrow."
        )

        return message

    for number, opportunity in enumerate(
        top_results,
        start=1
    ):

        title = opportunity.get(
            "title",
            "Untitled opportunity"
        )

        score = opportunity.get(
            "score",
            0
        )

        category = opportunity.get(
            "category",
            "Other"
        )

        priority = opportunity.get(
            "priority",
            "LOW"
        )

        eligibility = opportunity.get(
            "eligibility",
            "Unknown"
        )

        reason = opportunity.get(
            "reason",
            "No explanation provided."
        )

        url = opportunity.get(
            "url",
            ""
        )

        message += (
            f"{number}. {title}\n"
            f"⭐ Match: {score}/100\n"
            f"📂 {category}\n"
            f"🎯 {priority}\n"
            f"👤 {eligibility}\n"
            f"📝 {reason}\n"
            f"🔗 {url}\n\n"
        )

    message += (
        "──────────────────\n"

        f"🔎 Candidates collected: "
        f"{len(results)}\n"

        f"🔥 Strong matches: "
        f"{len(top_results)}\n\n"

        "🎓 Profile: "
        f"{profile['education']['degree']}\n"

        "🌍 Bangladesh"
    )

    return message


def main():

    print("=" * 60)
    print(
        "🌊 OCG OPPORTUNITY RADAR"
    )
    print("=" * 60)

    # ------------------------------------------
    # LOAD PROFILE
    # ------------------------------------------

    with open(
        "profile.json",
        "r",
        encoding="utf-8"
    ) as file:

        profile = json.load(file)

    print(
        "\n1. Profile loaded."
    )

    # ------------------------------------------
    # COLLECT OPPORTUNITIES
    # ------------------------------------------

    print(
        "\n2. Collecting opportunities..."
    )

    opportunities = (
        collect_opportunities()
    )

    print(
        f"\nCollected "
        f"{len(opportunities)} "
        "clean candidates."
    )

    if not opportunities:

        message = (
            "🌊 OCG OPPORTUNITY RADAR\n\n"

            "⚠️ No candidates were "
            "collected today.\n\n"

            "The search collector may have "
            "encountered a temporary "
            "search-engine problem."
        )

        send_telegram(
            message
        )

        return

    # ------------------------------------------
    # LIMIT AI CANDIDATES
    # ------------------------------------------

    ai_candidates = (
        opportunities[:40]
    )

    print(
        f"Sending "
        f"{len(ai_candidates)} "
        "candidates to OpenRouter AI..."
    )

    # ------------------------------------------
    # AI RANKING
    # ------------------------------------------

    all_rankings = []

    batch_size = 20

    for start in range(
        0,
        len(ai_candidates),
        batch_size
    ):

        batch = ai_candidates[
            start:start + batch_size
        ]

        batch_number = (
            start // batch_size + 1
        )

        print(
            f"AI batch "
            f"{batch_number}: "
            f"{len(batch)} opportunities"
        )

        try:

            rankings = (
                rank_opportunities(
                    batch,
                    profile
                )
            )

            # Convert local indexes
            # to global indexes

            for ranking in rankings:

                try:

                    local_index = int(
                        ranking.get(
                            "index",
                            0
                        )
                    )

                except (
                    ValueError,
                    TypeError
                ):

                    continue

                if local_index < 1:
                    continue

                if (
                    local_index
                    > len(batch)
                ):
                    continue

                global_index = (
                    start
                    + local_index
                )

                ranking["index"] = (
                    global_index
                )

                all_rankings.append(
                    ranking
                )

        except Exception as error:

            print(
                f"AI batch failed: "
                f"{error}"
            )

    print(
        f"\nAI returned "
        f"{len(all_rankings)} "
        "rankings."
    )

    # ------------------------------------------
    # APPLY AI RANKINGS
    # ------------------------------------------

    ranked_results = (
        apply_rankings(
            ai_candidates,
            all_rankings
        )
    )

    strong_results = [
        result
        for result in ranked_results
        if result.get(
            "score",
            0
        ) >= 60
    ]

    print(
        f"Strong opportunities: "
        f"{len(strong_results)}"
    )

    # ------------------------------------------
    # BUILD REPORT
    # ------------------------------------------

    report = build_report(
        ranked_results,
        profile
    )

    # ------------------------------------------
    # SEND TELEGRAM
    # ------------------------------------------

    print(
        "\nSending Telegram report..."
    )

    messages = split_message(
        report
    )

    for message in messages:

        send_telegram(
            message
        )

    print(
        f"Telegram report sent "
        f"({len(messages)} message(s))."
    )

    print(
        "\n✅ RADAR COMPLETED"
    )


if __name__ == "__main__":
    main()

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

            if current:
                current += "\n"

            current += line

    if current:
        parts.append(current)

    return parts


def build_report(
    results,
    profile
):

    # --------------------------------------------------------
    # Keep anything with an AI score
    # --------------------------------------------------------

    results = sorted(
        results,
        key=lambda x: x.get(
            "score",
            0
        ),
        reverse=True
    )

    top_results = results[:10]

    message = (
        "🌊 OCG OPPORTUNITY RADAR\n\n"
        "🔥 TOP OPPORTUNITIES\n\n"
    )

    if not top_results:

        message += (
            "No opportunities reached the "
            "AI ranking stage.\n\n"
            "The collector may have returned "
            "zero usable candidates."
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
        f"🔎 AI-ranked candidates: "
        f"{len(results)}\n\n"
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

    # --------------------------------------------------------
    # LOAD PROFILE
    # --------------------------------------------------------

    with open(
        "profile.json",
        "r",
        encoding="utf-8"
    ) as file:

        profile = json.load(file)

    print(
        "\n1. Profile loaded."
    )

    # --------------------------------------------------------
    # COLLECT
    # --------------------------------------------------------

    print(
        "\n2. Collecting opportunities..."
    )

    opportunities = (
        collect_opportunities()
    )

    print(
        "\n=============================================="
    )

    print(
        f"COLLECTOR RESULT: "
        f"{len(opportunities)} candidates"
    )

    print(
        "=============================================="
    )

    # --------------------------------------------------------
    # IMPORTANT DEBUG
    # --------------------------------------------------------

    if opportunities:

        print(
            "\nFIRST COLLECTED CANDIDATES:"
        )

        for index, opportunity in enumerate(
            opportunities[:10],
            start=1
        ):

            print(
                f"\n{index}. "
                f"{opportunity.get('title', '')}"
            )

            print(
                f"   URL: "
                f"{opportunity.get('url', '')}"
            )

            print(
                f"   Source: "
                f"{opportunity.get('source', '')}"
            )

    # --------------------------------------------------------
    # NO CANDIDATES
    # --------------------------------------------------------

    if not opportunities:

        message = (
            "🌊 OCG OPPORTUNITY RADAR\n\n"
            "⚠️ COLLECTOR RETURNED 0 CANDIDATES\n\n"
            "The opportunity websites/search "
            "sources returned no usable results.\n\n"
            "AI filtering was NOT run."
        )

        send_telegram(
            message
        )

        return

    # --------------------------------------------------------
    # LIMIT AI CANDIDATES
    # --------------------------------------------------------

    ai_candidates = opportunities[:40]

    print(
        f"\n3. Sending "
        f"{len(ai_candidates)} "
        "candidates to OpenRouter AI..."
    )

    # --------------------------------------------------------
    # AI RANKING
    # --------------------------------------------------------

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
            f"\nAI batch "
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

            print(
                f"AI returned "
                f"{len(rankings)} rankings."
            )

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

    # --------------------------------------------------------
    # APPLY AI RANKINGS
    # --------------------------------------------------------

    print(
        f"\n4. Total AI rankings: "
        f"{len(all_rankings)}"
    )

    ranked_results = (
        apply_rankings(
            ai_candidates,
            all_rankings
        )
    )

    print(
        f"5. Final ranked results: "
        f"{len(ranked_results)}"
    )

    # --------------------------------------------------------
    # PRINT SCORES
    # --------------------------------------------------------

    print(
        "\nAI SCORES:"
    )

    for result in ranked_results[:20]:

        print(
            f"{result.get('score', 0)}/100 - "
            f"{result.get('title', '')}"
        )

    # --------------------------------------------------------
    # REPORT
    # --------------------------------------------------------

    report = build_report(
        ranked_results,
        profile
    )

    print(
        "\n6. Sending Telegram report..."
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

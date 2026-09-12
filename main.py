import os
import json
import requests

from sources import collect_opportunities

from ai_filter import (
    rank_opportunities,
    apply_rankings
)


# ============================================================
# CONFIGURATION
# ============================================================

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

CHAT_ID = "6289716583"

MIN_SCORE = 70


# ============================================================
# TELEGRAM
# ============================================================

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


# ============================================================
# SPLIT TELEGRAM MESSAGE
# ============================================================

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

                parts.append(
                    current
                )

            current = line

        else:

            if current:

                current += "\n"

            current += line

    if current:

        parts.append(
            current
        )

    return parts


# ============================================================
# FINAL QUALITY FILTER
# ============================================================

def final_filter(
    results
):

    accepted = []

    rejected = []

    for opportunity in results:

        score = opportunity.get(
            "score",
            0
        )

        try:

            score = int(
                float(score)
            )

        except (
            ValueError,
            TypeError
        ):

            score = 0

        status = str(
            opportunity.get(
                "application_status",
                "Unknown"
            )
        ).strip().lower()

        eligibility = str(
            opportunity.get(
                "eligibility",
                ""
            )
        ).strip().lower()

        # ----------------------------------------------------
        # Reject low scores
        # ----------------------------------------------------

        if score < MIN_SCORE:

            rejected.append(
                (
                    opportunity,
                    f"score below {MIN_SCORE}"
                )
            )

            continue

        # ----------------------------------------------------
        # Reject closed opportunities
        # ----------------------------------------------------

        if status == "closed":

            rejected.append(
                (
                    opportunity,
                    "application closed"
                )
            )

            continue

        # ----------------------------------------------------
        # Reject clearly ineligible opportunities
        # ----------------------------------------------------

        if (
            "not eligible"
            in eligibility
        ):

            rejected.append(
                (
                    opportunity,
                    "student not eligible"
                )
            )

            continue

        # ----------------------------------------------------
        # Accept
        # ----------------------------------------------------

        accepted.append(
            opportunity
        )

    accepted.sort(
        key=lambda x: x.get(
            "score",
            0
        ),
        reverse=True
    )

    return accepted, rejected


# ============================================================
# BUILD TELEGRAM REPORT
# ============================================================

def build_report(
    results,
    profile
):

    message = (
        "🌊 OCG OPPORTUNITY RADAR\n\n"
        "🔥 TOP CURRENT OPPORTUNITIES\n\n"
    )

    if not results:

        message += (
            "No strong current opportunities "
            "were found today.\n\n"
            f"Minimum AI match score: "
            f"{MIN_SCORE}/100\n\n"
            "The radar automatically removed "
            "low-match, closed and clearly "
            "ineligible opportunities."
        )

        return message

    for number, opportunity in enumerate(
        results[:10],
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
            "Eligibility unclear"
        )

        reason = opportunity.get(
            "reason",
            "No explanation provided."
        )

        deadline = opportunity.get(
            "deadline",
            "Unknown"
        )

        funding = opportunity.get(
            "funding",
            "Unknown"
        )

        location = opportunity.get(
            "location",
            "Unknown"
        )

        status = opportunity.get(
            "application_status",
            "Unknown"
        )

        url = opportunity.get(
            "url",
            ""
        )

        application_link = opportunity.get(
            "application_link",
            ""
        )

        # ----------------------------------------------------
        # Prefer actual application link
        # ----------------------------------------------------

        final_link = (
            application_link
            if application_link
            else url
        )

        message += (
            f"{number}. {title}\n"
            f"⭐ Match: {score}/100\n"
            f"📂 {category}\n"
            f"🎯 {priority}\n"
            f"📅 Deadline: {deadline}\n"
            f"💰 Funding: {funding}\n"
            f"🌍 Location: {location}\n"
            f"📌 Status: {status}\n"
            f"👤 Eligibility: {eligibility}\n"
            f"📝 {reason}\n"
            f"🔗 {final_link}\n\n"
        )

    message += (
        "──────────────────\n"
        f"✅ Strong matches: "
        f"{len(results)}\n"
        f"🎯 Minimum score: "
        f"{MIN_SCORE}/100\n\n"
        "🎓 Profile: "
        f"{profile['education']['degree']}\n"
        "🌍 Bangladesh"
    )

    return message


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "=" * 60
    )

    print(
        "🌊 OCG OPPORTUNITY RADAR"
    )

    print(
        "=" * 60
    )

    # --------------------------------------------------------
    # LOAD PROFILE
    # --------------------------------------------------------

    with open(
        "profile.json",
        "r",
        encoding="utf-8"
    ) as file:

        profile = json.load(
            file
        )

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
    # NO CANDIDATES
    # --------------------------------------------------------

    if not opportunities:

        message = (
            "🌊 OCG OPPORTUNITY RADAR\n\n"
            "⚠️ NO CANDIDATES FOUND\n\n"
            "The collector did not find "
            "usable opportunity pages today.\n\n"
            "AI filtering was not run."
        )

        send_telegram(
            message
        )

        return

    # --------------------------------------------------------
    # LIMIT AI INPUT
    # --------------------------------------------------------

    ai_candidates = opportunities[:20]

    print(
        f"\n3. Sending "
        f"{len(ai_candidates)} "
        "candidates to OpenRouter..."
    )

    # --------------------------------------------------------
    # AI RANKING
    # --------------------------------------------------------

    all_rankings = []

    # Smaller batches reduce the chance of the AI mixing up
    # or copy-pasting details between different opportunities.
    batch_size = 10

    for start in range(
        0,
        len(ai_candidates),
        batch_size
    ):

        batch = ai_candidates[
            start:start + batch_size
        ]

        batch_number = (
            start // batch_size
            + 1
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

                if (
                    local_index < 1
                    or local_index > len(batch)
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
    # APPLY RANKINGS
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
        f"5. AI-ranked results: "
        f"{len(ranked_results)}"
    )

    # --------------------------------------------------------
    # SHOW ALL AI SCORES
    # --------------------------------------------------------

    print(
        "\nAI SCORES:"
    )

    for result in ranked_results:

        print(
            f"{result.get('score', 0)}/100 | "
            f"{result.get('application_status', 'Unknown')} | "
            f"{result.get('title', '')}"
        )

    # --------------------------------------------------------
    # FINAL QUALITY FILTER
    # --------------------------------------------------------

    print(
        "\n6. Applying final quality filter..."
    )

    accepted, rejected = (
        final_filter(
            ranked_results
        )
    )

    print(
        f"Accepted: "
        f"{len(accepted)}"
    )

    print(
        f"Rejected: "
        f"{len(rejected)}"
    )

    # --------------------------------------------------------
    # SHOW REJECTED
    # --------------------------------------------------------

    if rejected:

        print(
            "\nREJECTED:"
        )

        for opportunity, reason in rejected:

            print(
                f"- "
                f"{opportunity.get('score', 0)}/100 "
                f"{opportunity.get('title', '')} "
                f"({reason})"
            )

    # --------------------------------------------------------
    # SHOW ACCEPTED
    # --------------------------------------------------------

    if accepted:

        print(
            "\nACCEPTED:"
        )

        for opportunity in accepted:

            print(
                f"- "
                f"{opportunity.get('score', 0)}/100 "
                f"{opportunity.get('title', '')}"
            )

    # --------------------------------------------------------
    # BUILD REPORT
    # --------------------------------------------------------

    report = build_report(
        accepted,
        profile
    )

    # --------------------------------------------------------
    # SEND TELEGRAM
    # --------------------------------------------------------

    print(
        "\n7. Sending Telegram report..."
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


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    main()

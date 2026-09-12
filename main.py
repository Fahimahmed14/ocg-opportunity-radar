import os
import json
import re
import requests
from datetime import datetime, timezone

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
# DEADLINE PARSING
# ============================================================
# The AI is asked to reject expired opportunities, but free
# models are unreliable at date arithmetic - they've scored
# opportunities with deadlines weeks in the past as 90/100
# "Open". This is a code-level safety net that doesn't rely
# on the AI getting today's date right: it actually parsesxcept (
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

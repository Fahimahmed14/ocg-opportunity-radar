import os
import json
import requests
import re


# ============================================================
# OPENROUTER CONFIGURATION
# ============================================================

API_KEY = os.environ["OPENROUTER_API_KEY"]

API_URL = "https://openrouter.ai/api/v1/chat/completions"

# --------------------------------------------------------
# MODEL SELECTION
# --------------------------------------------------------
# "openrouter/free" is an auto-router: it can silently hand
# your request to a very weak model, which is why outputs
# were duplicating fields across unrelated opportunities.
#
# Instead we pin to specific named free models and try them
# in order, falling back to the next one if a call fails.
#
# IMPORTANT: OpenRouter's free lineup rotates - models here
# WILL eventually 404 like the previous list did. If a run's
# log shows every candidate failing with 404 ("unavailable
# for free"), refresh this list from the live collection:
# https://openrouter.ai/collections/free-models
# (copy the exact slug shown there, including the ":free" suffix)
#
# "openrouter/free" is kept as the final fallback so the
# pipeline still gets SOME response even if every nameds only
- Canadian citizens only

If eligibility is unavailable:

"Eligibility unclear"

Never invent eligibility.

==================================================
FIELD RELEVANCE
==================================================

Highest priority:

1. Oceanography
2. Ocean science
3. Marine science
4. Marine biology
5. Coastal science
6. Physical oceanography
7. Ocean modelling
8. Marine research
9. Fisheries science
10. GIS
11. Remote sensing
12. Earth observation
13. Climate science
14. Environmental science
15. Disaster risk reduction
16. Data science
17. Scientific programming

Also consider:

- Earth science
- Atmospheric science
- Hydrology
- Geospatial science
- Sustainability
- Conservation
- Environmental data
- Scientific computing

==================================================
ACTUAL OPPORTUNITY
==================================================

The page should represent something a student can
actually apply for, participate in, attend, or use.

Reject:

- General news
- Opinion articles
- Blog posts with no active opportunity
- University homepages
- Organization homepages
- Product pages
- Search-result pages
- Google pages
- Social media pages
- Login pages
- Privacy pages
- Contact pages
- Generic career pages
- Historical announcements
- Expired programs

A news article is valid ONLY when it clearly describes
a CURRENT opportunity.

==================================================
MATCH SCORE
==================================================

90-100:
Excellent match.

80-89:
Very strong match.

70-79:
Strong match.

60-69:
Possible useful match.

40-59:
Weak match.

20-39:
Very weak.

0-19:
Reject.

Expired, historical, clearly ineligible or unrelated
opportunities should normally score below 20.

==================================================
PRIORITY
==================================================

HIGH:
80-100

MEDIUM:
60-79

LOW:
Below 60

==================================================
CATEGORY
==================================================

Use the most appropriate category:

Internship
Research Internship
Research Assistant
Scholarship
Fellowship
Summer School
Winter School
Competition
Hackathon
Training
Workshop
Externship
Youth Program
Student Program
Research Program
Conference
Other

==================================================
FUNDING
==================================================

Look for:

- Fully funded
- Stipend
- Travel support
- Accommodation
- Tuition waiver
- Scholarship
- Paid
- Unpaid

If unavailable:

"Unknown"

Never invent funding.

==================================================
LOCATION
==================================================

Extract only if clearly stated.

Examples:

Bangladesh
USA
Germany
Europe
Remote
Global
Hybrid

If unknown:

"Unknown"

==================================================
APPLICATION STATUS
==================================================

Use one of:

Open
Upcoming
Closed
Unknown

==================================================
REASON
==================================================

Give a short explanation of why the opportunity matches
the student's background.

==================================================
RETURN FORMAT
==================================================

Return ONLY valid JSON.

Return a JSON array.

Every opportunity must have an item.

Use this structure:

[
  {{
    "index": 1,
    "score": 91,
    "category": "Research Internship",
    "eligibility": "Likely eligible",
    "priority": "HIGH",
    "reason": "Strong oceanography research match for an undergraduate student.",
    "deadline": "15 October 2026",
    "funding": "Unknown",
    "location": "USA",
    "application_status": "Open"
  }}
]

Do not use markdown.
Do not write explanations outside JSON.

==================================================
OPPORTUNITIES TO EVALUATE
==================================================

{opportunity_text}
"""

    return prompt


# ============================================================
# EXTRACT OPENROUTER CONTENT
# ============================================================

def extract_openrouter_content(data):

    if not isinstance(data, dict):
        raise ValueError(
            "OpenRouter returned an invalid JSON object."
        )

    choices = data.get("choices")

    if not choices:
        error_info = data.get("error")

        if error_info:
            raise ValueError(
                f"OpenRouter API error: {error_info}"
            )

        raise ValueError(
            "OpenRouter returned no choices."
        )

    choice = choices[0]

    if not isinstance(choice, dict):
        raise ValueError(
            "OpenRouter returned an invalid choice."
        )

    message = choice.get("message", {})

    if not isinstance(message, dict):
        message = {}

    # --------------------------------------------------------
    # Normal response
    # --------------------------------------------------------

    content = message.get("content")

    if content:

        if isinstance(content, str):
            return content

        if isinstance(content, list):

            parts = []

            for item in content:

                if isinstance(item, str):
                    parts.append(item)

                elif isinstance(item, dict):

                    if item.get("text"):
                        parts.append(
                            str(item["text"])
                        )

                    elif item.get("content"):
                        parts.append(
                            str(item["content"])
                        )

            combined = "\n".join(parts).strip()

            if combined:
                return combined

    # --------------------------------------------------------
    # Some reasoning models may place useful output
    # in a reasoning field.
    # --------------------------------------------------------

    reasoning = message.get("reasoning")

    if reasoning:

        if isinstance(reasoning, str):
            return reasoning

        if isinstance(reasoning, list):

            parts = []

            for item in reasoning:

                if isinstance(item, str):
                    parts.append(item)

                elif isinstance(item, dict):

                    if item.get("text"):
                        parts.append(
                            str(item["text"])
                        )

            combined = "\n".join(parts).strip()

            if combined:
                return combined

    # --------------------------------------------------------
    # Safe debugging information.
    # Do NOT print the API key.
    # --------------------------------------------------------

    print(
        "OpenRouter returned no usable message content."
    )

    print(
        "Choice keys:",
        list(choice.keys())
    )

    print(
        "Message keys:",
        list(message.keys())
    )

    print(
        "Finish reason:",
        choice.get("finish_reason")
    )

    print(
        "Response ID:",
        data.get("id", "Unknown")
    )

    raise ValueError(
        "AI returned an empty response."
    )


# ============================================================
# CALL A SINGLE MODEL
# ============================================================
# Makes one request to one specific model. Raises on any
# failure (HTTP error, bad JSON envelope, empty content).
# Does NOT try other models - that happens one level up in
# get_rankings_for_batch, where we can also detect a model
# that returned 200 OK but garbage/unparsable content.
# ============================================================

def call_single_model(model_name, prompt):

    headers = {

        "Authorization":
            f"Bearer {API_KEY}",

        "Content-Type":
            "application/json",

        "HTTP-Referer":
            (
                "https://github.com/"
                "Fahimahmed14/"
                "ocg-opportunity-radar"
            ),

        "X-Title":
            "OCG Opportunity Radar"

    }

    payload = {

        "model":
            model_name,

        "messages": [

            {
                "role": "system",
                "content":
                    (
                        "You are a strict opportunity "
                        "verification and ranking system. "
                        "Return valid JSON only. Do not "
                        "include any text, explanation or "
                        "markdown before or after the JSON "
                        "array. "
                        "Never invent eligibility, "
                        "deadlines, funding or facts. "
                        "Each opportunity is independent: "
                        "never reuse the funding, location, "
                        "deadline or reason text from one "
                        "opportunity for a different one."
                    )
            },

            {
                "role": "user",
                "content":
                    prompt
            }

        ],

        "temperature": 0.1,

        "max_tokens": 7000

    }

    response = requests.post(
        API_URL,
        headers=headers,
        json=payload,
        timeout=120
    )

    if not response.ok:

        try:
            error_data = response.json()

        except Exception:
            error_data = response.text[:500]

        raise ValueError(
            f"OpenRouter HTTP {response.status_code} "
            f"({model_name}): {error_data}"
        )

    try:

        data = response.json()

    except ValueError:

        raise ValueError(
            f"OpenRouter did not return valid JSON "
            f"({model_name})."
        )

    return extract_openrouter_content(
        data
    )


# ============================================================
# GET RANKINGS FOR A BATCH
# ============================================================
# Tries each candidate model in turn. A model only "counts"
# as successful if its response actually parses into at
# least one usable ranking - a 200 OK response containing
# garbage/prose (like the "Could not find valid JSON" case)
# is treated the same as a failure and we move on to the
# next model, instead of losing the whole batch.
# ============================================================

def get_rankings_for_batch(batch, profile):

    prompt = build_prompt(
        batch,
        profile
    )

    last_error = None

    for model_name in MODEL_CANDIDATES:

        try:

            print(
                f"Trying model: {model_name}"
            )

            content = call_single_model(
                model_name,
                prompt
            )

            print(
                "AI response length:",
                len(content)
            )

            rankings = extract_json(
                content
            )

            if isinstance(rankings, dict):
                rankings = [rankings]

            if not isinstance(rankings, list):

                raise ValueError(
                    "AI response was not a JSON list."
                )

            clean_rankings = []

            for ranking in rankings:

                ranking = normalize_ranking(
                    ranking
                )

                if ranking is None:
                    continue

                if (
                    ranking["index"] < 1
                    or ranking["index"] > len(batch)
                ):
                    continue

                clean_rankings.append(
                    ranking
                )

            if not clean_rankings:

                raise ValueError(
                    "Model returned no usable rankings."
                )

            print(
                f"Used model: {model_name} "
                f"({len(clean_rankings)} valid rankings)"
            )

            return clean_rankings

        except Exception as error:

            last_error = error

            print(
                f"Model {model_name} failed: {error}"
            )

            continue

    print(
        f"All candidate models failed for this batch. "
        f"Last error: {last_error}"
    )

    return []


# ============================================================
# RANK OPPORTUNITIES
# ============================================================

def rank_opportunities(
    opportunities,
    profile
):

    if not opportunities:
        return []

    # Maximum 20 opportunities per request
    batch = opportunities[:20]

    print(
        "Sending opportunities to OpenRouter..."
    )

    clean_rankings = get_rankings_for_batch(
        batch,
        profile
    )

    print(
        "Valid AI rankings:",
        len(clean_rankings)
    )

    # --------------------------------------------------------
    # RETRY: if the AI silently dropped some opportunities
    # (returned fewer rankings than we sent), re-send just
    # the missing ones once, as their own small batch - again
    # trying all candidate models for that retry.
    # --------------------------------------------------------

    covered_indices = {
        ranking["index"]
        for ranking in clean_rankings
    }

    missing_indices = [
        i for i in range(1, len(batch) + 1)
        if i not in covered_indices
    ]

    if missing_indices:

        print(
            f"Retrying {len(missing_indices)} "
            f"dropped opportunity(ies): "
            f"{missing_indices}"
        )

        missing_batch = [
            batch[i - 1]
            for i in missing_indices
        ]

        retry_rankings = get_rankings_for_batch(
            missing_batch,
            profile
        )

        for ranking in retry_rankings:

            local_index = ranking["index"]

            # Map the retry batch's local index back to
            # the original batch's index.
            ranking["index"] = missing_indices[
                local_index - 1
            ]

            clean_rankings.append(
                ranking
            )

        print(
            "Valid AI rankings after retry:",
            len(clean_rankings)
        )

    return clean_rankings


# ============================================================
# CROSS-CHECK: does the AI's reason actually match this
# opportunity, or was it copy-pasted from a different one?
# ============================================================

def reason_matches_opportunity(reason, opportunity):

    title = str(
        opportunity.get("title", "")
    ).lower()

    snippet = str(
        opportunity.get("snippet", "")
    ).lower()

    reason_lower = str(reason).lower()

    title_words = {
        word for word in title.split()
        if len(word) > 4
    }

    # No meaningful title words to check against -
    # don't block it, there's nothing to compare.
    if not title_words:
        return True

    reason_words = set(
        reason_lower.split()
    )

    # Accept if the reason shares at least one
    # meaningful word with the title, OR if a
    # meaningful title word appears in the snippet
    # (loose match - titles are often abbreviated).
    if title_words & reason_words:
        return True

    if any(
        word in snippet
        for word in title_words
    ):
        return True

    return False


# ============================================================
# APPLY AI RANKINGS
# ============================================================

def apply_rankings(
    opportunities,
    rankings
):

    final_results = []

    skipped_mismatches = 0

    for ranking in rankings:

        try:

            index = int(
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
            index < 1
            or index > len(opportunities)
        ):

            continue

        opportunity = (
            opportunities[
                index - 1
            ].copy()
        )

        # ----------------------------------------------------
        # Cross-check: reject rankings whose reason text
        # doesn't relate to this opportunity's own title.
        # This is what catches the AI copy-pasting details
        # from one opportunity onto another.
        # ----------------------------------------------------

        reason_text = ranking.get(
            "reason",
            ""
        )

        if not reason_matches_opportunity(
            reason_text,
            opportunity
        ):

            skipped_mismatches += 1

            print(
                f"Skipped mismatched ranking for: "
                f"{opportunity.get('title', '')} "
                f"(reason looked copy-pasted from "
                f"another opportunity)"
            )

            continue

        # ----------------------------------------------------
        # AI score
        # ----------------------------------------------------

        opportunity["score"] = normalize_score(
            ranking.get(
                "score",
                0
            )
        )

        # ----------------------------------------------------
        # AI fields
        # ----------------------------------------------------

        opportunity["category"] = (
            ranking.get(
                "category",
                "Other"
            )
        )

        opportunity["eligibility"] = (
            ranking.get(
                "eligibility",
                "Eligibility unclear"
            )
        )

        opportunity["priority"] = (
            ranking.get(
                "priority",
                "LOW"
            )
        )

        opportunity["reason"] = (
            ranking.get(
                "reason",
                "No explanation provided."
            )
        )

        opportunity["deadline"] = (
            ranking.get(
                "deadline",
                "Unknown"
            )
        )

        opportunity["funding"] = (
            ranking.get(
                "funding",
                "Unknown"
            )
        )

        opportunity["location"] = (
            ranking.get(
                "location",
                "Unknown"
            )
        )

        opportunity["application_status"] = (
            ranking.get(
                "application_status",
                "Unknown"
            )
        )

        final_results.append(
            opportunity
        )

    # --------------------------------------------------------
    # Sort highest match first
    # --------------------------------------------------------

    final_results.sort(
        key=lambda x: x.get(
            "score",
            0
        ),
        reverse=True
    )

    if skipped_mismatches:

        print(
            f"Skipped {skipped_mismatches} ranking(s) "
            f"due to copy-pasted/mismatched reason text."
        )

    return final_results

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
# Free models on OpenRouter rotate over time, so if all of
# these start failing, check https://openrouter.ai/models?max_price=0
# and update this list.
# --------------------------------------------------------

MODEL_CANDIDATES = [
    "deepseek/deepseek-chat-v3.1:free",
    "qwen/qwen3-235b-a22b:free",
    "meta-llama/llama-3.3-70b-instruct:free",
]


# ============================================================
# JSON EXTRACTION
# ============================================================

def extract_json(text):
    """
    Extract a JSON array or object from an AI response.
    """

    if text is None:
        raise ValueError("AI returned no usable text.")

    # Handle non-string content
    if isinstance(text, list):

        parts = []

        for item in text:

            if isinstance(item, str):
                parts.append(item)

            elif isinstance(item, dict):

                if "text" in item:
                    parts.append(str(item["text"]))

                elif "content" in item:
                    parts.append(str(item["content"]))

        text = "\n".join(parts)

    if not text:
        raise ValueError("AI returned an empty response.")

    text = str(text).strip()

    if not text:
        raise ValueError("AI returned an empty response.")

    # --------------------------------------------------------
    # Remove markdown code fences
    # --------------------------------------------------------

    text = re.sub(
        r"^```(?:json)?\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    text = text.strip()

    # --------------------------------------------------------
    # Direct JSON
    # --------------------------------------------------------

    try:
        return json.loads(text)

    except json.JSONDecodeError:
        pass

    # --------------------------------------------------------
    # Find JSON array
    # --------------------------------------------------------

    start = text.find("[")
    end = text.rfind("]")

    if (
        start != -1
        and end != -1
        and end > start
    ):

        candidate = text[start:end + 1]

        try:
            return json.loads(candidate)

        except json.JSONDecodeError:
            pass

    # --------------------------------------------------------
    # Find JSON object
    # --------------------------------------------------------

    start = text.find("{")
    end = text.rfind("}")

    if (
        start != -1
        and end != -1
        and end > start
    ):

        candidate = text[start:end + 1]

        try:
            return json.loads(candidate)

        except json.JSONDecodeError:
            pass

    raise ValueError(
        "Could not find valid JSON in AI response."
    )


# ============================================================
# NORMALIZE SCORE
# ============================================================

def normalize_score(value):

    try:

        score = int(float(value))

    except (
        ValueError,
        TypeError
    ):

        return 0

    return max(
        0,
        min(
            100,
            score
        )
    )


# ============================================================
# NORMALIZE RANKING
# ============================================================

def normalize_ranking(ranking):

    if not isinstance(ranking, dict):
        return None

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

        return None

    if index < 1:
        return None

    ranking["index"] = index

    ranking["score"] = normalize_score(
        ranking.get(
            "score",
            0
        )
    )

    ranking["category"] = (
        str(
            ranking.get(
                "category",
                "Other"
            )
        ).strip()
        or "Other"
    )

    ranking["eligibility"] = (
        str(
            ranking.get(
                "eligibility",
                "Eligibility unclear"
            )
        ).strip()
        or "Eligibility unclear"
    )

    ranking["priority"] = (
        str(
            ranking.get(
                "priority",
                "LOW"
            )
        ).upper()
    )

    if ranking["priority"] not in {
        "HIGH",
        "MEDIUM",
        "LOW"
    }:

        ranking["priority"] = "LOW"

    ranking["reason"] = (
        str(
            ranking.get(
                "reason",
                "No explanation provided."
            )
        ).strip()
        or "No explanation provided."
    )

    ranking["deadline"] = (
        str(
            ranking.get(
                "deadline",
                "Unknown"
            )
        ).strip()
        or "Unknown"
    )

    ranking["funding"] = (
        str(
            ranking.get(
                "funding",
                "Unknown"
            )
        ).strip()
        or "Unknown"
    )

    ranking["location"] = (
        str(
            ranking.get(
                "location",
                "Unknown"
            )
        ).strip()
        or "Unknown"
    )

    ranking["application_status"] = (
        str(
            ranking.get(
                "application_status",
                "Unknown"
            )
        ).strip()
        or "Unknown"
    )

    return ranking


# ============================================================
# BUILD AI PROMPT
# ============================================================

def build_prompt(opportunities, profile):

    opportunity_text = ""

    for index, opportunity in enumerate(
        opportunities,
        start=1
    ):

        opportunity_text += f"""

==================================================
OPPORTUNITY {index}
==================================================

TITLE:
{opportunity.get("title", "")}

URL:
{opportunity.get("url", "")}

SOURCE:
{opportunity.get("source", "")}

PUBLISHED:
{opportunity.get("published", "Unknown")}

DESCRIPTION:
{opportunity.get("snippet", "")}

==================================================
"""

    prompt = f"""
You are the strict opportunity-verification and
ranking AI for OCG Opportunity Radar.

CURRENT YEAR: 2026

Your job is to identify REAL, CURRENT and USEFUL
opportunities for the student described below.

==================================================
STUDENT PROFILE
==================================================

{json.dumps(profile, indent=2)}

==================================================
STUDENT CONTEXT
==================================================

The student is:

- An undergraduate B.Sc. (Hons) Oceanography student
- Based in Bangladesh
- Interested in oceanography and marine science
- Interested in GIS and remote sensing
- Interested in ocean modelling
- Interested in climate change
- Interested in environmental science
- Interested in disaster risk reduction
- Interested in data science
- Interested in Python, R and MATLAB
- Interested in scientific research

Important skills include:

- ArcGIS
- GIS
- Remote sensing
- Spatial analysis
- Python
- R
- MATLAB
- Ocean Data View
- Data analysis
- Scientific research

==================================================
VALID OPPORTUNITY TYPES
==================================================

Valid opportunities include:

- Internship
- Research internship
- Research assistantship
- Undergraduate research
- Research experience
- Scholarship
- Fellowship
- Studentship
- Summer school
- Winter school
- Summer research program
- Training
- Workshop
- Competition
- Hackathon
- Challenge
- Externship
- Youth program
- Student program
- Student research program
- Academic program
- Conference
- Scientific program

==================================================
CURRENTNESS
==================================================

The current year is 2026.

Reject clearly expired or historical opportunities.

Prefer:

- 2026 opportunities
- 2027 opportunities
- currently open applications
- future deadlines
- active recurring programs

An article about an old opportunity is NOT a current
opportunity.

If a deadline has clearly passed, score below 20.

Never invent dates.

==================================================
ELIGIBILITY
==================================================

The student is an undergraduate student from Bangladesh.

Strong eligibility signals include:

- Undergraduate students
- International students
- Students worldwide
- Open to all nationalities
- Students from Bangladesh
- Remote participation
- International applicants

Potentially NOT eligible:

- US citizens only
- US nationals only
- Permanent residents only
- EU citizens only
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
# CALL OPENROUTER
# ============================================================

def call_openrouter(prompt):

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

    last_error = None

    # ----------------------------------------------------
    # Try each candidate model in order until one works.
    # ----------------------------------------------------

    for model_name in MODEL_CANDIDATES:

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
                            "Return valid JSON only. "
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

        try:

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

                last_error = (
                    f"OpenRouter HTTP "
                    f"{response.status_code} "
                    f"({model_name}): {error_data}"
                )

                print(
                    f"Model {model_name} failed: "
                    f"{last_error}"
                )

                continue

            try:

                data = response.json()

            except ValueError:

                last_error = (
                    f"OpenRouter did not return valid "
                    f"JSON ({model_name})."
                )

                print(last_error)

                continue

            content = extract_openrouter_content(
                data
            )

            print(
                f"Used model: {model_name}"
            )

            return content

        except Exception as error:

            last_error = (
                f"Request failed for {model_name}: "
                f"{error}"
            )

            print(last_error)

            continue

    raise ValueError(
        f"All candidate models failed. "
        f"Last error: {last_error}"
    )


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

    prompt = build_prompt(
        batch,
        profile
    )

    print(
        "Sending opportunities to OpenRouter..."
    )

    content = call_openrouter(
        prompt
    )

    print(
        "OpenRouter response received."
    )

    # Helpful debug information without exposing
    # the actual response or API key.
    print(
        "AI response length:",
        len(content)
    )

    rankings = extract_json(
        content
    )

    # --------------------------------------------------------
    # AI should return a list
    # --------------------------------------------------------

    if isinstance(
        rankings,
        dict
    ):

        rankings = [
            rankings
        ]

    if not isinstance(
        rankings,
        list
    ):

        raise ValueError(
            "AI response was not a JSON list."
        )

    # --------------------------------------------------------
    # Normalize rankings
    # --------------------------------------------------------

    clean_rankings = []

    for ranking in rankings:

        ranking = normalize_ranking(
            ranking
        )

        if ranking is None:
            continue

        # Local batch index validation
        if (
            ranking["index"] < 1
            or ranking["index"] > len(batch)
        ):
            continue

        clean_rankings.append(
            ranking
        )

    print(
        "Valid AI rankings:",
        len(clean_rankings)
    )

    # --------------------------------------------------------
    # RETRY: if the AI silently dropped some opportunities
    # (returned fewer rankings than we sent), re-send just
    # the missing ones once, as their own small batch.
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

        try:

            retry_prompt = build_prompt(
                missing_batch,
                profile
            )

            retry_content = call_openrouter(
                retry_prompt
            )

            retry_rankings = extract_json(
                retry_content
            )

            if isinstance(retry_rankings, dict):
                retry_rankings = [retry_rankings]

            if isinstance(retry_rankings, list):

                for ranking in retry_rankings:

                    ranking = normalize_ranking(
                        ranking
                    )

                    if ranking is None:
                        continue

                    local_index = ranking["index"]

                    if (
                        local_index < 1
                        or local_index > len(missing_batch)
                    ):
                        continue

                    # Map the retry batch's local index
                    # back to the original batch's index.
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

        except Exception as error:

            print(
                f"Retry for dropped opportunities "
                f"failed: {error}"
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

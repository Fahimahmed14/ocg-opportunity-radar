import os
import json
import requests
import re


# ============================================================
# OPENROUTER CONFIGURATION
# ============================================================

API_KEY = os.environ["OPENROUTER_API_KEY"]

API_URL = "https://openrouter.ai/api/v1/chat/completions"

MODEL = "openrouter/free"


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

    payload = {

        "model":
            MODEL,

        "messages": [

            {
                "role": "system",
                "content":
                    (
                        "You are a strict opportunity "
                        "verification and ranking system. "
                        "Return valid JSON only. "
                        "Never invent eligibility, "
                        "deadlines, funding or facts."
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

    # --------------------------------------------------------
    # HTTP error handling
    # --------------------------------------------------------

    if not response.ok:

        try:
            error_data = response.json()

        except Exception:
            error_data = response.text[:500]

        raise ValueError(
            f"OpenRouter HTTP {response.status_code}: "
            f"{error_data}"
        )

    # --------------------------------------------------------
    # Parse JSON response
    # --------------------------------------------------------

    try:

        data = response.json()

    except ValueError:

        raise ValueError(
            "OpenRouter did not return valid JSON."
        )

    # --------------------------------------------------------
    # Extract model response safely
    # --------------------------------------------------------

    return extract_openrouter_content(
        data
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

    return clean_rankings


# ============================================================
# APPLY AI RANKINGS
# ============================================================

def apply_rankings(
    opportunities,
    rankings
):

    final_results = []

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

    return final_results

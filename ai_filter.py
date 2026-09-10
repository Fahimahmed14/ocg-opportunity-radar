import os
import json
import requests
import re


# ============================================================
# OPENROUTER CONFIGURATION
# ============================================================

API_KEY = os.environ["OPENROUTER_API_KEY"]

API_URL = (
    "https://openrouter.ai/api/v1/chat/completions"
)

MODEL = "openrouter/free"


# ============================================================
# JSON EXTRACTION
# ============================================================

def extract_json(text):
    """
    Extract a JSON array or object from an AI response.
    """

    if not text:
        raise ValueError(
            "AI returned an empty response."
        )

    text = text.strip()

    # --------------------------------------------------------
    # Remove markdown code fences
    # --------------------------------------------------------

    text = re.sub(
        r"^```(?:json)?",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"```$",
        "",
        text
    )

    text = text.strip()

    # --------------------------------------------------------
    # Try complete JSON directly
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

        candidate = text[
            start:end + 1
        ]

        try:

            return json.loads(
                candidate
            )

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

        candidate = text[
            start:end + 1
        ]

        try:

            return json.loads(
                candidate
            )

        except json.JSONDecodeError:

            pass

    raise ValueError(
        "Could not find valid JSON "
        "in AI response."
    )


# ============================================================
# NORMALIZE SCORE
# ============================================================

def normalize_score(value):

    try:

        score = int(
            float(value)
        )

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

def normalize_ranking(
    ranking
):

    if not isinstance(
        ranking,
        dict
    ):

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

    ranking["score"] = (
        normalize_score(
            ranking.get(
                "score",
                0
            )
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

    # --------------------------------------------------------
    # Optional useful fields
    # --------------------------------------------------------

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

def build_prompt(
    opportunities,
    profile
):

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
VERY IMPORTANT: CURRENTNESS
==================================================

The current year is 2026.

You MUST distinguish between:

1. A CURRENT opportunity
2. An article discussing an opportunity
3. An OLD opportunity
4. An expired opportunity

An article about an opportunity is NOT automatically
a current opportunity.

For example:

"Applications Now Open for 2019 Scholarship"

must be rejected.

If the opportunity clearly belongs to:

2019
2020
2021
2022
2023
2024
2025

then it should normally receive a score below 20.

Do NOT recommend clearly expired opportunities.

Prefer:

- 2026 opportunities
- 2027 opportunities
- currently open applications
- future deadlines
- recurring programs whose 2026/2027 cycle is open
- programs with no deadline but clearly active/current information

If the page does not provide enough information to
determine whether an opportunity is current, do not
invent a date.

==================================================
DEADLINE RULE
==================================================

Look for:

- Application deadline
- Deadline
- Applications close
- Apply by
- Closing date
- Submission deadline

If a deadline has clearly passed:

score should normally be below 20.

If the deadline is unknown:

write:

"Unknown"

Never invent a deadline.

==================================================
ELIGIBILITY RULE
==================================================

The student is an undergraduate student from Bangladesh.

Strong eligibility signals include:

- Undergraduate students
- International students
- Students worldwide
- Students from developing countries
- Students from Bangladesh
- Open to all nationalities
- Remote participation
- International applicants

Potentially eligible:

"Students from all countries"

Potentially eligible:

"International students"

Potentially eligible:

"Undergraduate students"

Potentially eligible:

"Open globally"

Potentially NOT eligible:

"US citizens only"

"US nationals only"

"Permanent residents only"

"EU citizens only"

"Canadian citizens only"

If eligibility is not available, write:

"Eligibility unclear"

Do NOT invent eligibility.

==================================================
FIELD RELEVANCE
==================================================

Highest priority should be given to:

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

Also consider related fields such as:

- Earth science
- Atmospheric science
- Hydrology
- Geospatial science
- Sustainability
- Conservation
- Environmental data
- Scientific computing

==================================================
ACTUAL OPPORTUNITY RULE
==================================================

The page should represent something a student can
actually apply for, participate in, attend, or use.

Reject:

- General news
- News articles with no active opportunity
- Opinion articles
- Blog posts
- University homepages
- Organization homepages
- Company homepages
- Product pages
- Search-result pages
- Google pages
- Social media pages
- Login pages
- Privacy pages
- Contact pages
- Generic career pages with no specific program
- General information with no opportunity
- Historical announcements
- Expired programs

==================================================
NEWS ARTICLE RULE
==================================================

A news article can only be recommended if the article
clearly describes a CURRENT opportunity.

For example:

"University announces 2026 ocean research internship
applications"

may be valid.

But:

"Students participated in 2022 ocean internship"

is NOT valid.

==================================================
MATCH SCORE
==================================================

Score from 0 to 100.

90-100:
Excellent match.

The opportunity is current, undergraduate-friendly,
strongly related to oceanography/GIS/climate/environment/
research/data science, and the student is likely eligible.

80-89:
Very strong match.

Strong subject relevance and likely eligibility.

70-79:
Strong match.

Useful and reasonably relevant.

60-69:
Possible useful match.

Relevant but some uncertainty exists.

40-59:
Weak match.

Some relevance but important eligibility,
currentness, location or field uncertainty.

20-39:
Very weak.

Only limited relevance or significant uncertainty.

0-19:
Reject.

Examples:

- Expired opportunity
- Old opportunity
- Clearly ineligible
- General article
- No actual opportunity
- Completely unrelated

==================================================
PRIORITY
==================================================

HIGH:

Score 80-100

MEDIUM:

Score 60-79

LOW:

Score below 60

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

Extract the location if clearly stated.

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

Do not call something Open unless the information
supports it.

==================================================
REASON
==================================================

Give a short reason explaining:

- Why it matches the student's background
- Important subject relevance
- Important eligibility issue if any

Keep it concise.

Example:

"Strong oceanography research match and suitable for
undergraduate students, but international eligibility
needs verification."

==================================================
RETURN FORMAT
==================================================

Return ONLY valid JSON.

Return a JSON array.

Every opportunity MUST have an item.

Use this exact structure:

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
# CALL OPENROUTER
# ============================================================

def call_openrouter(
    prompt
):

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

        "temperature":
            0.1,

        "max_tokens":
            7000

    }

    response = requests.post(
        API_URL,
        headers=headers,
        json=payload,
        timeout=120
    )

    response.raise_for_status()

    data = response.json()

    try:

        content = (
            data["choices"][0]
            ["message"]
            ["content"]
        )

    except (
        KeyError,
        IndexError,
        TypeError
    ) as error:

        raise ValueError(
            f"Unexpected OpenRouter response: "
            f"{error}"
        )

    return content


# ============================================================
# RANK OPPORTUNITIES
# ============================================================

def rank_opportunities(
    opportunities,
    profile
):

    if not opportunities:

        return []

    # --------------------------------------------------------
    # Maximum 20 opportunities per request
    # --------------------------------------------------------

    batch = opportunities[:20]

    prompt = build_prompt(
        batch,
        profile
    )

    print(
        "Sending opportunities to "
        "OpenRouter..."
    )

    content = call_openrouter(
        prompt
    )

    print(
        "OpenRouter response received."
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

        score = normalize_score(
            ranking.get(
                "score",
                0
            )
        )

        opportunity["score"] = score

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

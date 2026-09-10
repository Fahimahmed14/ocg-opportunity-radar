import os
import json
import requests
import re


API_KEY = os.environ["OPENROUTER_API_KEY"]

API_URL = (
    "https://openrouter.ai/api/v1/chat/completions"
)

MODEL = "openrouter/free"


def extract_json(text):
    """
    Extract JSON from an AI response.
    """

    text = text.strip()

    # Remove markdown code fences
    if text.startswith("```"):

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

    # Find JSON array
    start = text.find("[")
    end = text.rfind("]")

    if start != -1 and end != -1:

        return json.loads(
            text[start:end + 1]
        )

    # Find JSON object
    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1:

        return json.loads(
            text[start:end + 1]
        )

    raise ValueError(
        "Could not find valid JSON "
        "in AI response"
    )


def rank_opportunities(
    opportunities,
    profile
):
    """
    Send a batch of opportunities
    to OpenRouter and receive rankings.
    """

    if not opportunities:
        return []

    # Maximum 20 per AI request
    batch = opportunities[:20]

    opportunity_text = ""

    for index, opportunity in enumerate(
        batch,
        start=1
    ):

        opportunity_text += f"""

OPPORTUNITY {index}

Title:
{opportunity.get("title", "")}

URL:
{opportunity.get("url", "")}

Source:
{opportunity.get("source", "")}

Description/Snippet:
{opportunity.get("snippet", "")}

--------------------------------
"""

    prompt = f"""
You are the opportunity-ranking AI for
OCG Opportunity Radar.

You are helping a Bangladesh-based
undergraduate B.Sc. (Hons) Oceanography
student find REAL and USEFUL opportunities.

STUDENT PROFILE:

{json.dumps(profile, indent=2)}


ONLY RECOMMEND GENUINE OPPORTUNITIES.

An opportunity should be something a student
can actually apply for, join, participate in,
attend, or benefit from.

Examples:

- Internship
- Research internship
- Research assistantship
- Scholarship
- Fellowship
- Competition
- Hackathon
- Summer school
- Winter school
- Training
- Workshop
- Externship
- Student program
- Youth program
- Conference
- Research program


REJECT:

- Google search pages
- Search feedback pages
- Login pages
- Generic articles
- News articles with no opportunity
- General university homepages
- Company homepages with no program
- Random blogs
- Product pages
- Social media profiles
- Irrelevant jobs
- Pages with no actual opportunity
- Pages unrelated to the student's profile


HIGH PRIORITY FIELDS:

Oceanography
Marine Science
Ocean Science
GIS
Remote Sensing
Ocean Modelling
Climate Change
Environmental Science
Disaster Risk Reduction
Data Science
Python
R
MATLAB
Scientific Research


ELIGIBILITY:

The student is an undergraduate student
from Bangladesh.

Prefer opportunities that:

- accept undergraduate students
- accept international students
- accept students from Bangladesh
- are remote
- are available in Asia
- are globally accessible


SCORING:

90-100 = Excellent match
80-89 = Very strong match
70-79 = Strong match
60-69 = Useful possible match
40-59 = Weak match
0-39 = Reject


IMPORTANT:

If something is clearly NOT an opportunity,
give it a score below 30.

Do not invent eligibility information.

If eligibility is unclear, write:

"Eligibility unclear"


RETURN ONLY VALID JSON.

Return a JSON array.

Each item must contain:

{{
    "index": 1,
    "score": 0,
    "category": "Internship",
    "eligibility": "Likely eligible",
    "priority": "HIGH",
    "reason": "Short explanation"
}}


OPPORTUNITIES:

{opportunity_text}
"""

    headers = {
        "Authorization": (
            f"Bearer {API_KEY}"
        ),
        "Content-Type": "application/json",

        "HTTP-Referer": (
            "https://github.com/"
            "Fahimahmed14/"
            "ocg-opportunity-radar"
        ),

        "X-Title": (
            "OCG Opportunity Radar"
        )
    }

    payload = {

        "model": MODEL,

        "messages": [

            {
                "role": "system",
                "content": (
                    "You are a strict opportunity "
                    "matching system. "
                    "Return valid JSON only."
                )
            },

            {
                "role": "user",
                "content": prompt
            }
        ],

        "temperature": 0.1,

        "max_tokens": 5000
    }

    response = requests.post(
        API_URL,
        headers=headers,
        json=payload,
        timeout=90
    )

    response.raise_for_status()

    data = response.json()

    content = (
        data["choices"][0]
        ["message"]
        ["content"]
    )

    rankings = extract_json(
        content
    )

    return rankings


def apply_rankings(
    opportunities,
    rankings
):
    """
    Combine AI rankings with
    original opportunities.
    """

    final_results = []

    for ranking in rankings:

        try:

            index = int(
                ranking.get(
                    "index",
                    0
                )
            )

            score = int(
                ranking.get(
                    "score",
                    0
                )
            )

        except (
            ValueError,
            TypeError
        ):

            continue

        if index < 1:
            continue

        if index > len(opportunities):
            continue

        opportunity = (
            opportunities[index - 1].copy()
        )

        opportunity["score"] = max(
            0,
            min(100, score)
        )

        opportunity["category"] = (
            ranking.get(
                "category",
                "Other"
            )
        )

        opportunity["eligibility"] = (
            ranking.get(
                "eligibility",
                "Unknown"
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

        final_results.append(
            opportunity
        )

    final_results.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return final_results

import os
import json
import requests


API_KEY = os.environ["OPENROUTER_API_KEY"]

API_URL = "https://openrouter.ai/api/v1/chat/completions"


def rank_opportunity(opportunity, profile):

    prompt = f"""
You are an AI opportunity-matching assistant.

Your job is to decide how useful an opportunity is for this student.

STUDENT PROFILE:
{json.dumps(profile, indent=2)}

OPPORTUNITY:
Title: {opportunity.get("title", "")}
Source: {opportunity.get("source", "")}
URL: {opportunity.get("url", "")}

Evaluate:

1. Is the opportunity relevant to the student's field?
2. Can an undergraduate student apply?
3. Is it suitable for a student from Bangladesh?
4. Does it match Oceanography, Marine Science, GIS,
   Remote Sensing, Climate, Environment, Research,
   Data Science, Python, R or MATLAB?
5. Is it an internship, research opportunity,
   competition, scholarship, fellowship, school,
   training or similar useful opportunity?

Give a match score from 0 to 100.

Scoring:
90-100 = Excellent match
75-89 = Strong match
60-74 = Possible match
40-59 = Weak match
0-39 = Not relevant

Return ONLY valid JSON.

Required format:

{{
    "score": 0,
    "category": "Internship",
    "eligibility": "Likely eligible",
    "reason": "Short explanation",
    "priority": "HIGH"
}}
"""

    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/Fahimahmed14/ocg-opportunity-radar",
        "X-Title": "OCG Opportunity Radar"
    }

    data = {
        "model": "openrouter/free",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "temperature": 0.2
    }

    response = requests.post(
        API_URL,
        headers=headers,
        json=data,
        timeout=60
    )

    response.raise_for_status()

    result = response.json()

    text = result["choices"][0]["message"]["content"].strip()

    # Remove markdown JSON fences if the model adds them
    if text.startswith("```"):
        text = text.replace("```json", "")
        text = text.replace("```", "")
        text = text.strip()

    return json.loads(text)

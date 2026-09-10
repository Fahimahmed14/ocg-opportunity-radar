import requests
from bs4 import BeautifulSoup


SOURCES = [
    {
        "name": "Google Search - Oceanography",
        "url": "https://www.google.com/search?q=oceanography+internship+students"
    },
    {
        "name": "Google Search - GIS",
        "url": "https://www.google.com/search?q=GIS+internship+students"
    },
    {
        "name": "Google Search - Climate",
        "url": "https://www.google.com/search?q=climate+change+internship+students"
    },
    {
        "name": "Google Search - Marine Science",
        "url": "https://www.google.com/search?q=marine+science+student+opportunities"
    },
    {
        "name": "Google Search - Scholarships",
        "url": "https://www.google.com/search?q=scholarship+undergraduate+international+students"
    },
    {
        "name": "Google Search - Fellowships",
        "url": "https://www.google.com/search?q=fellowship+undergraduate+international+students"
    },
    {
        "name": "Google Search - Competitions",
        "url": "https://www.google.com/search?q=environment+competition+students+2026"
    }
]


def search_source(source):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    response = requests.get(
        source["url"],
        headers=headers,
        timeout=20
    )

    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    results = []

    for link in soup.select("a"):
        title = link.get_text(" ", strip=True)
        href = link.get("href")

        if title and href and href.startswith("http"):
            results.append({
                "source": source["name"],
                "title": title,
                "url": href
            })

    return results


def collect_opportunities():
    all_results = []

    for source in SOURCES:
        try:
            results = search_source(source)
            all_results.extend(results)
        except Exception as error:
            print(f"Source failed: {source['name']}")
            print(error)

    return all_results

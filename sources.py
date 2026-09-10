import requests
from bs4 import BeautifulSoup
from urllib.parse import quote, urlparse, parse_qs, unquote
import re


SEARCH_QUERIES = [
    "oceanography internship undergraduate students",
    "marine science internship undergraduate",
    "ocean science research internship students",
    "marine biology internship undergraduate",
    "GIS internship undergraduate students",
    "remote sensing internship students",
    "GIS remote sensing summer school students",
    "climate change internship undergraduate",
    "climate research internship students",
    "environmental science internship undergraduate",
    "environment research internship students",
    "oceanography scholarship undergraduate international students",
    "marine science scholarship international students",
    "climate fellowship undergraduate students",
    "environment fellowship students international",
    "ocean science competition students",
    "environment competition students 2026",
    "climate hackathon students 2026",
    "data science competition students 2026",
    "ocean science student program 2026"
]


BLOCKED_DOMAINS = {
    "google.com",
    "googleusercontent.com",
    "support.google.com",
    "accounts.google.com",
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "youtube.com"
}


BLOCKED_URL_WORDS = {
    "feedback",
    "support.google",
    "accounts.google",
    "search?",
    "/search",
    "login",
    "signin",
    "signup",
    "register",
    "privacy",
    "terms",
    "preferences",
    "settings"
}


OPPORTUNITY_KEYWORDS = [
    "internship",
    "intern",
    "research",
    "researcher",
    "scholarship",
    "fellowship",
    "competition",
    "contest",
    "hackathon",
    "summer school",
    "summer program",
    "winter school",
    "winter program",
    "training",
    "workshop",
    "externship",
    "student program",
    "student opportunity",
    "grant",
    "challenge",
    "academy",
    "bootcamp",
    "volunteer",
    "career",
    "young professional",
    "youth program",
    "research assistant",
    "studentship"
]


def clean_url(url):
    if not url:
        return None

    url = unquote(url)

    # DuckDuckGo redirect URL
    if "duckduckgo.com/l/" in url:
        parsed = urlparse(url)
        params = parse_qs(parsed.query)

        if "uddg" in params:
            url = params["uddg"][0]

    url = url.split("#")[0]

    if not url.startswith(("http://", "https://")):
        return None

    return url


def is_bad_url(url):
    if not url:
        return True

    lower_url = url.lower()

    parsed = urlparse(lower_url)
    domain = parsed.netloc.replace("www.", "")

    # Block unwanted domains
    for blocked_domain in BLOCKED_DOMAINS:
        if (
            domain == blocked_domain
            or domain.endswith("." + blocked_domain)
        ):
            return True

    # Block unwanted URL patterns
    for blocked_word in BLOCKED_URL_WORDS:
        if blocked_word in lower_url:
            return True

    return False


def looks_like_opportunity(title, snippet):
    text = f"{title} {snippet}".lower()

    for keyword in OPPORTUNITY_KEYWORDS:
        if keyword in text:
            return True

    return False


def normalize_title(title):
    title = re.sub(r"\s+", " ", title)
    return title.strip()


def search_duckduckgo(query):
    url = (
        "https://html.duckduckgo.com/html/?q="
        + quote(query)
    )

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 "
            "(KHTML, like Gecko) "
            "Chrome/131.0 Safari/537.36"
        )
    }

    response = requests.get(
        url,
        headers=headers,
        timeout=30
    )

    response.raise_for_status()

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    results = []

    for result in soup.select(".result"):

        link = result.select_one(".result__a")
        snippet_element = result.select_one(
            ".result__snippet"
        )

        if not link:
            continue

        title = normalize_title(
            link.get_text(" ", strip=True)
        )

        href = link.get("href")

        snippet = ""

        if snippet_element:
            snippet = snippet_element.get_text(
                " ",
                strip=True
            )

        href = clean_url(href)

        if not href:
            continue

        if is_bad_url(href):
            continue

        if not looks_like_opportunity(
            title,
            snippet
        ):
            continue

        results.append({
            "source": "DuckDuckGo",
            "title": title,
            "url": href,
            "snippet": snippet
        })

    return results


def deduplicate(results):
    unique = []

    seen_urls = set()
    seen_titles = set()

    for item in results:

        url = item.get(
            "url",
            ""
        ).strip()

        title = item.get(
            "title",
            ""
        ).strip().lower()

        if not url or not title:
            continue

        normalized_url = url.rstrip("/").lower()

        normalized_title = re.sub(
            r"[^a-z0-9]+",
            " ",
            title
        ).strip()

        if normalized_url in seen_urls:
            continue

        if normalized_title in seen_titles:
            continue

        seen_urls.add(normalized_url)
        seen_titles.add(normalized_title)

        unique.append(item)

    return unique


def collect_opportunities():

    all_results = []

    print(
        f"Running {len(SEARCH_QUERIES)} "
        "targeted searches..."
    )

    for index, query in enumerate(
        SEARCH_QUERIES,
        start=1
    ):

        print(
            f"[{index}/{len(SEARCH_QUERIES)}] "
            f"{query}"
        )

        try:

            results = search_duckduckgo(
                query
            )

            print(
                f"    Found {len(results)} "
                "useful candidates"
            )

            all_results.extend(results)

        except Exception as error:

            print(
                f"    Search failed: {error}"
            )

    unique_results = deduplicate(
        all_results
    )

    print(
        f"Total candidates after cleaning: "
        f"{len(unique_results)}"
    )

    return unique_results

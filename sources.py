import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re


# ============================================================
# OFFICIAL / TRUSTED OPPORTUNITY SOURCES
# ============================================================

SOURCE_PAGES = [

    {
        "name": "NOAA Student Opportunities",
        "url": "https://www.noaa.gov/education/opportunities/students"
    },

    {
        "name": "NOAA Ocean Exploration Student Opportunities",
        "url": "https://oceanexplorer.noaa.gov/careers/student-opportunities/"
    },

    {
        "name": "NOAA Coastal Ocean Science Students",
        "url": "https://coastalscience.noaa.gov/students/"
    },

    {
        "name": "NOAA Coastal Ocean Science Internships",
        "url": "https://coastalscience.noaa.gov/about/internships/"
    },

    {
        "name": "NOAA Undergraduate Fellowships",
        "url": "https://coast.noaa.gov/fellowship/undgrad_opportunities.html"
    },

    {
        "name": "NOAA Fisheries Careers",
        "url": "https://www.fisheries.noaa.gov/topic/careers-more"
    },

    {
        "name": "NOAA AOML Student Opportunities",
        "url": "https://www.aoml.noaa.gov/outreach-education/"
    },

    {
        "name": "NOAA Weather Student Opportunities",
        "url": "https://wpo.noaa.gov/student-opportunities/"
    },

    {
        "name": "NOAA Climate Student Opportunities",
        "url": "https://www.noaa.gov/education"
    },

    {
        "name": "NASA Internships",
        "url": "https://intern.nasa.gov/"
    },

    {
        "name": "NASA STEM Gateway",
        "url": "https://stemgateway.nasa.gov/"
    },

    {
        "name": "NSF Research Experiences",
        "url": "https://www.nsf.gov/crssprgm/reu/"
    },

    {
        "name": "UCAR Undergraduate Opportunities",
        "url": "https://www.ucar.edu/education-training"
    }
]


# ============================================================
# KEYWORDS
# ============================================================

OPPORTUNITY_KEYWORDS = [

    "internship",
    "intern",
    "research",
    "research assistant",
    "research experience",
    "scholarship",
    "fellowship",
    "studentship",
    "summer school",
    "summer program",
    "winter school",
    "winter program",
    "training",
    "workshop",
    "competition",
    "contest",
    "challenge",
    "hackathon",
    "student opportunity",
    "student program",
    "youth program",
    "undergraduate",
    "graduate",
    "fellow",
    "scholar",
    "application",
    "apply"
]


# ============================================================
# HIGH-VALUE SUBJECT KEYWORDS
# ============================================================

FIELD_KEYWORDS = [

    "ocean",
    "oceanography",
    "oceanographic",
    "marine",
    "coastal",
    "fisheries",
    "climate",
    "climate change",
    "earth science",
    "environment",
    "environmental",
    "gis",
    "geographic information",
    "remote sensing",
    "satellite",
    "earth observation",
    "data science",
    "data analysis",
    "python",
    "matlab",
    "r programming",
    "modeling",
    "modelling",
    "weather",
    "atmospheric",
    "hydrology",
    "disaster",
    "risk",
    "sustainability",
    "conservation"
]


# ============================================================
# BLOCKED DOMAINS / LINKS
# ============================================================

BLOCKED_DOMAINS = {

    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "youtube.com",
    "twitter.com",
    "x.com",

    "google.com",
    "accounts.google.com",
    "support.google.com",

    "login.gov",
    "accounts.nasa.gov"
}


BLOCKED_WORDS = {

    "privacy",
    "cookie",
    "cookies",
    "terms",
    "accessibility",
    "contact",
    "feedback",
    "subscribe",
    "newsletter",
    "login",
    "signin",
    "sign-in",
    "register",
    "account",
    "sitemap",
    "facebook",
    "instagram",
    "youtube",
    "twitter"
}


# ============================================================
# REQUEST SESSION
# ============================================================

SESSION = requests.Session()

SESSION.headers.update({

    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/131.0 Safari/537.36"
    )

})


# ============================================================
# URL CHECK
# ============================================================

def is_valid_url(url):

    if not url:
        return False

    try:

        parsed = urlparse(url)

        if parsed.scheme not in {
            "http",
            "https"
        }:
            return False

        if not parsed.netloc:
            return False

        domain = parsed.netloc.lower()

        if domain.startswith("www."):
            domain = domain[4:]

        for blocked in BLOCKED_DOMAINS:

            if (
                domain == blocked
                or domain.endswith(
                    "." + blocked
                )
            ):
                return False

        return True

    except Exception:

        return False


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(text):

    if not text:
        return ""

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# CHECK OPPORTUNITY RELEVANCE
# ============================================================

def opportunity_score(title, text):

    combined = (
        f"{title} {text}"
    ).lower()

    score = 0

    # Opportunity type
    for keyword in OPPORTUNITY_KEYWORDS:

        if keyword in combined:
            score += 2

    # User's fields
    for keyword in FIELD_KEYWORDS:

        if keyword in combined:
            score += 1

    return score


# ============================================================
# FETCH PAGE
# ============================================================

def fetch_page(url):

    try:

        response = SESSION.get(
            url,
            timeout=30
        )

        response.raise_for_status()

        return response.text

    except Exception as error:

        print(
            f"    Page failed: {error}"
        )

        return None


# ============================================================
# EXTRACT LINKS
# ============================================================

def extract_links(
    html,
    source
):

    soup = BeautifulSoup(
        html,
        "html.parser"
    )

    results = []

    # --------------------------------------------------------
    # First collect page title
    # --------------------------------------------------------

    page_title = ""

    if soup.title:

        page_title = clean_text(
            soup.title.get_text(
                " ",
                strip=True
            )
        )

    # --------------------------------------------------------
    # Extract all links
    # --------------------------------------------------------

    for link in soup.find_all(
        "a",
        href=True
    ):

        href = link.get(
            "href"
        )

        title = clean_text(
            link.get_text(
                " ",
                strip=True
            )
        )

        if not title:
            continue

        absolute_url = urljoin(
            source["url"],
            href
        )

        if not is_valid_url(
            absolute_url
        ):
            continue

        lower_title = title.lower()
        lower_url = absolute_url.lower()

        # ----------------------------------------------------
        # Ignore obvious navigation links
        # ----------------------------------------------------

        blocked = False

        for word in BLOCKED_WORDS:

            if (
                word in lower_title
                and len(title) < 80
            ):

                blocked = True
                break

            if word in lower_url:

                blocked = True
                break

        if blocked:
            continue

        # ----------------------------------------------------
        # Calculate relevance
        # ----------------------------------------------------

        relevance = opportunity_score(
            title,
            page_title
        )

        # Also check URL
        relevance += opportunity_score(
            "",
            lower_url
        )

        # ----------------------------------------------------
        # Only keep potentially useful links
        # ----------------------------------------------------

        if relevance < 2:
            continue

        results.append({

            "source": source["name"],

            "title": title,

            "url": absolute_url,

            "snippet": (
                f"{title}. "
                f"Found on {page_title}."
            )

        })

    return results


# ============================================================
# EXTRACT OPPORTUNITIES FROM SOURCE PAGE
# ============================================================

def collect_from_source(source):

    print(
        f"\nSource: {source['name']}"
    )

    print(
        f"URL: {source['url']}"
    )

    html = fetch_page(
        source["url"]
    )

    if not html:

        return []

    results = extract_links(
        html,
        source
    )

    print(
        f"    Candidates found: "
        f"{len(results)}"
    )

    return results


# ============================================================
# DEDUPLICATION
# ============================================================

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
        ).strip()

        if not url or not title:
            continue

        normalized_url = (
            url.rstrip("/")
            .lower()
        )

        normalized_title = re.sub(
            r"[^a-z0-9]+",
            " ",
            title.lower()
        ).strip()

        if normalized_url in seen_urls:
            continue

        if normalized_title in seen_titles:
            continue

        seen_urls.add(
            normalized_url
        )

        seen_titles.add(
            normalized_title
        )

        unique.append(item)

    return unique


# ============================================================
# FINAL KEYWORD FILTER
# ============================================================

def final_filter(results):

    filtered = []

    for item in results:

        title = item.get(
            "title",
            ""
        )

        snippet = item.get(
            "snippet",
            ""
        )

        url = item.get(
            "url",
            ""
        )

        combined = (
            f"{title} "
            f"{snippet} "
            f"{url}"
        ).lower()

        opportunity_match = any(
            keyword in combined
            for keyword in OPPORTUNITY_KEYWORDS
        )

        field_match = any(
            keyword in combined
            for keyword in FIELD_KEYWORDS
        )

        # We need at least one opportunity
        # keyword AND preferably a field match.
        #
        # Some general student opportunities
        # may not contain a field keyword,
        # so those are allowed with stronger
        # opportunity signals.

        opportunity_count = sum(
            keyword in combined
            for keyword in OPPORTUNITY_KEYWORDS
        )

        if (
            opportunity_match
            and (
                field_match
                or opportunity_count >= 2
            )
        ):

            filtered.append(item)

    return filtered


# ============================================================
# MAIN COLLECTOR
# ============================================================

def collect_opportunities():

    print(
        "\n"
        "=============================================="
    )

    print(
        "🌊 COLLECTING OPPORTUNITIES"
    )

    print(
        "=============================================="
    )

    all_results = []

    for source in SOURCE_PAGES:

        try:

            results = collect_from_source(
                source
            )

            all_results.extend(
                results
            )

        except Exception as error:

            print(
                f"    Source error: {error}"
            )

    print(
        "\nRaw candidates: "
        f"{len(all_results)}"
    )

    # --------------------------------------------------------
    # Deduplicate
    # --------------------------------------------------------

    unique_results = deduplicate(
        all_results
    )

    print(
        "After deduplication: "
        f"{len(unique_results)}"
    )

    # --------------------------------------------------------
    # Final filter
    # --------------------------------------------------------

    filtered_results = final_filter(
        unique_results
    )

    print(
        "After keyword filtering: "
        f"{len(filtered_results)}"
    )

    # --------------------------------------------------------
    # Limit collector output
    # --------------------------------------------------------

    filtered_results = filtered_results[:80]

    print(
        "Sending to AI: "
        f"{len(filtered_results)}"
    )

    return filtered_results

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote, urlparse
import xml.etree.ElementTree as ET
import re
from datetime import datetime

from googlenewsdecoder import gnewsdecoder


CURRENT_YEAR = datetime.now().year


SEARCH_QUERIES = [
    "oceanography internship undergraduate 2026",
    "marine science internship undergraduate 2026",
    "ocean science research internship 2026",
    "oceanography summer school 2026",
    "marine science summer school 2026",

    "GIS internship undergraduate 2026",
    "remote sensing internship students 2026",
    "earth observation internship 2026",
    "GIS summer school 2026",

    "climate change internship undergraduate 2026",
    "climate research internship 2026",
    "climate fellowship students 2026",
    "climate summer school 2026",

    "environmental science internship 2026",
    "environment research internship 2026",
    "environmental fellowship students 2026",

    "data science internship undergraduate 2026",
    "data science competition students 2026",

    "undergraduate research opportunity international students 2026",
    "student scholarship international students 2026",
    "student fellowship international students 2026",

    "student competition 2026",
    "student hackathon 2026",
    "youth climate program 2026"
]


GOOGLE_NEWS_RSS = (
    "https://news.google.com/rss/search?"
    "q={query}"
    "&hl=en-US"
    "&gl=US"
    "&ceid=US:en"
)


OPPORTUNITY_KEYWORDS = [
    "internship",
    "intern",
    "research internship",
    "research opportunity",
    "research program",
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
    "hackathon",
    "challenge",
    "student program",
    "student opportunity",
    "youth program",
    "call for applications",
    "applications open",
    "apply now"
]


FIELD_KEYWORDS = [
    "ocean",
    "oceanography",
    "marine",
    "coastal",
    "fisheries",
    "climate",
    "environment",
    "environmental",
    "gis",
    "geospatial",
    "remote sensing",
    "earth observation",
    "satellite",
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


BLOCKED_DOMAINS = {
    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "youtube.com",
    "twitter.com",
    "x.com",
    "news.google.com"
}


SESSION = requests.Session()

SESSION.headers.update({
    "User-Agent":
        "Mozilla/5.0 "
        "(Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "Chrome/131.0 Safari/537.36"
})


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_text(text):

    if not text:
        return ""

    text = BeautifulSoup(
        text,
        "html.parser"
    ).get_text(
        " ",
        strip=True
    )

    text = re.sub(
        r"\s+",
        " ",
        text
    )

    return text.strip()


# ============================================================
# URL VALIDATION
# ============================================================

def valid_url(url):

    if not url:
        return False

    try:

        parsed = urlparse(url)

        if parsed.scheme not in (
            "http",
            "https"
        ):
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
# GOOGLE NEWS URL CHECK
# ============================================================

def is_google_news_url(url):

    if not url:
        return False

    try:

        domain = urlparse(
            url
        ).netloc.lower()

        return (
            domain == "news.google.com"
            or domain.endswith(
                ".news.google.com"
            )
        )

    except Exception:

        return False


# ============================================================
# OLD YEAR CHECK
# ============================================================

def contains_old_year(text):

    if not text:
        return False

    years = re.findall(
        r"\b(20\d{2})\b",
        text
    )

    for year in years:

        year = int(year)

        if year < CURRENT_YEAR - 1:

            return True

    return False


# ============================================================
# RELEVANCE CHECK
# ============================================================

def is_relevant(
    title,
    description
):

    text = (
        f"{title} "
        f"{description}"
    ).lower()

    opportunity_hits = sum(
        keyword in text
        for keyword in OPPORTUNITY_KEYWORDS
    )

    field_hits = sum(
        keyword in text
        for keyword in FIELD_KEYWORDS
    )

    if opportunity_hits >= 2:

        return True

    if (
        opportunity_hits >= 1
        and field_hits >= 1
    ):

        return True

    return False


# ============================================================
# DECODE GOOGLE NEWS URL
# ============================================================

def decode_google_news_url(
    google_url
):

    if not is_google_news_url(
        google_url
    ):

        return google_url

    try:

        result = gnewsdecoder(
            google_url,
            interval=1
        )

        if not result.get(
            "status"
        ):

            print(
                "    Google URL decode failed"
            )

            return None

        decoded_url = result.get(
            "decoded_url"
        )

        if not decoded_url:

            return None

        if is_google_news_url(
            decoded_url
        ):

            return None

        return decoded_url

    except Exception as error:

        print(
            f"    Google decoder error: "
            f"{error}"
        )

        return None


# ============================================================
# SEARCH GOOGLE NEWS
# ============================================================

def search_google_news(
    query
):

    url = GOOGLE_NEWS_RSS.format(
        query=quote(query)
    )

    try:

        response = SESSION.get(
            url,
            timeout=30
        )

        response.raise_for_status()

    except Exception as error:

        print(
            f"    RSS error: {error}"
        )

        return []

    try:

        root = ET.fromstring(
            response.content
        )

    except Exception as error:

        print(
            f"    XML error: {error}"
        )

        return []

    results = []

    for item in root.findall(
        ".//item"
    ):

        title_node = item.find(
            "title"
        )

        link_node = item.find(
            "link"
        )

        description_node = (
            item.find(
                "description"
            )
        )

        pubdate_node = (
            item.find(
                "pubDate"
            )
        )

        source_node = (
            item.find(
                "source"
            )
        )

        if (
            title_node is None
            or link_node is None
        ):

            continue

        title = clean_text(
            title_node.text
        )

        google_url = (
            link_node.text
            or ""
        ).strip()

        description = ""

        if description_node is not None:

            description = clean_text(
                description_node.text
            )

        published = ""

        if pubdate_node is not None:

            published = clean_text(
                pubdate_node.text
            )

        source_name = ""

        if source_node is not None:

            source_name = clean_text(
                source_node.text
            )

        # ----------------------------------------------------
        # Basic filtering
        # ----------------------------------------------------

        if contains_old_year(
            f"{title} {description}"
        ):

            continue

        if not is_relevant(
            title,
            description
        ):

            continue

        # ----------------------------------------------------
        # Decode Google News URL
        # ----------------------------------------------------

        print(
            f"    Decoding: {title[:80]}"
        )

        original_url = (
            decode_google_news_url(
                google_url
            )
        )

        # VERY IMPORTANT:
        # Never send Google URLs forward.
        if not original_url:

            print(
                "    Rejected: "
                "could not resolve publisher URL"
            )

            continue

        if is_google_news_url(
            original_url
        ):

            print(
                "    Rejected: "
                "still a Google News URL"
            )

            continue

        if not valid_url(
            original_url
        ):

            continue

        results.append({

            "source":
                source_name
                or "Google News",

            "title":
                title,

            "url":
                original_url,

            "snippet":
                description,

            "published":
                published

        })

    return results


# ============================================================
# VERIFY REAL ARTICLE PAGE
# ============================================================

def verify_page(
    item
):

    url = item.get(
        "url",
        ""
    )

    if not url:

        return None

    # --------------------------------------------------------
    # Safety check
    # --------------------------------------------------------

    if is_google_news_url(
        url
    ):

        return None

    try:

        response = SESSION.get(
            url,
            timeout=25,
            allow_redirects=True
        )

        response.raise_for_status()

    except Exception as error:

        print(
            f"    Page error: {error}"
        )

        return None

    final_url = response.url

    # --------------------------------------------------------
    # Reject if redirect ended at Google
    # --------------------------------------------------------

    if is_google_news_url(
        final_url
    ):

        return None

    if not valid_url(
        final_url
    ):

        return None

    item["url"] = final_url

    try:

        soup = BeautifulSoup(
            response.text,
            "html.parser"
        )

    except Exception:

        return None

    page_title = ""

    if soup.title:

        page_title = clean_text(
            soup.title.get_text(
                " ",
                strip=True
            )
        )

    page_text = clean_text(
        soup.get_text(
            " ",
            strip=True
        )
    )

    # --------------------------------------------------------
    # Reject empty pages
    # --------------------------------------------------------

    if len(page_text) < 200:

        print(
            "    Rejected: page too short"
        )

        return None

    # --------------------------------------------------------
    # Reject clearly old pages
    # --------------------------------------------------------

    first_part = page_text[:7000]

    if contains_old_year(
        f"{page_title} {first_part}"
    ):

        print(
            "    Rejected: old opportunity"
        )

        return None

    # --------------------------------------------------------
    # Make sure actual opportunity exists
    # --------------------------------------------------------

    combined_text = (
        f"{page_title} "
        f"{first_part}"
    ).lower()

    opportunity_hits = sum(
        keyword in combined_text
        for keyword in OPPORTUNITY_KEYWORDS
    )

    field_hits = sum(
        keyword in combined_text
        for keyword in FIELD_KEYWORDS
    )

    if (
        opportunity_hits == 0
        or field_hits == 0
    ):

        print(
            "    Rejected: weak opportunity relevance"
        )

        return None

    # --------------------------------------------------------
    # Update title
    # --------------------------------------------------------

    if page_title:

        item["title"] = page_title

    # --------------------------------------------------------
    # Store real page content
    # --------------------------------------------------------

    item["snippet"] = page_text[:5000]

    return item


# ============================================================
# DEDUPLICATION
# ============================================================

def deduplicate(
    results
):

    unique = []

    seen_urls = set()

    seen_titles = set()

    for item in results:

        url = (
            item.get(
                "url",
                ""
            )
            .strip()
            .lower()
        )

        title = (
            item.get(
                "title",
                ""
            )
            .strip()
            .lower()
        )

        if not url or not title:

            continue

        if is_google_news_url(
            url
        ):

            continue

        normalized_title = re.sub(
            r"[^a-z0-9]+",
            " ",
            title
        ).strip()

        if url in seen_urls:

            continue

        if normalized_title in seen_titles:

            continue

        seen_urls.add(url)

        seen_titles.add(
            normalized_title
        )

        unique.append(
            item
        )

    return unique


# ============================================================
# MAIN COLLECTOR
# ============================================================

def collect_opportunities():

    print(
        "\n=================================================="
    )

    print(
        "🌊 OCG OPPORTUNITY RADAR"
    )

    print(
        "CURRENT YEAR:",
        CURRENT_YEAR
    )

    print(
        "=================================================="
    )

    all_results = []

    # --------------------------------------------------------
    # SEARCH
    # --------------------------------------------------------

    print(
        "\n1. Searching opportunity feeds..."
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

            results = search_google_news(
                query
            )

            print(
                f"    Real candidates: "
                f"{len(results)}"
            )

            all_results.extend(
                results
            )

        except Exception as error:

            print(
                f"    Failed: {error}"
            )

    print(
        f"\nRaw candidates: "
        f"{len(all_results)}"
    )

    all_results = deduplicate(
        all_results
    )

    print(
        f"After deduplication: "
        f"{len(all_results)}"
    )

    # --------------------------------------------------------
    # VERIFY
    # --------------------------------------------------------

    print(
        "\n2. Verifying publisher pages..."
    )

    verified = []

    for index, item in enumerate(
        all_results[:40],
        start=1
    ):

        print(
            f"\nChecking "
            f"{index}/{min(40, len(all_results))}: "
            f"{item.get('title', '')}"
        )

        verified_item = verify_page(
            item
        )

        if verified_item:

            verified.append(
                verified_item
            )

    verified = deduplicate(
        verified
    )

    print(
        f"\nVerified candidates: "
        f"{len(verified)}"
    )

    verified = verified[:40]

    print(
        "\nFINAL CANDIDATES SENT TO AI:"
    )

    for index, item in enumerate(
        verified,
        start=1
    ):

        print(
            f"\n{index}. "
            f"{item.get('title', '')}"
        )

        print(
            f"   URL: "
            f"{item.get('url', '')}"
        )

        print(
            f"   Source: "
            f"{item.get('source', '')}"
        )

    return verified

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote, urlparse
import xml.etree.ElementTree as ET
import re


# ============================================================
# SEARCH QUERIES
# ============================================================

SEARCH_QUERIES = [

    # Ocean
    "oceanography internship undergraduate",
    "marine science internship undergraduate",
    "ocean science research internship students",
    "marine research internship students",
    "physical oceanography internship",
    "oceanography summer school students",

    # GIS / Remote sensing
    "GIS internship undergraduate",
    "remote sensing internship students",
    "GIS remote sensing summer school",
    "earth observation internship students",
    "geospatial competition students",

    # Climate
    "climate change internship undergraduate",
    "climate research internship students",
    "climate fellowship undergraduate",
    "climate summer school students",

    # Environment
    "environmental science internship undergraduate",
    "environment research internship students",
    "environmental fellowship students",

    # Data
    "data science internship undergraduate",
    "data science competition students",
    "Python research internship students",

    # General
    "international student internship undergraduate",
    "undergraduate research opportunity international students",
    "student fellowship international students",
    "student scholarship international students",
    "student competition 2026",
    "student hackathon 2026",
    "youth climate program 2026",
    "student research program 2026"
]


# ============================================================
# GOOGLE NEWS RSS
# ============================================================

GOOGLE_NEWS_RSS = (
    "https://news.google.com/rss/search?"
    "q={query}"
    "&hl=en-US"
    "&gl=US"
    "&ceid=US:en"
)


# ============================================================
# DIRECT TRUSTED SOURCES
# ============================================================

DIRECT_SOURCES = [

    {
        "name": "NOAA Student Opportunities",
        "url":
        "https://www.noaa.gov/education/opportunities/students"
    },

    {
        "name": "NOAA Weather Program Office",
        "url":
        "https://wpo.noaa.gov/student-opportunities/"
    },

    {
        "name": "NOAA AOML Student Opportunities",
        "url":
        "https://www.aoml.noaa.gov/outreach-education/"
    },

    {
        "name": "NOAA IOOS Student Opportunities",
        "url":
        "https://ioos.noaa.gov/community/education/student-opportunities/"
    },

    {
        "name": "NOAA Undergraduate Fellowships",
        "url":
        "https://coast.noaa.gov/fellowship/undgrad_opportunities.html"
    },

    {
        "name": "NASA Internships",
        "url":
        "https://intern.nasa.gov/"
    },

    {
        "name": "NASA STEM Gateway",
        "url":
        "https://stemgateway.nasa.gov/"
    },

    {
        "name": "NSF Research Experiences",
        "url":
        "https://www.nsf.gov/crssprgm/reu/"
    },

    {
        "name": "UCAR Education",
        "url":
        "https://www.ucar.edu/education-training"
    }
]


# ============================================================
# KEYWORDS
# ============================================================

OPPORTUNITY_KEYWORDS = [

    "internship",
    "intern",
    "research opportunity",
    "research program",
    "research internship",
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
    "undergraduate opportunity",
    "application",
    "apply",
    "call for applications"
]


FIELD_KEYWORDS = [

    "ocean",
    "oceanography",
    "oceanographic",
    "marine",
    "coastal",
    "fisheries",
    "climate",
    "climate change",
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


# ============================================================
# BLOCKED URL WORDS
# ============================================================

BLOCKED_WORDS = [

    "facebook.com",
    "instagram.com",
    "linkedin.com",
    "youtube.com",
    "twitter.com",
    "x.com",

    "/login",
    "/signin",
    "/signup",
    "/register",

    "privacy",
    "terms",
    "cookie",
    "feedback",
    "preferences",
    "settings"
]


# ============================================================
# SESSION
# ============================================================

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

        lower = url.lower()

        for word in BLOCKED_WORDS:

            if word in lower:
                return False

        return True

    except Exception:

        return False


# ============================================================
# RELEVANCE
# ============================================================

def is_relevant(
    title,
    description
):

    text = (
        f"{title} {description}"
    ).lower()

    opportunity_hits = 0
    field_hits = 0

    for keyword in OPPORTUNITY_KEYWORDS:

        if keyword in text:
            opportunity_hits += 1

    for keyword in FIELD_KEYWORDS:

        if keyword in text:
            field_hits += 1

    # Strong opportunity signal
    if opportunity_hits >= 2:
        return True

    # One opportunity + one relevant field
    if (
        opportunity_hits >= 1
        and field_hits >= 1
    ):
        return True

    return False


# ============================================================
# GOOGLE NEWS RSS SEARCH
# ============================================================

def search_google_news(query):

    encoded_query = quote(
        query
    )

    url = GOOGLE_NEWS_RSS.format(
        query=encoded_query
    )

    try:

        response = SESSION.get(
            url,
            timeout=30
        )

        response.raise_for_status()

    except Exception as error:

        print(
            f"    RSS failed: {error}"
        )

        return []

    try:

        root = ET.fromstring(
            response.content
        )

    except Exception as error:

        print(
            f"    RSS parsing failed: {error}"
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

        description_node = item.find(
            "description"
        )

        if title_node is None:
            continue

        if link_node is None:
            continue

        title = clean_text(
            title_node.text
        )

        url = (
            link_node.text
            or ""
        ).strip()

        description = ""

        if description_node is not None:

            description = clean_text(
                description_node.text
            )

        if not title:
            continue

        if not valid_url(url):
            continue

        if not is_relevant(
            title,
            description
        ):
            continue

        results.append({

            "source":
                "Google News RSS",

            "title":
                title,

            "url":
                url,

            "snippet":
                description

        })

    return results


# ============================================================
# DIRECT SOURCE PAGE
# ============================================================

def collect_direct_source(
    source
):

    print(
        f"\nDirect source: "
        f"{source['name']}"
    )

    try:

        response = SESSION.get(
            source["url"],
            timeout=30
        )

        response.raise_for_status()

    except Exception as error:

        print(
            f"    Failed: {error}"
        )

        return []

    soup = BeautifulSoup(
        response.text,
        "html.parser"
    )

    page_text = clean_text(
        soup.get_text(
            " ",
            strip=True
        )
    )

    title = ""

    if soup.title:

        title = clean_text(
            soup.title.get_text(
                " ",
                strip=True
            )
        )

    results = []

    # The source page itself is a valid
    # opportunity hub.
    #
    # We send it to the AI instead of
    # requiring the HTML structure to
    # expose individual opportunities.

    if is_relevant(
        title,
        page_text[:8000]
    ):

        results.append({

            "source":
                source["name"],

            "title":
                title
                or source["name"],

            "url":
                source["url"],

            "snippet":
                page_text[:3000]

        })

    # Also collect useful links
    for link in soup.find_all(
        "a",
        href=True
    ):

        link_title = clean_text(
            link.get_text(
                " ",
                strip=True
            )
        )

        href = link.get(
            "href"
        )

        if not link_title:
            continue

        absolute_url = (
            href
            if href.startswith(
                "http://"
            ) or href.startswith(
                "https://"
            )
            else None
        )

        if not absolute_url:
            continue

        if not valid_url(
            absolute_url
        ):
            continue

        if not is_relevant(
            link_title,
            absolute_url
        ):
            continue

        results.append({

            "source":
                source["name"],

            "title":
                link_title,

            "url":
                absolute_url,

            "snippet":
                f"{link_title} "
                f"from {source['name']}"

        })

    print(
        f"    Found {len(results)} "
        "candidates"
    )

    return results


# ============================================================
# DEDUPLICATE
# ============================================================

def deduplicate(results):

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
        )

        title = (
            item.get(
                "title",
                ""
            )
            .strip()
        )

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
# MAIN
# ============================================================

def collect_opportunities():

    print(
        "\n"
        "=================================================="
    )

    print(
        "🌊 OCG OPPORTUNITY RADAR COLLECTOR"
    )

    print(
        "=================================================="
    )

    all_results = []

    # --------------------------------------------------------
    # GOOGLE NEWS RSS
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
                f"    Found {len(results)}"
            )

            all_results.extend(
                results
            )

        except Exception as error:

            print(
                f"    Search error: {error}"
            )

    # --------------------------------------------------------
    # DIRECT TRUSTED SOURCES
    # --------------------------------------------------------

    print(
        "\n2. Checking trusted sources..."
    )

    for source in DIRECT_SOURCES:

        try:

            results = collect_direct_source(
                source
            )

            all_results.extend(
                results
            )

        except Exception as error:

            print(
                f"    Source error: {error}"
            )

    # --------------------------------------------------------
    # DEDUPLICATE
    # --------------------------------------------------------

    print(
        "\n3. Cleaning candidates..."
    )

    unique_results = deduplicate(
        all_results
    )

    print(
        f"Raw candidates: "
        f"{len(all_results)}"
    )

    print(
        f"Unique candidates: "
        f"{len(unique_results)}"
    )

    # --------------------------------------------------------
    # LIMIT
    # --------------------------------------------------------

    unique_results = unique_results[:80]

    print(
        f"Final candidates sent to AI: "
        f"{len(unique_results)}"
    )

    # --------------------------------------------------------
    # DEBUG LIST
    # --------------------------------------------------------

    print(
        "\nFIRST CANDIDATES:"
    )

    for index, item in enumerate(
        unique_results[:10],
        start=1
    ):

        print(
            f"{index}. "
            f"{item.get('title', '')}"
        )

        print(
            f"   {item.get('url', '')}"
        )

    return unique_results

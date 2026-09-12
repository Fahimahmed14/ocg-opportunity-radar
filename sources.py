import re
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from googlenewsdecoder import gnewsdecoder


# ============================================================
# OCG OPPORTUNITY RADAR - SOURCES V5
# ============================================================

CURRENT_YEAR = 2026
NEXT_YEAR = 2027

TODAY = datetime.now().date()

SEARCH_WORKERS = 8
VERIFY_WORKERS = 8

MAX_RESULTS_PER_QUERY = 8
MAX_VERIFY_CANDIDATES = 45
MAX_AI_CANDIDATES = 25

REQUEST_TIMEOUT = 8

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/139.0 Safari/537.36"
    )
}


# ============================================================
# SEARCH QUERIES
# ============================================================

SEARCH_QUERIES = [

    # Oceanography / Marine
    '"oceanography" internship 2026 applications',
    '"marine science" internship 2026 undergraduate',
    '"ocean science" internship 2026 students',
    '"marine research" internship 2026 students',
    '"oceanography" "summer school" 2026 2027',
    '"marine science" "summer school" 2026 2027',
    '"oceanography" fellowship 2026 students',
    '"marine science" fellowship 2026 students',

    # GIS / Remote Sensing
    '"GIS" internship 2026 students',
    '"GIS" research internship 2026 undergraduate',
    '"remote sensing" internship 2026 students',
    '"Earth observation" internship 2026 students',
    '"geospatial" internship 2026 students',

    # Climate / Environment
    '"climate" internship 2026 undergraduate',
    '"climate change" fellowship 2026 students',
    '"environmental science" internship 2026 students',
    '"environment" research internship 2026',
    '"environmental" fellowship 2026 students',

    # Research / Data
    '"undergraduate research" ocean 2026',
    '"research internship" environmental science 2026',
    '"data science" research internship 2026 students',
    '"scientific computing" internship 2026 students',

    # Scholarships / Fellowships
    '"ocean" scholarship 2026 undergraduate',
    '"marine" scholarship 2026 students',
    '"climate" scholarship 2026 undergraduate',
    '"climate" fellowship 2026 undergraduate',

    # Competitions
    '"ocean" competition 2026 students',
    '"ocean" hackathon 2026',
    '"climate" hackathon 2026 students',
    '"GIS" competition 2026 students',

    # Youth
    '"climate" youth program 2026 applications',
    '"environment" youth program 2026 applications',
    '"ocean" youth program 2026 applications',

    # Bangladesh / Asia
    '"Bangladesh" oceanography internship 2026',
    '"Bangladesh" climate fellowship 2026 students',
    '"Asia" marine science internship 2026',
]


# ============================================================
# DOMAIN QUALITY
# ============================================================

HIGH_VALUE_DOMAINS = [
    ".edu",
    ".ac.uk",
    ".ac.jp",
    ".ac.in",
    ".edu.au",
    ".gov",
    ".gov.uk",
    ".int",
    ".org",
]

OFFICIAL_DOMAIN_KEYWORDS = [
    "nasa.gov",
    "noaa.gov",
    "usgs.gov",
    "esa.int",
    "copernicus.eu",
    "europa.eu",
    "un.org",
    "unesco.org",
    "fao.org",
    "wmo.int",
    "worldbank.org",
    "undp.org",
    "iucn.org",
    "mit.edu",
    "harvard.edu",
    "stanford.edu",
    "ox.ac.uk",
    "cam.ac.uk",
    "soton.ac.uk",
    "uw.edu",
    "whoi.edu",
]

LOW_VALUE_DOMAINS = [
    "facebook.com",
    "instagram.com",
    "youtube.com",
    "twitter.com",
    "x.com",
    "linkedin.com",
    "reddit.com",
    "pinterest.com",
    "tiktok.com",
]

AGGREGATOR_DOMAINS = [
    "globalsouthopportunities.com",
    "opportunitydesk.org",
    "scholarshiproar.com",
    "scholarshipregion.com",
    "scholars4dev.com",
    "youthop.com",
    "opportunitiescorners.info",
]


# ============================================================
# URL / PAGE FILTERS
# ============================================================

BAD_PATH_TERMS = [
    "/news/",
    "/newsroom/",
    "/stories/",
    "/story/",
    "/blog/",
    "/blogs/",
    "/press-release/",
    "/press-releases/",
    "/article/",
    "/articles/",
    "/media/",
    "/events/archive/",
    "/archive/",
    "/alumni/",
]

BAD_TITLE_TERMS = [
    "congratulations",
    "congrats",
    "meet our",
    "student spotlight",
    "student profile",
    "student story",
    "our students",
    "awardees",
    "winners",
    "announces",
    "announced",
    "welcomes",
    "celebrates",
    "graduated",
    "graduates",
    "graduation",
    "recap",
    "highlights",
    "success story",
    "journey",
    "news",
    "press release",
]


# ============================================================
# BASIC HELPERS
# ============================================================

def clean_text(text):

    if not text:
        return ""

    return re.sub(
        r"\s+",
        " ",
        text
    ).strip()


def normalize_url(url):

    if not url:
        return ""

    url = url.strip()

    if url.startswith("//"):
        url = "https:" + url

    if not url.startswith(
        ("http://", "https://")
    ):
        return ""

    return url.split("#")[0]


def get_domain(url):

    try:

        return urlparse(
            url
        ).netloc.lower().replace(
            "www.",
            ""
        )

    except Exception:
        return ""


def get_path(url):

    try:
        return urlparse(url).path.lower()

    except Exception:
        return ""


def is_google_news_url(url):

    if not url:
        return True

    domain = get_domain(url)

    return (
        "news.google.com" in domain
        or domain == "google.com"
    )


def is_social_url(url):

    domain = get_domain(url)

    return any(
        bad in domain
        for bad in LOW_VALUE_DOMAINS
    )


def is_aggregator(url):

    domain = get_domain(url)

    return any(
        domain == d
        or domain.endswith("." + d)
        for d in AGGREGATOR_DOMAINS
    )


def is_bad_path(url):

    path = get_path(url)

    return any(
        term in path
        for term in BAD_PATH_TERMS
    )


def has_bad_title(title):

    title = clean_text(
        title
    ).lower()

    return any(
        term in title
        for term in BAD_TITLE_TERMS
    )


def domain_quality(url):

    domain = get_domain(url)

    if not domain:
        return 0

    if is_social_url(url):
        return 0

    score = 0

    if any(
        domain.endswith(x)
        for x in HIGH_VALUE_DOMAINS
    ):
        score += 25

    if any(
        x in domain
        for x in OFFICIAL_DOMAIN_KEYWORDS
    ):
        score += 40

    if is_aggregator(url):
        score += 5

    if domain.endswith(".org"):
        score += 10

    if domain.endswith(".edu"):
        score += 30

    return min(
        score,
        70
    )


# ============================================================
# GOOGLE NEWS DECODER
# ============================================================

def decode_google_news_url(url):

    if not url:
        return ""

    if not is_google_news_url(url):
        return normalize_url(url)

    try:

        result = gnewsdecoder(url)

        if isinstance(
            result,
            dict
        ):

            decoded = result.get(
                "decoded_url"
            )

            if decoded:

                decoded = normalize_url(
                    decoded
                )

                if (
                    decoded
                    and not is_google_news_url(decoded)
                ):
                    return decoded

    except Exception:
        pass

    return ""


# ============================================================
# GOOGLE NEWS SEARCH
# ============================================================

def search_google_news(query):

    url = (
        "https://news.google.com/rss/search?"
        f"q={requests.utils.quote(query)}"
        "&hl=en-US"
        "&gl=US"
        "&ceid=US:en"
    )

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        soup = BeautifulSoup(
            response.text,
            "xml",
        )

        results = []

        for item in soup.find_all(
            "item"
        )[:MAX_RESULTS_PER_QUERY]:

            title = clean_text(
                item.title.get_text()
                if item.title
                else ""
            )

            google_url = (
                item.link.get_text(
                    strip=True
                )
                if item.link
                else ""
            )

            description = clean_text(
                item.description.get_text()
                if item.description
                else ""
            )

            published = clean_text(
                item.pubDate.get_text()
                if item.pubDate
                else ""
            )

            if not title or not google_url:
                continue

            results.append({
                "title": title,
                "google_url": google_url,
                "description": description,
                "published": published,
            })

        return results

    except Exception as e:

        print(
            f"Search failed: "
            f"{query[:70]}... -> {e}"
        )

        return []


# ============================================================
# PARALLEL SEARCH
# ============================================================

def collect_google_news_results():

    all_results = []

    print(
        f"Running {len(SEARCH_QUERIES)} searches "
        f"with {SEARCH_WORKERS} workers..."
    )

    with ThreadPoolExecutor(
        max_workers=SEARCH_WORKERS
    ) as executor:

        futures = {
            executor.submit(
                search_google_news,
                query,
            ): query
            for query in SEARCH_QUERIES
        }

        for future in as_completed(
            futures
        ):

            query = futures[future]

            try:

                results = future.result()

                print(
                    f"  ✓ {len(results):2d} results | "
                    f"{query[:65]}"
                )

                all_results.extend(
                    results
                )

            except Exception as e:

                print(
                    f"  ✗ Search error | "
                    f"{query[:65]} | {e}"
                )

    return all_results


# ============================================================
# URL DECODING
# ============================================================

def decode_results(results):

    decoded = []

    print(
        f"\nDecoding {len(results)} "
        f"Google News URLs..."
    )

    def decode_one(item):

        publisher_url = decode_google_news_url(
            item.get(
                "google_url",
                ""
            )
        )

        if not publisher_url:
            return None

        item = item.copy()

        item["url"] = publisher_url

        return item

    with ThreadPoolExecutor(
        max_workers=SEARCH_WORKERS
    ) as executor:

        futures = [
            executor.submit(
                decode_one,
                item,
            )
            for item in results
        ]

        for future in as_completed(
            futures
        ):

            try:

                result = future.result()

                if result:
                    decoded.append(
                        result
                    )

            except Exception:
                pass

    return decoded


# ============================================================
# DEDUPLICATION
# ============================================================

def deduplicate_results(results):

    seen_urls = set()
    seen_titles = set()

    unique = []

    for item in results:

        url = normalize_url(
            item.get(
                "url",
                ""
            )
        )

        title = clean_text(
            item.get(
                "title",
                ""
            )
        ).lower()

        if not url:
            continue

        if is_google_news_url(url):
            continue

        if is_social_url(url):
            continue

        title_key = re.sub(
            r"[^a-z0-9]+",
            "",
            title
        )

        if url in seen_urls:
            continue

        if (
            title_key
            and title_key in seen_titles
        ):
            continue

        seen_urls.add(url)

        if title_key:
            seen_titles.add(
                title_key
            )

        item["url"] = url

        unique.append(item)

    return unique


# ============================================================
# OPPORTUNITY SIGNALS
# ============================================================

STRONG_FIELD_TERMS = [
    "oceanography",
    "ocean science",
    "ocean sciences",
    "marine science",
    "marine sciences",
    "marine research",
    "physical oceanography",
    "coastal science",
    "ocean modelling",
    "ocean modeling",
    "marine biology",
    "fisheries",
    "remote sensing",
    "earth observation",
    "geospatial",
    "gis",
    "geographic information",
    "climate science",
    "climate change",
    "environmental science",
    "environment",
    "disaster risk",
    "data science",
    "scientific computing",
]


OPPORTUNITY_TERMS = [
    "internship",
    "intern",
    "research",
    "research assistant",
    "scholarship",
    "fellowship",
    "summer school",
    "winter school",
    "training",
    "hackathon",
    "competition",
    "challenge",
    "program",
    "programme",
    "students",
    "undergraduate",
    "application",
    "applications",
    "apply",
    "call for applications",
]


BAD_TERMS = [
    "job vacancy",
    "senior manager",
    "director",
    "chief",
    "professor position",
    "phd position",
    "postdoctoral",
    "postdoc",
    "sales manager",
    "marketing manager",
    "software engineer",
    "developer",
    "accountant",
    "lawyer",
]


def text_signals(item):

    text = (
        item.get("title", "")
        + " "
        + item.get("description", "")
    ).lower()

    field_score = sum(
        1
        for term in STRONG_FIELD_TERMS
        if term in text
    )

    opportunity_score = sum(
        1
        for term in OPPORTUNITY_TERMS
        if term in text
    )

    bad_score = sum(
        1
        for term in BAD_TERMS
        if term in text
    )

    current_score = 0

    if str(CURRENT_YEAR) in text:
        current_score += 15

    if str(NEXT_YEAR) in text:
        current_score += 12

    if "apply" in text:
        current_score += 5

    if "application" in text:
        current_score += 5

    return (
        field_score,
        opportunity_score,
        bad_score,
        current_score,
    )


# ============================================================
# PRELIMINARY RANKING
# ============================================================

def preliminary_score(item):

    field_score, opportunity_score, bad_score, current_score = (
        text_signals(item)
    )

    score = 0

    score += min(
        field_score * 12,
        48
    )

    score += min(
        opportunity_score * 6,
        24
    )

    score += current_score

    score += domain_quality(
        item.get(
            "url",
            ""
        )
    )

    score -= bad_score * 20

    if is_aggregator(
        item.get(
            "url",
            ""
        )
    ):
        score -= 8

    if is_bad_path(
        item.get(
            "url",
            ""
        )
    ):
        score -= 25

    if has_bad_title(
        item.get(
            "title",
            ""
        )
    ):
        score -= 30

    return score


def select_candidates(results):

    scored = []

    for item in results:

        url = item.get(
            "url",
            ""
        )

        title = item.get(
            "title",
            ""
        )

        # Reject obvious article/story pages
        if is_bad_path(url):
            continue

        if has_bad_title(title):
            continue

        score = preliminary_score(
            item
        )

        if score < 12:
            continue

        item = item.copy()

        item["preliminary_score"] = score

        item["domain"] = get_domain(
            url
        )

        scored.append(item)

    scored.sort(
        key=lambda x: x.get(
            "preliminary_score",
            0
        ),
        reverse=True,
    )

    return scored[
        :MAX_VERIFY_CANDIDATES
    ]


# ============================================================
# PAGE VERIFICATION
# ============================================================

def extract_page_data(url):

    try:

        response = requests.get(
            url,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=True,
        )

        if response.status_code >= 400:
            return None

        final_url = normalize_url(
            response.url
        )

        if not final_url:
            return None

        # Don't follow redirects into social/Google pages
        if is_google_news_url(
            final_url
        ):
            return None

        if is_social_url(
            final_url
        ):
            return None

        html = response.text

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        for tag in soup(
            [
                "script",
                "style",
                "noscript",
                "svg",
            ]
        ):
            tag.decompose()

        title = clean_text(
            soup.title.get_text()
            if soup.title
            else ""
        )

        body = clean_text(
            soup.get_text(
                " ",
                strip=True,
            )
        )

        if len(body) < 250:
            return None

        body_excerpt = body[:12000]

        application_links = []

        for a in soup.find_all(
            "a",
            href=True
        ):

            text = clean_text(
                a.get_text(
                    " ",
                    strip=True
                )
            ).lower()

            href = a.get(
                "href",
                ""
            ).strip()

            if not href:
                continue

            absolute = urljoin(
                final_url,
                href
            )

            if not absolute.startswith(
                ("http://", "https://")
            ):
                continue

            application_signal = any(
                word in text
                for word in [
                    "apply",
                    "application",
                    "register",
                    "registration",
                    "apply now",
                    "submit",
                    "how to apply",
                ]
            )

            if application_signal:

                application_links.append(
                    absolute
                )

        application_links = list(
            dict.fromkeys(
                application_links
            )
        )[:5]

        return {
            "final_url": final_url,
            "page_title": title,
            "page_text": body_excerpt,
            "application_links":
                application_links,
        }

    except Exception:

        return None


# ============================================================
# DATE / EXPIRY SIGNALS
# ============================================================

MONTHS = {
    "jan": 1,
    "january": 1,
    "feb": 2,
    "february": 2,
    "mar": 3,
    "march": 3,
    "apr": 4,
    "april": 4,
    "may": 5,
    "jun": 6,
    "june": 6,
    "jul": 7,
    "july": 7,
    "aug": 8,
    "august": 8,
    "sep": 9,
    "september": 9,
    "oct": 10,
    "october": 10,
    "nov": 11,
    "november": 11,
    "dec": 12,
    "december": 12,
}


def find_date_strings(text):

    if not text:
        return []

    pattern = (
        rf"(?:jan(?:uary)?|feb(?:ruary)?|"
        rf"mar(?:ch)?|apr(?:il)?|may|"
        rf"jun(?:e)?|jul(?:y)?|aug(?:ust)?|"
        rf"sep(?:tember)?|oct(?:ober)?|"
        rf"nov(?:ember)?|dec(?:ember)?)"
        rf"\s+\d{{1,2}},?\s+\d{{4}}"
        rf"|"
        rf"\d{{1,2}}\s+"
        rf"(?:jan(?:uary)?|feb(?:ruary)?|"
        rf"mar(?:ch)?|apr(?:il)?|may|"
        rf"jun(?:e)?|jul(?:y)?|aug(?:ust)?|"
        rf"sep(?:tember)?|oct(?:ober)?|"
        rf"nov(?:ember)?|dec(?:ember)?)"
        rf"\s+\d{{4}}"
    )

    try:

        return list(
            dict.fromkeys(
                re.findall(
                    pattern,
                    text,
                    flags=re.IGNORECASE,
                )
            )
        )[:20]

    except Exception:

        return []


def parse_date_string(value):

    value = clean_text(
        value
    ).lower()

    value = value.replace(
        ",",
        ""
    )

    patterns = [
        "%B %d %Y",
        "%b %d %Y",
        "%d %B %Y",
        "%d %b %Y",
    ]

    for pattern in patterns:

        try:

            return datetime.strptime(
                value,
                pattern
            ).date()

        except ValueError:
            continue

    return None


def find_deadline_hints(text):

    if not text:
        return []

    matches = []

    # Dates near deadline/application language
    deadline_patterns = [
        rf"(?:deadline|apply by|applications? close|"
        rf"application deadline|closing date).{{0,100}}"
        rf"({MONTHS_PATTERN if False else MONTH_PATTERN}\s+\d{{1,2}},?\s+\d{{4}})",
        rf"({MONTH_PATTERN}\s+\d{{1,2}},?\s+\d{{4}})"
    ]

    for pattern in deadline_patterns:

        try:

            found = re.findall(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if found:

                if isinstance(
                    found[0],
                    tuple
                ):
                    found = [
                        x[0]
                        for x in found
                    ]

                matches.extend(
                    found
                )

        except Exception:
            pass

    # Fallback: collect all recognizable dates
    if not matches:

        matches = find_date_strings(
            text
        )

    cleaned = []

    for value in matches:

        value = clean_text(
            value
        )

        if value and value not in cleaned:

            cleaned.append(
                value
            )

    return cleaned[:10]


# Keep this separate because it is used by the
# deadline parser above.
MONTH_PATTERN = (
    r"(?:jan(?:uary)?|feb(?:ruary)?|"
    r"mar(?:ch)?|apr(?:il)?|may|"
    r"jun(?:e)?|jul(?:y)?|aug(?:ust)?|"
    r"sep(?:tember)?|oct(?:ober)?|"
    r"nov(?:ember)?|dec(?:ember)?)"
)


def contains_expired_deadline(text):

    dates = find_date_strings(
        text
    )

    for value in dates:

        parsed = parse_date_string(
            value
        )

        if not parsed:
            continue

        # Clearly old dates
        if parsed.year < CURRENT_YEAR:
            return True

        # Current year but already passed
        if (
            parsed.year == CURRENT_YEAR
            and parsed < TODAY
        ):
            # Only treat as expiry when the surrounding
            # text strongly suggests it is a deadline.
            lower = text.lower()

            deadline_words = [
                "deadline",
                "apply by",
                "applications close",
                "application closes",
                "closing date",
                "last date",
            ]

            if any(
                word in lower
                for word in deadline_words
            ):
                return True

    return False


# ============================================================
# PAGE VERIFICATION
# ============================================================

def verify_page(item):

    data = extract_page_data(
        item.get(
            "url",
            ""
        )
    )

    if not data:
        return None

    page_title = data.get(
        "page_title",
        ""
    )

    page_text = data.get(
        "page_text",
        ""
    )

    # Reject obvious story/news pages
    if is_bad_path(
        data.get(
            "final_url",
            ""
        )
    ):
        return None

    if has_bad_title(
        page_title
    ):
        return None

    combined_text = (
        item.get("title", "")
        + " "
        + item.get("description", "")
        + " "
        + page_title
        + " "
        + page_text
    ).lower()

    field_score = sum(
        1
        for term in STRONG_FIELD_TERMS
        if term in combined_text
    )

    opportunity_score = sum(
        1
        for term in OPPORTUNITY_TERMS
        if term in combined_text
    )

    bad_score = sum(
        1
        for term in BAD_TERMS
        if term in combined_text
    )

    if opportunity_score == 0:
        return None

    if (
        bad_score >= 2
        and field_score == 0
    ):
        return None

    broad_opportunity = any(
        term in combined_text
        for term in [
            "scholarship",
            "fellowship",
            "youth program",
            "student program",
            "hackathon",
            "competition",
        ]
    )

    if (
        field_score == 0
        and not broad_opportunity
    ):
        return None

    application_links = data.get(
        "application_links",
        []
    )

    # --------------------------------------------------------
    # Expiry filter
    # --------------------------------------------------------

    if contains_expired_deadline(
        combined_text
    ):

        # Allow it through only when the page clearly
        # contains a future cycle as well.
        has_future_signal = (
            str(NEXT_YEAR) in combined_text
        )

        if not has_future_signal:
            return None

    deadline_hints = find_deadline_hints(
        combined_text
    )

    verified = item.copy()

    verified["url"] = data.get(
        "final_url",
        item.get(
            "url",
            ""
        )
    )

    verified["page_title"] = page_title

    verified["page_text"] = page_text

    # Important: main.py / AI can use the richer
    # page content instead of the short RSS snippet.
    verified["snippet"] = (
        page_text[:9000]
        if page_text
        else item.get(
            "description",
            ""
        )
    )

    verified["application_links"] = (
        application_links
    )

    verified["deadline_hints"] = (
        deadline_hints
    )

    verified["field_signal"] = (
        field_score
    )

    verified["opportunity_signal"] = (
        opportunity_score
    )

    verified["official_score"] = (
        domain_quality(
            verified["url"]
        )
    )

    verified["has_application_link"] = (
        len(application_links) > 0
    )

    return verified


# ============================================================
# PARALLEL PAGE VERIFICATION
# ============================================================

def verify_pages(candidates):

    verified = []

    print(
        f"\nVerifying {len(candidates)} "
        f"candidate pages with "
        f"{VERIFY_WORKERS} workers..."
    )

    with ThreadPoolExecutor(
        max_workers=VERIFY_WORKERS
    ) as executor:

        futures = {
            executor.submit(
                verify_page,
                item,
            ): item
            for item in candidates
        }

        for future in as_completed(
            futures
        ):

            try:

                result = future.result()

                if result:
                    verified.append(
                        result
                    )

            except Exception:
                pass

    verified.sort(
        key=lambda x: (
            x.get(
                "has_application_link",
                False
            ),
            x.get(
                "official_score",
                0
            ),
            x.get(
                "field_signal",
                0
            ),
            x.get(
                "opportunity_signal",
                0
            ),
            x.get(
                "preliminary_score",
                0
            ),
        ),
        reverse=True,
    )

    return verified


# ============================================================
# FINAL PRE-AI SELECTION
# ============================================================

def prepare_for_ai(results):

    final = []

    seen = set()

    for item in results:

        url = item.get(
            "url",
            ""
        )

        if not url or url in seen:
            continue

        seen.add(url)

        text = (
            item.get("title", "")
            + " "
            + item.get("description", "")
            + " "
            + item.get("page_text", "")
        ).lower()

        # Reject obvious news/story pages one more time
        if is_bad_path(url):
            continue

        if has_bad_title(
            item.get(
                "page_title",
                item.get(
                    "title",
                    ""
                )
            )
        ):
            continue

        # Strong source criteria
        has_field = (
            item.get(
                "field_signal",
                0
            ) >= 2
        )

        has_application = (
            len(
                item.get(
                    "application_links",
                    []
                )
            ) > 0
        )

        is_official = (
            item.get(
                "official_score",
                0
            ) >= 30
        )

        has_current_year = (
            str(CURRENT_YEAR)
            in text
        )

        has_next_year = (
            str(NEXT_YEAR)
            in text
        )

        # Candidate must satisfy at least one strong
        # source-quality condition.
        strong = (
            has_field
            or has_application
            or is_official
            or has_current_year
            or has_next_year
        )

        if not strong:
            continue

        # Aggregators must have an actual application link
        if is_aggregator(url):

            if not has_application:
                continue

        # News-like pages need a direct application link
        if (
            (
                "/news/" in get_path(url)
                or "/story/" in get_path(url)
                or "/article/" in get_path(url)
            )
            and not has_application
        ):
            continue

        final.append(item)

    final.sort(
        key=lambda x: (
            x.get(
                "has_application_link",
                False
            ),
            x.get(
                "official_score",
                0
            ),
            x.get(
                "field_signal",
                0
            ),
            x.get(
                "opportunity_signal",
                0
            ),
            x.get(
                "preliminary_score",
                0
            ),
        ),
        reverse=True,
    )

    return final[
        :MAX_AI_CANDIDATES
    ]


# ============================================================
# MAIN COLLECTOR
# ============================================================

def collect_opportunities():

    start_time = time.time()

    print("\n" + "=" * 70)
    print(
        "🌊 OCG OPPORTUNITY RADAR - "
        "SOURCE COLLECTOR V5"
    )
    print("=" * 70)

    print(
        f"Current date: {TODAY}"
    )

    # --------------------------------------------------------
    # STEP 1
    # --------------------------------------------------------

    raw_results = (
        collect_google_news_results()
    )

    print(
        f"\nRaw Google News results: "
        f"{len(raw_results)}"
    )

    if not raw_results:
        return []

    # --------------------------------------------------------
    # STEP 2
    # --------------------------------------------------------

    decoded_results = decode_results(
        raw_results
    )

    print(
        f"Decoded publisher URLs: "
        f"{len(decoded_results)}"
    )

    # --------------------------------------------------------
    # STEP 3
    # --------------------------------------------------------

    unique_results = (
        deduplicate_results(
            decoded_results
        )
    )

    print(
        f"Unique publisher pages: "
        f"{len(unique_results)}"
    )

    # --------------------------------------------------------
    # STEP 4
    # --------------------------------------------------------

    candidates = select_candidates(
        unique_results
    )

    print(
        f"Preliminary candidates: "
        f"{len(candidates)}"
    )

    # --------------------------------------------------------
    # STEP 5
    # --------------------------------------------------------

    verified = verify_pages(
        candidates
    )

    print(
        f"Verified opportunity pages: "
        f"{len(verified)}"
    )

    # --------------------------------------------------------
    # STEP 6
    # --------------------------------------------------------

    final_candidates = (
        prepare_for_ai(
            verified
        )
    )

    print(
        f"Candidates sent to AI: "
        f"{len(final_candidates)}"
    )

    # --------------------------------------------------------
    # PRINT FINAL CANDIDATES
    # --------------------------------------------------------

    print("\n" + "-" * 70)
    print("FINAL SOURCE CANDIDATES")
    print("-" * 70)

    for i, item in enumerate(
        final_candidates,
        start=1,
    ):

        print(
            f"\n{i}. "
            f"{item.get('title', '')}"
        )

        print(
            f"   URL: "
            f"{item.get('url', '')}"
        )

        print(
            f"   Domain: "
            f"{item.get('domain', get_domain(item.get('url', '')))}"
        )

        print(
            f"   Field signal: "
            f"{item.get('field_signal', 0)}"
        )

        print(
            f"   Official score: "
            f"{item.get('official_score', 0)}"
        )

        print(
            f"   Application link: "
            f"{item.get('has_application_link', False)}"
        )

        if item.get(
            "deadline_hints"
        ):

            print(
                f"   Deadline hints: "
                f"{item.get('deadline_hints')[:3]}"
            )

    elapsed = (
        time.time()
        - start_time
    )

    print("\n" + "=" * 70)

    print(
        f"Collection completed in "
        f"{elapsed / 60:.2f} minutes"
    )

    print("=" * 70)

    return final_candidates


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    results = (
        collect_opportunities()
    )

    print(
        f"\nReturned "
        f"{len(results)} candidates."
    )

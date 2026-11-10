"""Collect Mongabay Indonesia articles through the site's public WordPress API.

Articles are published under CC BY-ND 4.0. Full text stays in data/raw (git-ignored);
only article URLs and extracted facts are ever published.

Every downloaded page is cached, so an interrupted run resumes where it stopped.
"""
import json
import re
import time
from collections import Counter
from pathlib import Path

import requests
from bs4 import BeautifulSoup

API = "https://mongabay.co.id/wp-json/wp/v2/posts"
# WordPress search matches any text containing the term, so searching exactly the species
# words used by the candidate filter guarantees every article the filter could keep is fetched.
TERMS = ["harimau", "macan", "gajah", "buaya", "beruang"]
AFTER, BEFORE = "2015-01-01T00:00:00", "2026-01-01T00:00:00"
HEADERS = {"User-Agent": "sumatera-hwc-risk student research (laksa.fyansen@gmail.com)"}
PER_PAGE = 50            # smaller responses are less likely to be cut off mid-transfer
DELAY_SECONDS = 3
MAX_ATTEMPTS = 4

CACHE_DIR = Path("data/raw/mongabay_pages")        # one JSON file per API page, git-ignored
RAW = Path("data/raw/articles.jsonl")
CANDIDATES = Path("data/interim/candidates.jsonl")
REJECTED = Path("data/interim/rejected.jsonl")     # kept so you can audit the filter later

SPECIES = re.compile(r"\b(harimau|macan|gajah|buaya|beruang)\b", re.I)
CONFLICT = re.compile(
    r"\b(konflik|serang|menyerang|diserang|terkam|diterkam|menerkam|mangsa|dimangsa|memangsa|"
    r"gigit|digigit|tewas|luka|ternak|sapi|kambing|kerbau|kebun|ladang|sawit|tanaman|"
    r"permukiman|pemukiman|perangkap|kerangkeng|halau|menghalau|usir|mengusir|jerat)\w*", re.I)


def is_candidate(title: str, text: str) -> bool:
    blob = f"{title}\n{text}"
    return bool(SPECIES.search(blob)) and len(CONFLICT.findall(blob)) >= 2


def clean_html(rendered: str) -> str:
    soup = BeautifulSoup(rendered, "html.parser")
    for tag in soup(["script", "style", "figure", "figcaption"]):
        tag.decompose()                                  # photo captions add noise, not facts
    text = soup.get_text("\n")
    text = text.replace("\u2028", "\n").replace("\u2029", "\n")   # rare Unicode line breaks
    return re.sub(r"\n\s*\n+", "\n\n", text).strip()


def get_page(term: str, page: int, session: requests.Session) -> dict:
    """Return {'total_pages', 'posts'} for one API page, from cache or with retries."""
    path = CACHE_DIR / f"{term.replace(' ', '_')}_{page:03d}.json"
    if path.exists():
        return json.loads(path.read_text())
    params = {"search": term, "per_page": PER_PAGE, "page": page, "after": AFTER,
              "before": BEFORE, "orderby": "date", "order": "asc",
              "_fields": "id,date,link,title,content"}
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            resp = session.get(API, params=params, headers=HEADERS, timeout=60)
            if resp.status_code in (429, 500, 502, 503, 504):
                raise requests.HTTPError(f"HTTP {resp.status_code}")
            resp.raise_for_status()
            data = {"total_pages": int(resp.headers.get("X-WP-TotalPages", 1)), "posts": resp.json()}
            path.write_text(json.dumps(data, ensure_ascii=False))
            time.sleep(DELAY_SECONDS)
            return data
        except (requests.RequestException, ValueError) as exc:
            wait = 10 * 2 ** (attempt - 1)               # 10, 20, 40, 80 seconds
            print(f"  attempt {attempt} failed ({type(exc).__name__}), waiting {wait}s")
            time.sleep(wait)
    raise RuntimeError(f"Gave up on '{term}' page {page}. Rerun later; finished pages are cached.")


def fetch_term(term: str, session: requests.Session):
    page, total_pages = 1, 1
    while page <= total_pages:
        data = get_page(term, page, session)
        total_pages = data["total_pages"]
        print(f"  '{term}' page {page}/{total_pages}")
        yield from data["posts"]
        page += 1


def main():
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    CANDIDATES.parent.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    articles = {}
    for term in TERMS:
        print(f"Searching '{term}'")
        for post in fetch_term(term, session):
            if post["id"] in articles:                   # same article found by another term
                articles[post["id"]]["terms"].append(term)
                continue
            articles[post["id"]] = {
                "id": post["id"], "site": "mongabay", "url": post["link"],
                "title": clean_html(post["title"]["rendered"]),
                "pub_date": post["date"][:10],
                "text": clean_html(post["content"]["rendered"]),
                "terms": [term]}

    kept = 0
    with RAW.open("w") as raw, CANDIDATES.open("w") as cand, REJECTED.open("w") as rej:
        for art in articles.values():
            line = json.dumps(art, ensure_ascii=False) + "\n"
            raw.write(line)
            if is_candidate(art["title"], art["text"]):
                cand.write(line)
                kept += 1
            else:
                rej.write(line)

    years = Counter(a["pub_date"][:4] for a in articles.values())
    print(f"\n{len(articles)} unique articles, {kept} kept as candidates")
    print("Articles per year:", dict(sorted(years.items())))


if __name__ == "__main__":
    main()

"""Collect Mongabay Indonesia articles through the site's public WordPress API.

Articles are published under CC BY-ND 4.0. Full text stays in data/raw (git-ignored);
only article URLs and extracted facts are ever published.
"""
import json
import re
import time
from collections import Counter
from pathlib import Path

import requests
from bs4 import BeautifulSoup

API = "https://mongabay.co.id/wp-json/wp/v2/posts"
TERMS = ["harimau", "gajah", "buaya", "beruang madu", "konflik satwa", "konflik manusia"]
AFTER, BEFORE = "2015-01-01T00:00:00", "2026-01-01T00:00:00"
HEADERS = {"User-Agent": "sumatera-hwc-risk student research (laksa.fyansen@gmail.com)"}
DELAY_SECONDS = 3

RAW = Path("data/raw/articles.jsonl")              
CANDIDATES = Path("data/interim/candidates.jsonl")
REJECTED = Path("data/interim/rejected.jsonl")     

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
        tag.decompose()                                  
    text = soup.get_text("\n")
    return re.sub(r"\n\s*\n+", "\n\n", text).strip()


def fetch_term(term: str, session: requests.Session):
    """Yield every post matching one search term, page by page."""
    page, total_pages = 1, 1
    while page <= total_pages:
        params = {"search": term, "per_page": 100, "page": page, "after": AFTER,
                  "before": BEFORE, "orderby": "date", "order": "asc",
                  "_fields": "id,date,link,title,content"}
        resp = session.get(API, params=params, headers=HEADERS, timeout=60)
        time.sleep(DELAY_SECONDS)
        if resp.status_code != 200:
            print(f"  stopped at page {page}: HTTP {resp.status_code}")
            break
        total_pages = int(resp.headers.get("X-WP-TotalPages", 1))
        print(f"  '{term}' page {page}/{total_pages}")
        yield from resp.json()
        page += 1


def main():
    RAW.parent.mkdir(parents=True, exist_ok=True)
    CANDIDATES.parent.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    articles = {}
    for term in TERMS:
        print(f"Searching '{term}'")
        for post in fetch_term(term, session):
            if post["id"] in articles:                   
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

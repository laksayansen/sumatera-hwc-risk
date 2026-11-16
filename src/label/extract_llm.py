"""Turn articles into structured conflict events with an LLM, following labels/codebook.md.

Every response is cached with its prompt version, so reruns cost nothing and old prompt
versions stay comparable. Failed calls are retried on the next run.

Examples:
  python src/label/extract_llm.py data/interim/gold_articles.jsonl --split dev --limit 3
  python src/label/extract_llm.py data/interim/gold_articles.jsonl --split dev
  python src/label/extract_llm.py data/interim/candidates.jsonl
"""
import argparse
import csv
import json
import os
import re
import time
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from config import PROMPT_VERSION

load_dotenv()
MODEL = "claude-haiku-5-5"
CACHE = Path("data/interim/llm_cache.jsonl")
GOLD = Path("labels/gold_labels.csv")
MAX_CHARS = 15000          # Mongabay features are long; incidents can appear late
MAX_ATTEMPTS = 4

SYSTEM = """You extract human-wildlife conflict events from Indonesian news articles for a
research dataset. Apply every rule below exactly. When unsure, follow the rule literally.

WHAT AN EVENT IS
An event is one negative encounter between people and a wild animal at one place within a
short period, reported as having actually happened. It must involve one of exactly four
species: tiger (harimau sumatera, also called datuk), elephant (gajah), crocodile (buaya),
sun bear (beruang madu). No other species ever creates an event.

event_type is one of:
- human_attack: a person injured or killed by the animal
- animal_harmed: the animal killed, injured, or snared in a conflict setting
- livestock: livestock attacked or eaten
- property_damage: houses, huts, or fences damaged
- crop_damage: crops or plantation trees damaged
- incursion_response: the animal entered a village or farm, posed a threat to people,
  livestock, or crops, AND authorities or residents responded (team sent, trap set,
  animal driven away or captured)
If one incident has several types, use the first in this order: human_attack,
animal_harmed, livestock, property_damage, crop_damage, incursion_response.

THE THREE-PART TEST. Create an event only if the article gives ALL of:
(a) the species, (b) a place at regency (kabupaten/kota) level or finer, and
(c) a date at month level or finer. If any part is missing, do not create the event.

SCOPE
- Only events in Sumatra: Aceh, Sumatera Utara, Sumatera Barat, Riau, Kepulauan Riau,
  Jambi, Bengkulu, Sumatera Selatan, Kepulauan Bangka Belitung, Lampung. Skip all others.
- Location comes from where the event happened, never from the outlet or the agency name
  ("BKSDA Bengkulu" also covers Lampung).
- A named park or reserve that spans several regencies does not satisfy the place test
  unless the article also names the regency.

EXCLUDE
- Rescues or handovers of animals found near homes when no threat to people, livestock,
  or crops is described
- Pet trade, seizures, trafficking, and poaching for trade. If the article says the animal
  was snared or killed to be sold, exclude it even if the snare was in a plantation.
- Releases or translocations with no incident; zoo or captive animals
- Population surveys, camera-trap sightings, tracks with no threat or response
- Policy, awareness, opinion, or species-profile pieces with no specific incident
- Year-end or multi-year statistics: set aggregate_only to true if the article only
  reports totals, and create no events from the totals
- Attacks blamed on a focal species only by residents' guesses, with no witness or evidence
- Titles of related-article links ("Baca:", "Baca juga:") are not part of the article

SPECIAL RULES
- Snares count as animal_harmed only when linked to protecting crops or livestock (for
  example jerat babi, wild boar snares) or when the snaring happened in a farm, garden, or
  plantation. Snares set by hunters (jerat pemburu) in forest are poaching: exclude.
- Live capture without injury (box trap, net, residents catching the animal) is
  incursion_response. animal_harmed needs injury or death.
- Deaths: label animal_harmed when the article reports physical evidence of a human-made
  cause at the scene (animal entangled in wire or a snare, poisoned bait with the carcass,
  gunshot wounds), even if officials say "diduga". If the cause is only speculated or shown
  only by symptoms, do NOT create an event; list it under death_unknown instead.
- Darting, trapping, or patrols within 14 days of an incident in the same place belong to
  that incident. A capture or evacuation on a later date is its own incursion_response event.
- An ongoing incident in one place that spans more than one calendar month is one event
  per month affected.
- Separate places or separate dates are separate events. One herd raiding the same village
  for several days within one month is one event.
- Photo captions are part of the article. If a caption and the body disagree on a date,
  use the body.

DATES
- Use the incident date. Convert relative dates such as "Kamis (12/5)", "kemarin", or
  "pekan lalu" using the publication date.
- If a news report describes an incident as current but gives no date, use the
  publication date and set date_precision to "publication".
- If only the month is known, use the 1st of that month and set date_precision to "month".
- Vague phrases that do not pin down a month ("beberapa bulan lalu", "tahun lalu") fail
  the date test.

WORDS THAT ARE NOT FOCAL SPECIES
harimau dahan (clouded leopard), macan tutul (leopard), kebun binatang (zoo), and species
words inside place names (Desa Gajah Mati, Barak Gajah) are not focal animals.

LOCATION FIELDS
Copy names as the article gives them. kabupaten is the regency name without "Kabupaten";
write cities as "Kota X". Use null when a level is not named. province is always required
for an event.

Return ONLY one JSON object, with no other text:
{"aggregate_only": bool,
 "events": [{"event_type": str, "species": "tiger"|"elephant"|"crocodile"|"sun_bear",
             "desa": str|null, "kecamatan": str|null, "kabupaten": str|null,
             "province": str, "incident_date": "YYYY-MM-DD",
             "date_precision": "day"|"month"|"publication", "evidence": str}],
 "death_unknown": [{"species": str, "kabupaten": str|null, "province": str|null,
                    "incident_date": str|null}],
 "notes": str}
"evidence" is one short sentence in English saying which facts in the article support the
event. "notes" is at most two sentences explaining what you excluded and why."""


def parse_json(text: str) -> dict:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    start, end = text.find("{"), text.rfind("}")
    return json.loads(text[start:end + 1] if start >= 0 else text)


def call_llm(client, article: dict) -> dict:
    user = (f"Publication date: {article['pub_date']}\nTitle: {article['title']}\n\n"
            f"{article['text'][:MAX_CHARS]}")
    last_error = None
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            resp = client.messages.create(model=MODEL, max_tokens=2000, system=SYSTEM,
                                          messages=[{"role": "user", "content": user}])
            raw = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
            usage = getattr(resp, "usage", None)
            tokens = {"input_tokens": getattr(usage, "input_tokens", None),
                      "output_tokens": getattr(usage, "output_tokens", None)}
            try:
                return {"parsed": parse_json(raw), "raw": raw, "error": None, **tokens}
            except (json.JSONDecodeError, ValueError) as exc:
                return {"parsed": None, "raw": raw, "error": f"parse: {exc}", **tokens}
        except Exception as exc:                      # network, rate limit, server errors
            last_error = f"{type(exc).__name__}: {exc}"
            wait = 10 * 2 ** (attempt - 1)
            print(f"  attempt {attempt} failed ({type(exc).__name__}), waiting {wait}s")
            time.sleep(wait)
    return {"parsed": None, "raw": "", "error": f"api: {last_error}",
            "input_tokens": None, "output_tokens": None}


def split_urls(split: str) -> set[str]:
    with GOLD.open() as f:
        return {row["url"] for row in csv.DictReader(f) if row["split"] == split}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("--split", choices=["dev", "holdout"], help="only gold articles in this split")
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()

    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    done = set()
    if CACHE.exists():
        with CACHE.open() as f:
            for line in f:
                rec = json.loads(line)
                if rec["prompt_version"] == PROMPT_VERSION and rec["parsed"] is not None:
                    done.add(rec["url"])

    with open(args.input) as f:
        articles = [json.loads(line) for line in f]
    if args.split:
        keep = split_urls(args.split)
        articles = [a for a in articles if a["url"] in keep]
    pending = [a for a in articles if a["url"] not in done]
    todo = pending[:args.limit]
    print(f"{len(articles)} articles selected, {len(articles) - len(pending)} already cached, "
          f"{len(todo)} to extract now with prompt {PROMPT_VERSION}")

    CACHE.parent.mkdir(parents=True, exist_ok=True)
    with CACHE.open("a") as out:
        for i, art in enumerate(todo, 1):
            result = call_llm(client, art)
            out.write(json.dumps({"url": art["url"], "prompt_version": PROMPT_VERSION,
                                  "model": MODEL, **result}, ensure_ascii=False) + "\n")
            out.flush()
            if result["error"]:
                print(f"  {art['url']}: {result['error'][:120]}")
            if i % 10 == 0 or i == len(todo):
                print(f"{i}/{len(todo)} extracted")


if __name__ == "__main__":
    main()

"""Rebuild data/interim/gold_articles.jsonl from data/raw/articles.jsonl.

Run this after the collector changes how article text is stored (for example, adding
photo captions), so the gold articles the extractor reads match the current collector.
Every URL in labels/gold_labels.csv must be found, or nothing is written.
"""
import csv
import json
from pathlib import Path

RAW = Path("data/raw/articles.jsonl")
GOLD = Path("labels/gold_labels.csv")
OUT = Path("data/interim/gold_articles.jsonl")

with RAW.open() as f:
    by_url = {rec["url"]: rec for rec in map(json.loads, f)}
with GOLD.open() as f:
    urls = [row["url"] for row in csv.DictReader(f)]

missing = [u for u in urls if u not in by_url]
if missing:
    raise SystemExit(f"{len(missing)} gold URLs not found in {RAW}, nothing written:\n"
                     + "\n".join(missing[:10]))

with OUT.open("w") as out:
    for u in urls:
        out.write(json.dumps(by_url[u], ensure_ascii=False) + "\n")

with_captions = sum(1 for u in urls if by_url[u].get("captions"))
print(f"wrote {len(urls)} gold articles to {OUT}, {with_captions} with photo captions")

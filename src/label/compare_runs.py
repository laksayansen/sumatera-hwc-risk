"""Measure how much the extractor's output changes between two runs on the same articles.

The model has no temperature setting, so two runs of the same prompt can differ. Comparing
two runs shows how large a score difference must be before it means anything.

  python src/label/compare_runs.py v3 v3-r2
  python src/label/compare_runs.py v2 v3          # also works across prompt versions
"""
import argparse
import json
from pathlib import Path

import pandas as pd

from places import SUMATRA, norm_province, norm_regency

TYPES = {"human_attack", "animal_harmed", "livestock", "property_damage", "crop_damage",
         "incursion_response"}
SPECIES = {"tiger", "elephant", "crocodile", "sun_bear"}

ap = argparse.ArgumentParser()
ap.add_argument("run_a")
ap.add_argument("run_b")
ap.add_argument("--split", default="dev", choices=["dev", "holdout"])
args = ap.parse_args()

gold = pd.read_csv("labels/gold_labels.csv", dtype=str).fillna("")
gold = gold[gold["split"] == args.split]
titles = dict(zip(gold["url"], gold["title"]))

runs = {args.run_a: {}, args.run_b: {}}
with open("data/interim/llm_cache.jsonl") as f:
    for line in f:
        rec = json.loads(line)
        if rec["prompt_version"] in runs and rec["parsed"] is not None:
            runs[rec["prompt_version"]][rec["url"]] = rec["parsed"]


def cells(parsed):
    """The regency-month cells an extraction would mark positive in the panel."""
    if parsed.get("aggregate_only"):
        return set()
    return {(e.get("species"), norm_regency(e.get("kabupaten"))[0],
             str(e.get("incident_date", ""))[:7])
            for e in parsed.get("events") or []
            if e.get("event_type") in TYPES and e.get("species") in SPECIES
            and norm_province(e.get("province")) in SUMATRA}


both = [u for u in titles if u in runs[args.run_a] and u in runs[args.run_b]]
if not both:
    raise SystemExit(f"No {args.split} articles extracted in both {args.run_a} and {args.run_b}.")

event_agree, cell_agree, rows = 0, 0, []
for u in both:
    ca, cb = cells(runs[args.run_a][u]), cells(runs[args.run_b][u])
    same_event = bool(ca) == bool(cb)
    event_agree += same_event
    cell_agree += ca == cb
    if ca != cb:
        rows.append({"url": u, "title": titles[u],
                     "event_disagrees": not same_event,
                     args.run_a: " | ".join(sorted(map(" ".join, ca))),
                     args.run_b: " | ".join(sorted(map(" ".join, cb)))})

report = {"run_a": args.run_a, "run_b": args.run_b, "split": args.split,
          "articles_compared": len(both),
          "is_event_agreement": round(event_agree / len(both), 3),
          "is_event_disagreements": len(both) - event_agree,
          "identical_cells": round(cell_agree / len(both), 3),
          "articles_with_different_cells": len(both) - cell_agree}
Path("reports").mkdir(exist_ok=True)
stem = f"reports/run_agreement_{args.run_a}_vs_{args.run_b}_{args.split}"
Path(f"{stem}.json").write_text(json.dumps(report, indent=2))
pd.DataFrame(rows, columns=["url", "title", "event_disagrees", args.run_a, args.run_b]
             ).to_csv(f"{stem}.csv", index=False)
print(json.dumps(report, indent=2))
print(f"\n{len(rows)} articles with different output, listed in {stem}.csv")

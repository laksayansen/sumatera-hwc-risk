"""Score the LLM extractor against your gold labels.

Run on dev while improving the prompt. Run on holdout exactly once, at the very end:
  python src/label/evaluate_extraction.py                   # dev, current prompt version
  python src/label/evaluate_extraction.py --version v1      # re-score an older version
  python src/label/evaluate_extraction.py holdout           # once, final score
"""
import argparse
import json
from pathlib import Path

import pandas as pd

from config import PROMPT_VERSION
from places import SUMATRA, norm_province, norm_regency

ap = argparse.ArgumentParser()
ap.add_argument("split", nargs="?", default="dev", choices=["dev", "holdout"])
ap.add_argument("--version", default=PROMPT_VERSION, help="prompt version to score")
args = ap.parse_args()
SPLIT, VERSION = args.split, args.version

TYPES = {"human_attack", "animal_harmed", "livestock", "property_damage", "crop_damage",
         "incursion_response"}
SPECIES = {"tiger", "elephant", "crocodile", "sun_bear"}
PRICE_IN, PRICE_OUT = 0.10, 0.50          # US$ per million tokens, Claude Haiku 5.5

gold_all = pd.read_csv("labels/gold_labels.csv", dtype=str).fillna("")
gold = gold_all[gold_all["split"] == SPLIT].copy()
gold["is_event"] = gold["is_event"].astype(int)

# Keep the latest successful extraction per article; remember articles that only failed.
cache, failed = {}, {}
with open("data/interim/llm_cache.jsonl") as f:
    for line in f:
        rec = json.loads(line)
        if rec["prompt_version"] != VERSION:
            continue
        if rec["parsed"] is not None:
            cache[rec["url"]] = rec
        else:
            failed[rec["url"]] = rec
failed = {u: r for u, r in failed.items() if u not in cache}


def valid_events(url):
    """Events that pass the same scope rules you labeled with."""
    rec = cache.get(url)
    if not rec or rec["parsed"].get("aggregate_only"):
        return []
    return [e for e in rec["parsed"].get("events") or []
            if e.get("event_type") in TYPES and e.get("species") in SPECIES
            and norm_province(e.get("province")) in SUMATRA]


n_failed = sum(u in failed for u in gold["url"])
n_missing = sum(u not in cache and u not in failed for u in gold["url"])
if n_failed:
    print(f"NOTE: {n_failed} {SPLIT} articles failed extraction with prompt {VERSION} and "
          f"count as predicting no event. Rerun extract_llm.py to retry them.")
if n_missing:
    print(f"WARNING: {n_missing} {SPLIT} articles were never extracted with prompt {VERSION}. "
          f"Run extract_llm.py with --split {SPLIT} first.")

gold["pred_events"] = gold["url"].map(valid_events)
gold["pred_is_event"] = gold["pred_events"].map(lambda e: int(len(e) > 0))
tp = int(((gold.is_event == 1) & (gold.pred_is_event == 1)).sum())
fp = int(((gold.is_event == 0) & (gold.pred_is_event == 1)).sum())
fn = int(((gold.is_event == 1) & (gold.pred_is_event == 0)).sum())
tn = int(((gold.is_event == 0) & (gold.pred_is_event == 0)).sum())
precision = tp / (tp + fp) if tp + fp else float("nan")
recall = tp / (tp + fn) if tp + fn else float("nan")
f1 = 2 * precision * recall / (precision + recall) if tp else 0.0


def matches_main(e, g):
    return (e.get("event_type") == g.event_type
            and norm_regency(e.get("kabupaten"))[0] == norm_regency(g.kabupaten)[0]
            and str(e.get("incident_date", ""))[:7] == g.incident_date[:7])


# Field accuracy on true positives: does ANY predicted event match the gold main event?
fields = {"event_type": 0, "species": 0, "kabupaten": 0, "province": 0, "month": 0, "n_events": 0}
both = gold[(gold.is_event == 1) & (gold.pred_is_event == 1)]
for _, g in both.iterrows():
    evs = g.pred_events
    fields["event_type"] += any(e.get("event_type") == g.event_type for e in evs)
    fields["species"] += any(e.get("species") == g.species for e in evs)
    fields["kabupaten"] += any(norm_regency(e.get("kabupaten"))[0] == norm_regency(g.kabupaten)[0] for e in evs)
    fields["province"] += any(norm_province(e.get("province")) == norm_province(g.province) for e in evs)
    fields["month"] += any(str(e.get("incident_date", ""))[:7] == g.incident_date[:7] for e in evs)
    fields["n_events"] += len(evs) == int(g.n_events or 0)
field_acc = {k: round(v / len(both), 3) for k, v in fields.items()} if len(both) else {}


# Keyword-filter audit, from dev labels only, scaled to the full candidate and reject piles.
def count_lines(path):
    with open(path) as f:
        return sum(1 for _ in f)


dev = gold_all[gold_all["split"] == "dev"]
rates = dev.groupby("pool")["is_event"].apply(lambda s: s.astype(int).mean())
n_cand = count_lines("data/interim/candidates.jsonl")
n_rej = count_lines("data/interim/rejected.jsonl")
r_c, r_r = rates.get("candidate", 0.0), rates.get("rejected", 0.0)
filter_recall = (r_c * n_cand) / (r_c * n_cand + r_r * n_rej) if (r_c + r_r) else float("nan")

records = [cache.get(u) or failed.get(u) for u in gold["url"]]
tokens_in = sum((r or {}).get("input_tokens") or 0 for r in records)
tokens_out = sum((r or {}).get("output_tokens") or 0 for r in records)
cost = tokens_in / 1e6 * PRICE_IN + tokens_out / 1e6 * PRICE_OUT

report = {"prompt_version": VERSION, "split": SPLIT, "n_articles": len(gold),
          "n_gold_events_articles": int(gold.is_event.sum()), "n_failed": n_failed,
          "tp": tp, "fp": fp, "fn": fn, "tn": tn,
          "precision": round(precision, 3), "recall": round(recall, 3), "f1": round(f1, 3),
          "field_accuracy_on_tp": field_acc,
          "keyword_filter_recall_est": round(filter_recall, 3),
          "tokens_in": tokens_in, "tokens_out": tokens_out, "cost_usd": round(cost, 4)}
Path("reports").mkdir(exist_ok=True)
Path(f"reports/extraction_eval_{VERSION}_{SPLIT}.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))


# Error analysis file: read every row before changing the prompt.
def summarize(evs):
    return " | ".join(f"{e.get('event_type')} {e.get('species')} {e.get('kabupaten')} "
                      f"{e.get('incident_date')}" for e in evs)


rows = []
for _, g in gold.iterrows():
    parsed = (cache.get(g.url) or {}).get("parsed") or {}
    if g.url in failed:
        error = "extraction_failed"
    elif g.is_event == 0 and g.pred_is_event == 1:
        error = "false_positive"
    elif g.is_event == 1 and g.pred_is_event == 0:
        error = "false_negative"
    elif g.is_event == 1 and not any(matches_main(e, g) for e in g.pred_events):
        error = "field_mismatch"
    elif g.is_event == 1 and len(g.pred_events) != int(g.n_events or 0):
        error = "count_mismatch"
    else:
        continue
    rows.append({"url": g.url, "title": g.title, "error": error,
                 "gold": f"{g.event_type} {g.species} {g.kabupaten} {g.incident_date} n={g.n_events}",
                 "predicted": summarize(g.pred_events),
                 "llm_notes": parsed.get("notes", "") or (failed.get(g.url) or {}).get("error", ""),
                 "your_notes": g.notes})
out = Path(f"reports/extraction_errors_{VERSION}_{SPLIT}.csv")
pd.DataFrame(rows, columns=["url", "title", "error", "gold", "predicted", "llm_notes",
                            "your_notes"]).to_csv(out, index=False)
print(f"\n{len(rows)} articles to review in {out}")

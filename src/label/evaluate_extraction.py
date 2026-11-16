"""Score the LLM extractor against your gold labels.

Run on dev while improving the prompt. Run on holdout exactly once, at the very end:
  python src/label/evaluate_extraction.py            # dev
  python src/label/evaluate_extraction.py holdout    # once, final score
"""
import json
import sys
from pathlib import Path

import pandas as pd

from config import PROMPT_VERSION
from places import SUMATRA, norm_province, norm_regency

SPLIT = sys.argv[1] if len(sys.argv) > 1 else "dev"
TYPES = {"human_attack", "animal_harmed", "livestock", "property_damage", "crop_damage",
         "incursion_response"}
SPECIES = {"tiger", "elephant", "crocodile", "sun_bear"}
PRICE_IN, PRICE_OUT = 0.10, 0.50          # US$ per million tokens, Claude Haiku 5.5

gold_all = pd.read_csv("labels/gold_labels.csv", dtype=str).fillna("")
gold = gold_all[gold_all["split"] == SPLIT].copy()
gold["is_event"] = gold["is_event"].astype(int)

cache = {}
with open("data/interim/llm_cache.jsonl") as f:
    for line in f:
        rec = json.loads(line)
        if rec["prompt_version"] == PROMPT_VERSION and rec["parsed"] is not None:
            cache[rec["url"]] = rec


def valid_events(url):
    """Events that pass the same scope rules you labeled with."""
    rec = cache.get(url)
    if not rec or rec["parsed"].get("aggregate_only"):
        return []
    return [e for e in rec["parsed"].get("events") or []
            if e.get("event_type") in TYPES and e.get("species") in SPECIES
            and norm_province(e.get("province")) in SUMATRA]


missing = [u for u in gold["url"] if u not in cache]
if missing:
    print(f"WARNING: {len(missing)} {SPLIT} articles have no cached extraction for "
          f"prompt {PROMPT_VERSION}. Run extract_llm.py with --split {SPLIT} first.")

gold["pred_events"] = gold["url"].map(valid_events)
gold["pred_is_event"] = gold["pred_events"].map(lambda e: int(len(e) > 0))
tp = int(((gold.is_event == 1) & (gold.pred_is_event == 1)).sum())
fp = int(((gold.is_event == 0) & (gold.pred_is_event == 1)).sum())
fn = int(((gold.is_event == 1) & (gold.pred_is_event == 0)).sum())
tn = int(((gold.is_event == 0) & (gold.pred_is_event == 0)).sum())
precision = tp / (tp + fp) if tp + fp else float("nan")
recall = tp / (tp + fn) if tp + fn else float("nan")
f1 = 2 * precision * recall / (precision + recall) if tp else 0.0

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

tokens_in = sum(cache[u].get("input_tokens") or 0 for u in gold["url"] if u in cache)
tokens_out = sum(cache[u].get("output_tokens") or 0 for u in gold["url"] if u in cache)
cost = tokens_in / 1e6 * PRICE_IN + tokens_out / 1e6 * PRICE_OUT

report = {"prompt_version": PROMPT_VERSION, "split": SPLIT, "n_articles": len(gold),
          "tp": tp, "fp": fp, "fn": fn, "tn": tn,
          "precision": round(precision, 3), "recall": round(recall, 3), "f1": round(f1, 3),
          "field_accuracy_on_tp": field_acc,
          "keyword_filter_recall_est": round(filter_recall, 3),
          "tokens_in": tokens_in, "tokens_out": tokens_out, "cost_usd": round(cost, 4)}
Path("reports").mkdir(exist_ok=True)
Path(f"reports/extraction_eval_{PROMPT_VERSION}_{SPLIT}.json").write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))

# Error analysis file: read every row before changing the prompt.
def summarize(evs):
    return " | ".join(f"{e.get('event_type')} {e.get('species')} {e.get('kabupaten')} "
                      f"{e.get('incident_date')}" for e in evs)

rows = []
for _, g in gold.iterrows():
    rec = cache.get(g.url, {})
    parsed = rec.get("parsed") or {}
    wrong_label = g.is_event != g.pred_is_event
    wrong_fields = (g.is_event == 1 and g.pred_is_event == 1 and
                    not any(e.get("event_type") == g.event_type and
                            norm_regency(e.get("kabupaten"))[0] == norm_regency(g.kabupaten)[0] and
                            str(e.get("incident_date", ""))[:7] == g.incident_date[:7]
                            for e in g.pred_events))
    if wrong_label or wrong_fields:
        rows.append({"url": g.url, "title": g.title,
                     "error": "false_positive" if g.is_event == 0 and g.pred_is_event == 1
                     else "false_negative" if g.is_event == 1 and g.pred_is_event == 0
                     else "field_mismatch",
                     "gold": f"{g.event_type} {g.species} {g.kabupaten} {g.incident_date} n={g.n_events}",
                     "predicted": summarize(g.pred_events),
                     "llm_notes": parsed.get("notes", ""), "your_notes": g.notes})
out = Path(f"reports/extraction_errors_{PROMPT_VERSION}_{SPLIT}.csv")
pd.DataFrame(rows).to_csv(out, index=False)
print(f"\n{len(rows)} articles to review in {out}")

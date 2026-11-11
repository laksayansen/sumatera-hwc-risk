"""Replace a holdout that was seen during codebook development with 20 fresh, unseen articles.

The old holdout rows keep their labels and become dev rows. The new rows are appended
unlabeled. Label them yourself and never use them to write or change codebook rules.
"""
import json
import random
import shutil
from datetime import date
from pathlib import Path

import pandas as pd

random.seed(2026)
N_CANDIDATES, N_REJECTED = 16, 4          # same 80/20 mix as the original sample
GOLD = Path("labels/gold_labels.csv")
GOLD_TEXT = Path("data/interim/gold_articles.jsonl")


def load(path):
    with open(path) as f:
        return [json.loads(line) for line in f]


backup = GOLD.with_name(f"gold_labels_backup_{date.today()}.csv")
shutil.copy(GOLD, backup)                  # never risk hand labels without a copy

gold = pd.read_csv(GOLD, dtype=str).fillna("")
n_old_holdout = int((gold["split"] == "holdout").sum())
gold["split"] = "dev"

used = set(gold["url"])
cands = [r for r in load("data/interim/candidates.jsonl") if r["url"] not in used]
rejs = [r for r in load("data/interim/rejected.jsonl") if r["url"] not in used]
picked = [(r, "candidate") for r in random.sample(cands, N_CANDIDATES)] + \
         [(r, "rejected") for r in random.sample(rejs, N_REJECTED)]
random.shuffle(picked)

new_rows = pd.DataFrame([{"url": r["url"], "title": r["title"], "pub_date": r["pub_date"],
                          "pool": pool, "split": "holdout"} for r, pool in picked])
gold = pd.concat([gold, new_rows], ignore_index=True).fillna("")
gold.to_csv(GOLD, index=False)

with GOLD_TEXT.open("a") as out:
    for r, _ in picked:
        out.write(json.dumps(r, ensure_ascii=False) + "\n")

print(f"Backup saved to {backup}")
print(f"{n_old_holdout} old holdout rows moved to dev; {len(new_rows)} fresh holdout rows appended")
print(gold["split"].value_counts().to_string())

"""Draw the gold-label sample: mostly candidates, plus some rejects to audit the keyword filter."""
import json
import random
from pathlib import Path

import pandas as pd

random.seed(42)
N_CANDIDATES, N_REJECTED = 80, 20
OUT = Path("labels/gold_to_label.csv")


def load(path):
    with open(path) as f:
        return [json.loads(line) for line in f]


cands = random.sample(load("data/interim/candidates.jsonl"), N_CANDIDATES)
rejs = random.sample(load("data/interim/rejected.jsonl"), N_REJECTED)
rows = [{"url": r["url"], "title": r["title"], "pub_date": r["pub_date"], "pool": pool}
        for pool, group in [("candidate", cands), ("rejected", rejs)] for r in group]
random.shuffle(rows)  # so you cannot tell which pool an article came from while labeling

label_cols = ["is_event", "n_events", "event_type", "species", "kabupaten", "province",
              "incident_date", "notes"]
df = pd.DataFrame(rows)
# Lock away 20% as a holdout you never look at while tuning the prompt.
df["split"] = ["holdout" if i < len(df) * 0.2 else "dev" for i in range(len(df))]
for col in label_cols:
    df[col] = ""
OUT.parent.mkdir(exist_ok=True)
df.to_csv(OUT, index=False)
print(f"wrote {len(df)} rows to {OUT}")

# Also save the full text of the sampled articles so the extractor can run on exactly this set.
chosen = set(df["url"])
with open("data/interim/gold_articles.jsonl", "w") as out:
    for rec in cands + rejs:
        if rec["url"] in chosen:
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")

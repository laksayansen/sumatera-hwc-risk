"""Restore the Pasaman Barat dev label changed on 2026-11-16. See decisions.md #11.

On a full re-read, the article reports that after leaving the dam channel the tiger was
"masih berkeliaran disekitar pemukiman warga" (still roaming around residents' homes), that a
team checked residents' reports of tracks near Pinaga Aur Kuning, and that BKSDA told
residents to limit field work to 08.00 to 16.00. That meets incursion_response, so the
original label was right.
"""
import pandas as pd

GOLD = "labels/gold_labels.csv"
KEY = "harimau-sumatera-masuk-bendungan-di-pasaman-barat"
RESTORED = dict(
    is_event="1", n_events="3", event_type="incursion_response", species="tiger",
    kabupaten="Pasaman Barat", province="Sumatera Barat", incident_date="2024-03-23",
    notes=("Restored 2026-11-17 (decisions.md #11). Tiger fell into the PLTMH channel in Nagari "
           "Kajai, Pasaman Barat, on 23 Mar 2024, then roamed near settlements; BKSDA checked "
           "track reports near Pinaga Aur Kuning and told residents to limit field work. "
           "Two more events in Pasaman (not Pasaman Barat): Puti Malabin box-trapped "
           "2024-02-04 and livestock killed January 2024 (month only). The 2026-11-16 "
           "correction relied on an incomplete reading of the article"),
)

g = pd.read_csv(GOLD, dtype=str).fillna("")
rows = g["url"].str.contains(KEY, regex=False)
assert rows.sum() == 1, f"expected one row, found {rows.sum()}"
assert (g.loc[rows, "split"] == "dev").all(), "never edit holdout labels"
for col, val in RESTORED.items():
    g.loc[rows, col] = val
g.to_csv(GOLD, index=False, lineterminator="\r\n")   # keep Sheets line endings
print(g.loc[rows, ["split", "is_event", "n_events", "event_type", "kabupaten",
                   "incident_date"]].to_string())
print("dev event articles:", int((g[g.split == "dev"].is_event == "1").sum()))

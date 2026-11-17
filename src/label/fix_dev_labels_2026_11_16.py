"""Dev label corrections from the prompt v1 error analysis (2026-11-16). See decisions.md #10."""
import pandas as pd
g = pd.read_csv("labels/gold_labels.csv", dtype=str).fillna("")
fixes = {
    "kala-warga-tebo-berkonflik-lahan": dict(
        is_event="1", n_events="1", event_type="property_damage", species="elephant",
        kabupaten="Tebo", province="Jambi", incident_date="2022-11-06",
        notes="Corrected 2026-11-16 after v1 error analysis. Herd of 8 elephants destroyed huts and young oil palm in Muaro Sekalo on the nights of 6 and 7 Nov 2022 (adjacent huts, same herd, one event). Originally labeled 0 from the title. March 2022 entry has no damage or response, so no event"),
    "harimau-sumatera-masuk-bendungan-di-pasaman-barat": dict(
        is_event="1", n_events="2", event_type="incursion_response", species="tiger",
        kabupaten="Pasaman", province="Sumatera Barat", incident_date="2024-02-04",
        notes="Corrected 2026-11-16 after v1 error analysis. PLTMH dam tiger in Nagari Kajai, Pasaman Barat (2024-03-23) excluded under the infrastructure rule: no threat described and the tiger left on its own. Remaining events in Pasaman (not Pasaman Barat): Puti Malabin box-trapped 2024-02-04 and livestock killed January 2024 (month only)"),
}
for key, values in fixes.items():
    rows = g["url"].str.contains(key, regex=False)
    assert rows.sum() == 1, f"expected one row for {key}, found {rows.sum()}"
    assert (g.loc[rows, "split"] == "dev").all(), "never edit holdout labels"
    for col, val in values.items():
        g.loc[rows, col] = val
g.to_csv("labels/gold_labels.csv", index=False, lineterminator="\r\n")   # keep Sheets line endings
print(g[g["url"].str.contains("|".join(fixes), regex=True)][
    ["split", "is_event", "n_events", "event_type", "species", "kabupaten", "province", "incident_date"]].to_string())
print("dev event articles:", int((g[g.split == "dev"].is_event == "1").sum()))

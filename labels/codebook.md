# Conflict event codebook (v1, 2026-11-08)

An EVENT is one negative encounter between people and a wild animal at one place
within a short period, reported as having actually happened.

## Include (event_type)
1. human_attack       A person injured or killed by the animal
2. livestock          Livestock attacked or eaten
3. crop_damage        Crops or plantation trees damaged (e.g. elephants in oil palm)
4. property_damage    Houses, huts, or fences damaged
5. incursion_response Animal entered a village or farm, posed a threat to people,
                      livestock, or crops, AND authorities or residents responded
6. animal_harmed      Animal killed, injured, or snared in a conflict setting
                      (e.g. retaliation, snares set near farms)

## Exclude
- Rescues from the pet trade, seizures, poaching or trafficking cases
- Releases or translocations with no incident described
- Zoo or captive animals
- Population surveys, camera-trap sightings with no threat or response
- Policy, awareness, or opinion pieces with no specific incident
- Year-end statistics articles (mark as aggregate, do not turn into events)

## Species
tiger, elephant, crocodile, sun_bear, other (write the name)

## Location
Record the lowest level named: desa, kecamatan, kabupaten/kota, and province.
Province is required. Never infer location from which Antara site published it.

## Date
Use the incident date. Articles often write "Kamis (12/5)", so convert it using
the publication date. If no incident date is given, use the publication date and
set date_precision = publication.

## Multiple incidents
Separate places or separate dates become separate events.
One herd raiding the same village for several days is ONE event.

## Indonesian terms to watch for
- diterkam, menerkam: mauled or pounced on (usually tiger)
- dimangsa, memangsa: preyed on
- diserang, menyerang: attacked
- digigit: bitten (often crocodile)
- merusak kebun / tanaman: damaged gardens or crops (usually elephant)
- masuk permukiman: entered a settlement
- dihalau, diusir: driven away
- kandang jebak, perangkap: trap set by BKSDA
- jerat: snare
- beruang madu: sun bear
- buaya muara: estuarine crocodile

## Edge cases decided so far
- 2026-11-08 Rescues or handovers of an animal found near homes are excluded unless a threat
  to people, livestock, or crops is described (e.g. bekantan rescue in Samarinda).
- 2026-11-08 Events outside Sumatra are out of scope, even when published on a Sumatran
  Antara site, because Antara sites cross-post stories from other islands.
  - 2026-11-08 SPECIES SCOPE. Only tiger, elephant, crocodile, and sun bear count as events.
  Other species (tapir, bekantan, rabbit, birds, primates) are excluded even when harmed,
  because the model targets conflict with large, dangerous wildlife. (Rejang Lebong
  rabbit article, Mesuji tapir article)
- 2026-11-08 animal_harmed counts only when the killing or injury is linked to the animal's
  presence near people, farms, or livestock (retaliation, fear, crop or livestock protection,
  snares near farms). Organized poaching for trade is excluded.
- 2026-11-08 Deaths with an unknown cause are recorded as event_type = death_unknown, which
  is NOT part of the main target. If a later article confirms a human cause in a conflict
  setting, relabel it as animal_harmed, dated to the death. (Mukomuko tiger and elephant
  deaths)
- 2026-11-08 Passing references to an earlier incident (one sentence, no new detail) do not
  create an event. Only articles whose main subject is the incident do. (Seblat drone article)
- 2026-11-08 Location comes from where the event happened, never from the agency's name
  ("BKSDA Bengkulu" also covers Lampung). (Mesuji tapir article)
- 2026-11-08 An incident counts only if the article gives (a) the species, (b) a place at
  regency level or finer, and (c) a date at month level or finer. Background mentions that
  lack any of these do not create events. Deduplication merges repeat mentions of the same
  incident across articles.
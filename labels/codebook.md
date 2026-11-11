# Conflict event codebook (v2, 2026-11-10)

Changes from v1 (2026-11-08): species list limited to the four focal species; location
and date rules generalized for Mongabay; passing-reference rule superseded by the
species-place-date rule; labeling conventions for the gold set added.

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
- Policy, awareness, opinion, or species-profile pieces with no specific incident
- Year-end statistics articles (mark as aggregate, do not turn into events)

## Species
tiger, elephant, crocodile, sun_bear. No other species create events.

## Location
Record the lowest level named: desa, kecamatan, kabupaten/kota, and province.
Province is required. Location comes from where the event happened, never from the
outlet that published the article or the name of the agency quoted in it.

## Date
Use the incident date. Convert relative dates such as "Kamis (12/5)", "kemarin", or
"pekan lalu" using the publication date. If a news report describes an incident as
current but gives no date, use the publication date and write "publication date" in
notes. Background mentions of past incidents need their own month-level date; without
one they do not create events.

## Multiple incidents
Separate places or separate dates become separate events.
One herd raiding the same village for several days is ONE event.

## Labeling conventions (gold set)
- is_event: 1 if the article describes at least one qualifying event, otherwise 0
- n_events: number of qualifying events in the article (0 if none)
- With several events, fill the columns for the event the article is mainly about
- event_type: if one incident has several types, use the first in this order:
  human_attack, animal_harmed, livestock, property_damage, crop_damage, incursion_response
- kabupaten: as named in the article, without "Kabupaten"; cities as "Kota X"
- If only a kecamatan or desa is named, leave kabupaten blank and write the place in notes
- province: always filled, even when only implied by the kabupaten
- incident_date: YYYY-MM-DD; if only the month is known, use the 1st and write
  "month only" in notes
- death_unknown only: is_event = 0, and write "death_unknown", species, and place in notes
- Aggregate-only articles: is_event = 0, and write "aggregate" in notes

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
- kebun binatang: zoo (not a farm; zoo animals are excluded)
- harimau dahan: clouded leopard (not a tiger; out of scope)
- macan tutul: leopard (not a tiger; out of scope)
- Species words inside place names (Desa Gajah Mati, Barak Gajah) are not animals
- datuk: respectful local name for a tiger in Riau and nearby regions

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
- 2026-11-10 [SUPERSEDED 2026-11-10 by the physical-evidence rule below] A suspected cause
  ("diduga diracun") does not confirm a human cause. Such deaths stay death_unknown until a
  later article confirms the cause. (Langkat elephant death)
- 2026-11-08 Location comes from where the event happened, never from the agency's name
  ("BKSDA Bengkulu" also covers Lampung). (Mesuji tapir article)
- 2026-11-08 An incident counts only if the article gives (a) the species, (b) a place at
  regency level or finer, and (c) a date at month level or finer. Background mentions that
  lack any of these do not create events. Deduplication merges repeat mentions of the same
  incident across articles.
- 2026-11-10 Species-profile features that mention focal species only in comparison or in
  pet-trade context are excluded (siamang feature, mongabay.co.id 2015-08-09).
  - 2026-11-10 Live capture without injury (box trap, net, residents catching the animal) is
  incursion_response. animal_harmed requires injury or death. (Solok Selatan sun bear)
- 2026-11-10 Snares count as animal_harmed only when the article links them to protecting
  crops or livestock (e.g. jerat babi) or places the snaring in a farm, garden, or
  plantation. Snares described as set by hunters (jerat pemburu) in forest are poaching
  and excluded. (Aceh snare article; Seluma sun bear included)
- 2026-11-10 Photo captions are part of the article. When a caption and the body text
  disagree on a date, use the body text. (Solok Selatan sun bear)
- 2026-11-10 A suspected cause ("diduga diracun") does not confirm a human cause. Such deaths
  stay death_unknown until a later article confirms the cause. (Langkat elephant death)
- 2026-11-10 PHYSICAL EVIDENCE. A death counts as animal_harmed when the article reports
  physical evidence of a human-made cause at the scene (animal entangled in wire or a snare,
  poisoned bait found with the carcass, gunshot wounds), even if officials say "diduga".
  Deaths with only symptoms or speculation stay death_unknown. (Pidie Jaya elephant and
  Aceh Selatan tiger included; Langkat 2017 elephant stays death_unknown)
- 2026-11-10 TRADE MOTIVE. If the article states the animal was snared or killed to be sold,
  it is poaching and excluded, even when the snare was in a plantation. (Langkat 2017 tiger
  excluded; Langkat 2023 sun bears, motive unknown, included)
- 2026-11-10 MULTI-MONTH INCIDENTS. An ongoing incident in the same place that spans more than
  one calendar month is recorded as one event per month affected. (OKI elephant herd,
  June and July 2016)
- 2026-11-10 VAGUE TIMING. Relative phrases that do not pin down a month ("beberapa bulan
  lalu", "tahun lalu") fail the date test. (Batang Gadis sun bear attack)
- 2026-11-10 PROTECTED AREAS. A named reserve or park that spans several regencies does not
  satisfy the place test unless the article also names the regency. (Kerumutan encounters)
- 2026-11-10 UNCERTAIN ATTACKER. A human injury or death blamed on a focal species only by
  residents' guesses, with no witness or evidence, does not count. (Batang Gadis January
  2023 death)
- 2026-11-10 RESPONSE ACTIONS. Darting, trapping, or patrols within 14 days of an incident in
  the same place belong to that incident. A capture or evacuation on a later date is its own
  incursion_response event. (Bonita darted 2018-03-16 belongs to the 2018-03-10 attack;
  Bonita captured April 2018 is a new event)
- 2026-11-10 RELATED LINKS. "Baca" and "Baca juga" link titles are not part of the article.
  (Pasaman Barat article)
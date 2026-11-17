# Development log

## 2026-10-30 (1 h)
- Done. Created repo, opened accounts, submitted FIRMS archive request (VIIRS S-NPP, Indonesia, 2015 to 2025), set up Python 3.12 environment and folder structure, pinned package versions in requirements-lock.txt
- Problems. Homebrew python@3.12 could not create a working venv. Its pyexpat module was built against a newer libexpat than macOS 26.2 provides (missing symbol XML_SetAllocTrackerActivationThreshold), so platform.mac_ver() returned an empty string and pip crashed on startup. Fixed by switching to the python.org installer
- Problems. LightGBM failed to import because libomp was missing. Fixed with brew install libomp
- Problems. Rotated the Anthropic API key after a possible exposure; confirmed no key in git history
- Decisions. Python 3.12 from python.org (decisions.md #2); VIIRS S-NPP only for fire data (decisions.md #3)
- Next. Write the codebook, test the Antara crawler on one site and one tag

## 2026-11-08 (4 h)
- Done. Resumed after a midterm pause (Oct 31 to Nov 7) and compressed the schedule, moving the label checkpoint to Nov 15 (decisions.md #4)
- Done. Validated the FIRMS archive. It covers 2015-01 to 2025-12, all 132 months, VIIRS S-NPP collection 2 only, 2.38M detections. Sumatra spikes in 2015, 2019, and 2023 match known El Niño fire years
- Done. Wrote codebook v1 and tested it on real articles. Added rules for species scope (tiger, elephant, crocodile, sun bear only), conflict-linked animal harm, deaths with unknown cause (death_unknown, outside the main target), passing references, rescues with no threat, events outside Sumatra, and location taken from the event rather than the agency name
- Problem. Antara article pages prohibit crawling, content taking, and automated indexing for AI without written permission. Did not crawl Antara (decisions.md #5)
- Fix. Switched the label source to Mongabay Indonesia. Articles are published under CC BY-ND 4.0 (screenshot in docs/) and robots.txt is empty. Only extracted facts and URLs will be published (decisions.md #6)
- Done. Built a collector on Mongabay's public WordPress API instead of crawling pages
- Problem. The first full run failed on page 13 of 19 with a ChunkedEncodingError when the server cut a response short. No data was saved, because the script only wrote files at the end
- Fix. Added retries with exponential backoff (10, 20, 40, 80 seconds), a per-page cache in data/raw/mongabay_pages so interrupted runs resume, and smaller pages (50 articles instead of 100)
- Fix. Changed search terms to exactly the species words used by the candidate filter (harimau, macan, gajah, buaya, beruang). Because WordPress search matches any text containing the term, every article the filter could keep is guaranteed to be retrieved, while roughly halving the downloads
- Data. 2,981 unique articles from 2015 to 2025, 1,851 kept as candidates. Articles per year range from 214 to 344, so early years are not thin and the full 2015 to 2025 panel stays

## 2026-11-10 (3 h)
- Problem. VS Code flagged unusual line terminators in candidates.jsonl. Some article text contained Unicode line and paragraph separators (U+2028, U+2029), which tools such as VS Code and str.splitlines() treat as line breaks and which could split a JSONL record in two
- Fix. Normalized both separators to newlines in clean_html. Verified 0 remaining in articles.jsonl, candidates.jsonl, and rejected.jsonl
- Problem. The collector file was briefly overwritten by the original version, most likely by saving a VS Code tab that still held the old file. A rerun with that version failed on a dropped connection (RemoteDisconnected), since it had no retries
- Fix. Restored the retry and cache version and confirmed it with grep (get_page present, search terms harimau, macan, gajah, buaya, beruang, 85 cached pages). Lesson recorded: close a file's editor tab before replacing the file on disk
- Data. Rebuilt all files from the page cache with no new downloads. 2,981 unique articles and 1,851 candidates, identical to 2026-11-08, which confirms that run already used the retry and cache version and that the cache reproduces results exactly
- Done. Drew the gold sample with make_gold_sample.py. 100 articles (80 candidates and 20 keyword-filter rejects, seed 42), with 20 locked away as a holdout to be scored once at the very end (decisions.md #7)
- Next. Hand-label all 100 articles in labels/gold_labels.csv before running any LLM extraction
- Done. Updated the codebook to v2 before labeling. Limited species to the four focal species, generalized the location and date rules for Mongabay, marked the passing-reference rule as superseded by the species-place-date rule, reconciled the publication-date fallback with that rule, and added labeling conventions for the gold set.
- Done. Labeled the first gold article (siamang species feature, 2015-08-09) as a non-event and added a rule for species-profile features
- Done. Cross-checked 18 gold articles against codebook v2. Added rules for live capture, snares, photo captions, and suspected causes of death, plus glossary entries for harimau dahan, macan tutul, and species words inside place names
- Note. Some cross-checked articles are in the holdout split; rules derived from them may make the holdout extraction score slightly optimistic
- Done. Finished hand-labeling all 100 gold articles
- Done. Cross-ch`ecked the remaining 81 articles,15 read in full and 66 judged from title and location. Added codebook rules for physical evidence of cause of death, trade motive, multi-month incidents, vague timing, protected areas spanning regencies, uncertain attackers, response actions, and related-article links, plus the glossary entry datuk
- Problem. The original holdout rows sat at the top of the sheet and were reviewed while rules were written, so the holdout was no longer unseen
- Fix. Moved them to dev and drew 20 fresh holdout articles with refresh_holdout.py (decisions.md #8)
- Next. Label the 20 fresh holdout articles, then compute agreement with the second reader on the dev set
- Note. Dev labels (100 articles) were finalized after reading the second reader's review, so the 100% is_event agreement is post-adjudication, not independent inter-rater agreement
- Done. Labeled the 20 `fresh holdout articles alone, without the second reader

## 2026-11-10 (3 hours)
- Done. Rewrote the extraction prompt to follow codebook v3 (four species, Sumatra only, species-place-date test, physical-evidence, trade-motive, snare, multi-month, and response-action rules), raised the text limit to 15,000 characters, and restricted gold runs to the dev split so the holdout stays unseen (prompt v1)
- Done. Updated evaluate_extraction.py to apply the same scope as the labels, report field accuracy for event type and event count, track token cost, and write a detailed error file

## 2026-11-17 (4 h)
- Data. Prompt v1 on the 100 dev articles scored precision 0.917, recall 0.846, F1 0.88 (11 TP, 1 FP, 2 FN, 86 TN) at a cost of US$0.08. Field accuracy on true positives was 1.0 for event type, species, and province, 0.909 for regency and month, and 0.727 for event count
- Done. Read all 5 error rows. Only one was a prompt problem
- Problem. Pipeline bug. The collector deleted photo captions to keep the keyword filter clean, so the extractor never saw the Seluma sun bear event, which appears only in a caption, even though the codebook counts captions as part of the article
- Fix. The collector now stores captions in a separate captions field, so the keyword filter and candidate split are unchanged, and the extractor sends them after the body under "Keterangan foto". Rebuilt articles.jsonl from the page cache with no new downloads, then rebuilt gold_articles.jsonl with rebuild_gold_text.py
- Problem. The Tesso Nilo reply could not be parsed as JSON, so it counted as a miss. v1 did not record why
- Fix. extract_llm.py now records stop_reason and retries an unparseable reply once, and the evaluator reports failed extractions separately (n_failed) instead of hiding them among false negatives
- Problem. Prompt error. For Bonita, the model gave the undated attacks the date of the April 2018 capture and labeled them human_attack
- Fix. Prompt v2 states that each event needs its own date and that an undated attack never takes the date of a later capture
- Problem. Label errors. The Tebo article (2023-05-24) was labeled 0 from its title, but it describes an elephant herd destroying huts in Muaro Sekalo, Tebo, on 6 and 7 Nov 2022, so the model was right. The Pasaman Barat dam tiger (2024-03-23), labeled incursion_response during adjudication with the second reader, describes no threat and the tiger left on its own, so it does not meet the rule
- Fix. Corrected both dev labels with fix_dev_labels_2026_11_16.py (decisions.md #10) and added codebook rules for infrastructure sites, events needing their own date, and multi-day damage by one herd (codebook v3)
- Note. The model split the Tebo herd into two events on consecutive nights. This is harmless downstream because dedup.py merges same-species events in the same regency within 14 days, so the prompt was not changed for it
- Data. Re-scored prompt v1 on the corrected dev labels (14 event articles): precision 1.0, recall 0.857, F1 0.923 (12 TP, 0 FP, 2 FN), with 1 failed extraction
- Data. Prompt v2 on dev scored precision 0.929, recall 0.929, F1 0.929 (13 TP, 1 FP, 1 FN, 85 TN) at a cost of US$0.08. The caption fix recovered the Seluma sun bear event and the own-date rule fixed Bonita. Field accuracy on true positives was 1.0 for event type, species, regency, province, and month
- Note. v1 and v2 differ by one article each way, which is within run-to-run variation on 14 event articles. The Langkat 2017 elephant death went from correct in v1 to a false positive in v2 although no rule about it changed, and the v2 reply contradicts itself: its notes call the death death_unknown while its events list an animal_harmed event
- Problem. Tesso Nilo failed in both runs. v1 used all 2,000 output tokens and returned no text. v2 used all 3,000 output tokens (stop_reason=max_tokens) and returned only 879 characters of unfinished JSON, so roughly 2,700 tokens went to thinking. Claude Haiku 5.5 thinks before answering by default and thinking tokens count toward max_tokens, so on this article the limit ran out before the answer was finished
- Fix. Raised max_tokens to 16,000, which costs nothing extra because only tokens actually used are billed. Did not set temperature, because Haiku 5.5 takes no sampling parameters
- Problem. My 2026-11-16 correction of the Pasaman Barat label was wrong. It relied on an incomplete reading of the article, which says the tiger roamed around settlements after leaving the dam channel and that BKSDA told residents to limit field work. That meets incursion_response, so v2's reasoning was right
- Fix. Restored the original label with fix_dev_labels_2026_11_17.py (decisions.md #11) and revised the infrastructure rule (codebook v4)
- Note. The remaining v2 count mismatches (Solok Selatan January 2016 bears, Tebo herd on consecutive nights) fall in the same regency-month as the gold events, so they do not change the panel target
- Done. Prompt v3 raises max_tokens to 16,000, revises the infrastructure rule, and ends with a self-check that no death_unknown animal and nothing excluded in the notes appears in events. Added --tag to store a second run separately and compare_runs.py to measure run-to-run agreement
- Decision. v3 is the final prompt, with the rule for using it on the holdout written and committed before running it (decisions.md #12)
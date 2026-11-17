# Decisions log

## 1. Unit of analysis and scope (2026-10-30)
**Decision.** One row per regency (kabupaten/kota) per month, January 2015 to December 2025,
covering all ten Sumatran provinces, with Bengkulu as the case study.
**Why.** Bengkulu alone records too few conflict events to train a model, especially for tigers.
Sumatra-wide data gives enough positive examples while keeping the Bengkulu focus.
**Revisit if.** The Nov 7 checkpoint shows fewer than 250 positive regency-months.

## 2. Python 3.12 from python.org (2026-10-30)
**Decision.** Use the python.org 3.12 installer (3.12.9) for the project environment.
**Why.** Python 3.10 reaches end of life in October 2026, and current pandas and NumPy need 3.11 or later.
The Homebrew 3.12 build failed on macOS 26.2 because of a libexpat version mismatch.
**Exact versions.** Pinned in requirements-lock.txt.

## 3. Fire data from one sensor only (2026-10-30)
**Decision.** Use only VIIRS S-NPP hotspots for every year.
**Why.** Adding NOAA-20 from 2020 onward would create an artificial jump in fire counts
that the model could mistake for a real trend.

## 4. Compressed schedule after a midterm pause (2026-11-08)
**Decision.** Paused Oct 31 to Nov 7 for midterms. Kept the Nov 30 finish by compressing
each phase and moving the label checkpoint to Nov 15.
**Cost.** Optional extras (second labeler, Mongabay as a second source, rainfall feature)
are dropped unless the project gets ahead of schedule.

## 5. Antara cannot be crawled (2026-11-08)
**Finding.** Antara article pages state that taking content, crawling, or automated indexing
for AI is prohibited without written permission from ANTARA.
**Decision.** Do not crawl Antara or send its articles to an LLM. Find a label source whose
terms permit this use, and request permission from Antara in parallel.

## 6. Mongabay Indonesia as the label source (2026-11-08)
**Decision.** Collect conflict events from mongabay.co.id through its public WordPress API.
**Why.** Articles are published under CC BY-ND 4.0 (screenshot in docs/), and robots.txt
sets no restrictions. The project publishes only extracted facts and article URLs,
never article text or edited versions.
**Benchmark.** The NTU human-tiger interaction dataset for Riau (2010 to 2020) will be
used to estimate recall, not for training.
**Risk.** Mongabay publishes fewer incident reports than Antara, so the Nov 15 checkpoint
may require switching to regency-quarters.

## 7. Gold set of 100 articles (2026-11-10)
**Decision.** Hand-label 100 articles (80 candidates, 20 rejects) instead of the planned 150.
**Why.** Mongabay articles are long features that take about 3 minutes each to label,
so 150 would take over 7 hours. 100 still supports precision and recall estimates,
with 20 articles held out for one final score.
**Cost.** Wider uncertainty on the extraction scores, which will be reported as such.

## 8. Fresh holdout set (2026-11-10)
**Problem.** make_gold_sample.py placed the 20 holdout rows at the top of the sheet, so they
were labeled first and reviewed with a second reader while codebook rules were being written.
Rules learned from them would make the holdout extraction score optimistic.
**Decision.** Moved those 20 rows to dev and drew 20 fresh holdout articles (16 candidates,
4 rejects, seed 2026) with refresh_holdout.py. The fresh rows are labeled by me alone and
never used to write or change codebook rules or the extraction prompt.
**Cost.** About one more hour of labeling.

## 9. How label agreement is reported (2026-11-10)
**Finding.** Dev labels were finalized after reading a second reader's review, so their
agreement with that reader is post-adjudication.
**Decision.** Report the dev set as adjudicated labels, not as an inter-rater reliability
score. The 20 holdout articles were labeled by me alone and are used only for the final
extraction score.`

## 10. Correcting dev labels found wrong during error analysis (2026-11-16)
**Finding.** The prompt v1 error analysis showed two dev labels broke the codebook. The Tebo
article (2023-05-24) describes elephants destroying huts on 6 and 7 Nov 2022 but was labeled 0
from its title. The Pasaman Barat dam tiger (2024-03-23) does not meet incursion_response.
**Decision.** Correct a dev label when error analysis shows it breaks the codebook, apply the
change with a committed script (fix_dev_labels_2026_11_16.py), and re-score the previous
prompt on the corrected labels so label fixes and prompt changes are measured separately.
Holdout labels are never changed.
**Limitation.** Only articles where the model disagreed were re-examined, so an error shared
by me and the model would not be found.

## 11. Pasaman Barat label restored (2026-11-17)
**Finding.** The 2026-11-16 correction (decision #10) relied on an incomplete reading of the
Pasaman Barat article. The article says the tiger was still roaming around settlements after
leaving the dam channel, a team checked residents' track reports near Pinaga Aur Kuning, and
BKSDA told residents to limit field work. That meets incursion_response.
**Decision.** Restored the original label with fix_dev_labels_2026_11_17.py and revised the
infrastructure rule (codebook v4). From now on, a label is changed only after reading the full
passage in the article itself, not a summary of it.

## 12. Prompt v3 is the final extraction prompt (2026-11-17)
**Decision.** Stop prompt changes at v3, as planned (at most three versions). With 14 event
articles in dev, a one-article difference between v1 and v2 is within run-to-run variation.
**Rule, written before seeing any v3 result.** Run v3 on dev twice. If the main v3 run has no
failed extractions and a dev F1 of at least 0.85, score the holdout once with v3 and use v3 for
the full run. Otherwise fix only bugs (failed calls, parsing), never rules, and leave the
holdout untouched until that is done.
**Settings.** Claude Haiku 5.5, max_tokens 16,000, no sampling parameters (the model does not
take them), up to 15,000 characters of body text plus photo captions.
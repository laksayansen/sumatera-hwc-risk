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
- Next. Draw a 100-article gold sample (80 candidates, 20 rejects) and label it by hand before running any LLM extraction

## 2026-11-10 (3 h)
- Problem. VS Code flagged unusual line terminators in candidates.jsonl. Some article text contained Unicode line and paragraph separators (U+2028, U+2029), which tools such as VS Code and str.splitlines() treat as line breaks and which could split a JSONL record in two
- Fix. Normalized both separators to newlines in clean_html. Verified 0 remaining in articles.jsonl, candidates.jsonl, and rejected.jsonl
- Problem. The collector file was briefly overwritten by the original version, most likely by saving a VS Code tab that still held the old file. A rerun with that version failed on a dropped connection (RemoteDisconnected), since it had no retries
- Fix. Restored the retry and cache version and confirmed it with grep (get_page present, search terms harimau, macan, gajah, buaya, beruang, 85 cached pages). Lesson recorded: close a file's editor tab before replacing the file on disk
- Data. Rebuilt all files from the page cache with no new downloads. 2,981 unique articles and 1,851 candidates, identical to 2026-11-08, which confirms that run already used the retry and cache version and that the cache reproduces results exactly
- Done. Drew the gold sample with make_gold_sample.py. 100 articles (80 candidates and 20 keyword-filter rejects, seed 42), with 20 locked away as a holdout to be scored once at the very end (decisions.md #7)
- Next. Hand-label all 100 articles in labels/gold_labels.csv before running any LLM extraction
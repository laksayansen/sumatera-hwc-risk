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

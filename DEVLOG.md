# Development log

## 2026-10-30 (1 h)
- Done. Created repo, opened accounts, submitted FIRMS archive request (VIIRS S-NPP, Indonesia, 2015 to 2025), set up Python 3.12 environment and folder structure, pinned package versions in requirements-lock.txt
- Problems. Homebrew python@3.12 could not create a working venv. Its pyexpat module was built against a newer libexpat than macOS 26.2 provides (missing symbol XML_SetAllocTrackerActivationThreshold), so platform.mac_ver() returned an empty string and pip crashed on startup. Fixed by switching to the python.org installer
- Problems. LightGBM failed to import because libomp was missing. Fixed with brew install libomp
- Problems. Rotated the Anthropic API key after a possible exposure; confirmed no key in git history
- Decisions. Python 3.12 from python.org (decisions.md #2); VIIRS S-NPP only for fire data (decisions.md #3)
- Next. Write the codebook, test the Antara crawler on one site and one tag

# Sentinel's Journal

## 2024-10-24 - Initial Security Posture
**Vulnerability:** Absence of `.gitignore` in a new repository.
**Learning:** Even in the "Foundation & Infrastructure" phase (Phase 0), the lack of a `.gitignore` poses a significant risk of accidental secret leakage (e.g., `.env`, API keys) as developers set up their environments.
**Prevention:** Created a comprehensive `.gitignore` immediately upon repository initialization to enforce security by default.

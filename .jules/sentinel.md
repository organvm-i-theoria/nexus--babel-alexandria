## 2024-05-22 - [Empty Repo Security Baseline]
**Vulnerability:** Lack of `.gitignore` in a new repository poses a high risk of accidental secret leakage (e.g., `.env`, keys).
**Learning:** Even in an empty repository, establishing a security baseline (specifically `.gitignore`) is a critical "security enhancement" that prevents future vulnerabilities.
**Prevention:** Always initialize repositories with a strict `.gitignore` that explicitly excludes secrets and environment files before any code is written.

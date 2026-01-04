## 2024-05-22 - Missing Security Foundation
**Vulnerability:** Complete absence of `.gitignore` in a new repository.
**Learning:** Even when documentation (roadmap) mentions environment setup, the actual implementation (files) might be missing. Trust filesystem verification over assumptions or memory.
**Prevention:** Always verify the existence of security config files (`.gitignore`, `.env.example`, etc.) immediately upon entering a new repo, regardless of project phase.

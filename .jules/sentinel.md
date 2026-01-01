## 2024-01-01 - Baseline Security Configuration
**Vulnerability:** Absence of `.gitignore` and `pyproject.toml` in a new repository exposes the project to accidental secret leakage (e.g., `.env`, `secrets.json`) and supply chain attacks (unmanaged dependencies).
**Learning:** Establishing a security baseline in Phase 0 (Foundation) is critical. Passive security measures like strict `.gitignore` patterns and configuring `ruff` with `flake8-bandit` (`S` selector) provide immediate, automated protection without active code.
**Prevention:** Always initialize repositories with a comprehensive `.gitignore` and security-aware linting configuration (`ruff` with `S` rule) before writing feature code.

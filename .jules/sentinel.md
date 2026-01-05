## 2024-02-14 - [Founding Security in Empty Repositories]
**Vulnerability:** Missing `.gitignore` in a new repository allows immediate accidental commitment of secrets (API keys, .env files) and build artifacts.
**Learning:** Security must be established *before* code is written. Passive security measures like `.gitignore` are the most effective first line of defense as they prevent the error state entirely.
**Prevention:** Always initialize a repository with a comprehensive `.gitignore` that explicitly excludes common secret filenames (`secrets.json`, `.env`) and dependency directories (`node_modules`, `.venv`).

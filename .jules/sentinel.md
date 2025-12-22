# Sentinel Journal

## 2024-05-22 - Secure Repository Initialization
**Vulnerability:** Repository initialized without `.gitignore`, creating a high risk of accidental secret or artifact commit.
**Learning:** Security must be foundational. Waiting for code to exist before adding protection mechanisms leaves a window of vulnerability during the initial setup phase.
**Prevention:** Always initialize repositories with a comprehensive `.gitignore` that explicitly blocks secrets (`.env`, `*.key`) and build artifacts before any development begins.

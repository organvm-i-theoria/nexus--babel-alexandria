## 2024-01-01 - [Initial Security Setup]
**Vulnerability:** New repository lacked security controls, risking secret leakage and unmanaged dependencies.
**Learning:** Security must be baked in from the start (Shift Left). Empty repos are the best place to set strict defaults.
**Prevention:** Established .gitignore, dependency scanning (safety), and static analysis (bandit) before any code was written.

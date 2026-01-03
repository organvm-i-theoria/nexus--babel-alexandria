## 2024-05-23 - [Initial Security State: Passive Defense]
**Vulnerability:** Repository lacked `.gitignore`, creating high risk of accidental secret leakage (credentials, .env files) if development started.
**Learning:** In "Phase 0" or empty repositories, the most critical security action is establishing passive defenses (exclusions) before active code is written. Prevention is cheaper than remediation.
**Prevention:** Always verify and create a strict `.gitignore` as the first step in any repository interaction, covering secrets, environments, and build artifacts.

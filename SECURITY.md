# Security Policy

## Supported Versions

The following versions of the Rhetorical-Linguistic Operating System (RLOS) are currently being supported with security updates:

| Version | Supported          |
| ------- | ------------------ |
| 0.1.x   | :white_check_mark: |
| < 0.1   | :x:                |

## Reporting a Vulnerability

We take the security of this project seriously. If you discover a security vulnerability, please follow these steps:

1.  **Do not** open a public issue on GitHub/GitLab.
2.  Email the security team at `security@example.com` (replace with actual contact if available) or use the private vulnerability reporting feature on the repository platform.
3.  Include as much information as possible:
    *   Type of issue (e.g., SQL injection, XSS, etc.)
    *   Full paths of source file(s) related to the manifestation of the issue.
    *   The location of the affected source code (tag/branch/commit or direct URL).
    *   Any special configuration required to reproduce the issue.
    *   Step-by-step instructions to reproduce the issue.
    *   Proof-of-concept or exploit code (if possible).
    *   Impact of the issue, including how an attacker might exploit it.

## Vulnerability Disclosure Process

1.  **Acknowledgment:** We will acknowledge receipt of your report within 48 hours.
2.  **Assessment:** We will investigate the issue and determine its severity and impact.
3.  **Fix:** We will work on a fix and test it thoroughly.
4.  **Disclosure:** Once the fix is released, we will publicly disclose the vulnerability (unless you request otherwise).

## Security Best Practices

*   **Secrets:** Never commit secrets (API keys, passwords, private keys) to the repository. Use environment variables.
*   **Dependencies:** Regularly update dependencies to patch known vulnerabilities.
*   **Code Review:** All code changes must be reviewed by at least one other developer, with a focus on security.

## Tools

We use the following tools to ensure security:
*   `bandit`: For finding common security issues in Python code.
*   `pytest`: For running tests.
*   `pre-commit`: For running checks before committing.

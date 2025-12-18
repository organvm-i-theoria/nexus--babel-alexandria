# Security Policy

## Reporting a Vulnerability

We take the security of the Rhetorical-Linguistic Operating System (RLOS) seriously. If you discover a security vulnerability, please bring it to our attention immediately.

### **Do NOT create a public GitHub issue for security vulnerabilities.**

Instead, please report security vulnerabilities via email to:

**architecture@rlos.org**

Please include the following information in your report:
- A description of the vulnerability.
- Steps to reproduce the issue.
- Potential impact of the vulnerability.
- Any relevant code snippets or screenshots.

We will acknowledge your report within 48 hours and will keep you updated on the progress of the fix.

## Supported Versions

Currently, the project is in the design/roadmap phase.

## Security Best Practices

When contributing to RLOS, please adhere to the following security guidelines:
- **No Hardcoded Secrets**: Do not commit API keys, passwords, or other sensitive information to the repository. Use environment variables instead.
- **Input Validation**: Validate all user inputs to prevent injection attacks (e.g., SQL injection, XSS).
- **Sanitization**: Sanitize data before displaying it or using it in system commands.
- **Least Privilege**: Ensure that the application runs with the minimum necessary privileges.
- **Dependencies**: Keep dependencies up to date to avoid known vulnerabilities.

## License

By contributing to this repository, you agree that your contributions will be licensed under the project's license.

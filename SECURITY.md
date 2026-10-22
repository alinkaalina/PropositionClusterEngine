# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| v2.0.x  | :white_check_mark: |

## Reporting a Vulnerability

Please do not open a public issue for security vulnerabilities. Instead, submit a private report via GitHub Security Advisories in this repository.

## Architectural Safeguards
- **Transitivity Verification**: Pairwise LLM classifications are verified for strict mathematical transitivity (`adj[i][j] and adj[j][k] => adj[i][k]`) before state indexing.
- **Prompt Injection Isolation**: All fetched statements are canonicalized and evaluated strictly as passive data; any ambiguity or injection attempt forces an `ISOLATED` state.
- **Cryptographic Source Pinning**: Enforces exact SHA-256 payload digest matching against the registered commit hash.

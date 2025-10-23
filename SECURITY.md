# Security Policy

## Supported Versions

Security updates apply to the latest released version of `langchain-notion-tools`.

## Reporting a Vulnerability

If you discover a security issue, please email [security@dineshkummara.dev](mailto:security@dineshkummara.dev) with:

- A description of the vulnerability
- Steps to reproduce
- Any potential impact

We will acknowledge receipt within 48 hours and follow up with next steps.

## Notion API Scopes & Responsibilities

This toolkit relies on the official Notion API, which is proprietary. Your integration token **must** be provisioned with the following scopes to enable search and write flows:

- `pages:read`
- `pages:write`
- `databases:read`
- `databases:write`

The package sanitises payloads (block allow-lists and size limits) before sending them to Notion, but all content you submit is ultimately processed by the Notion platform. Review and harden your prompts to avoid supplying malicious HTML/JavaScript, and rotate tokens if you suspect compromise.

For more information about Notion’s platform policies, consult the [Notion Developer Terms](https://www.notion.so/developers).

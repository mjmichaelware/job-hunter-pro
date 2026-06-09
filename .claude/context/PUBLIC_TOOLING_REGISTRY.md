# Public Tooling Registry

This is a registry of useful public tooling categories. It is not exhaustive and must be updated over time.

## Core CLI tools

- git — version control
- gh — GitHub CLI
- gcloud — Google Cloud CLI
- python3 — scripting and apps
- uv — Python package/project management
- ruff — Python linting and formatting
- pytest — Python testing
- node / npm — JavaScript tooling
- playwright — browser/UI testing when supported
- jq — JSON inspection
- ripgrep / rg — fast code search
- tar / gzip — portable handoff archives

## AI/provider categories

- OpenAI-compatible APIs
- Anthropic Claude APIs
- Google Gemini / Vertex APIs
- local model runtimes where supported
- embedding APIs
- reranking APIs
- speech-to-text APIs
- text-to-speech APIs
- OCR/document parsing APIs
- search APIs
- maps/geocoding APIs
- job/discovery APIs

## Rule

Every provider must be added through a registry/adapter pattern, with secrets in environment or secret manager only.

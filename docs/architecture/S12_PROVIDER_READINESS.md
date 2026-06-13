# S12 Provider Readiness

Status: Ready for UI/engine deploy with review-only dormant providers.

## Passing providers/capabilities

- SerpAPI
- Adzuna
- USAJOBS
- Jooble
- The Muse
- Google Maps
- OpenAI
- Gemini
- Anthropic
- Groq

## Review-only dormant providers

- xAI: API key reaches xAI, but the team requires credits or license before use.
- Careerjet: API key reaches Careerjet, but the source IP requires authorization/allowlisting.

## Deploy decision

This S12 deploy is intended to test the UI/UX cockpit and safe engine surfaces with the working provider set.

This deploy does not create Scheduler, does not call `/api/ingest`, and does not call live `/api/jobs`.

## Secret safety

Secret values are stored in Google Secret Manager only. No secret values are committed or printed.

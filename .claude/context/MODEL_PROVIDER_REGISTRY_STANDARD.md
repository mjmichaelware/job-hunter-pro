# Model and Provider Registry Standard

Any app using APIs or models should use adapters and registries.

## Provider adapter fields

- provider_id
- display_name
- capability_type
- cost_risk
- auth_source
- timeout
- retry policy
- rate limit
- input schema
- output schema
- error schema
- safe dry-run behavior

## Capability types

- discovery
- enrichment
- classification
- extraction
- ranking
- geocoding
- storage
- notification
- visualization

## Critical rule

Do not mix discovery providers with LLM enrichment providers. Keep capability boundaries explicit.

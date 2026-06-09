# AI Model and Agent Safety Standard

AI agents are powerful but unsafe without boundaries.

## LLM rules

- LLMs may summarize, classify, extract, explain, rank, draft, and enrich.
- LLMs must not be treated as ground truth without source evidence.
- LLMs must not invent providers, APIs, files, deployments, credentials, or proof.
- LLMs must not print secrets.
- LLMs must not call costly or protected endpoints unless explicitly authorized.
- Tool permissions must be explicit.
- Destructive actions must be gated.

## AI security risks to track

- prompt injection
- insecure output handling
- training/data poisoning
- model denial of service
- supply chain risk
- sensitive information disclosure
- excessive agency
- overreliance
- insecure plugin/tool design
- unbounded cost or quota usage

## Agent stop conditions

- missing secrets
- unknown billing impact
- ambiguous deploy target
- failing compile
- failing safe proof
- unexpected production side effect
- user has not authorized commit, push, deploy, or live calls

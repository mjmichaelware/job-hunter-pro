# Swarm Providers — adding APIs as one decoupled file each

Goal: scale to 50+ discovery sources where **adding an API = one new file**, secrets
live in Secret Manager only, and a broken source can never take down the rest.

## The bedrock (already in place)
- **Auto-discovery** (`providers/__init__.py`): every `providers/search/*.py` and
  `providers/reasoning/*.py` is imported in isolation; any module-level `Provider`
  instance registers itself by `metadata.key`. No central import list, no shared file
  to merge-conflict on. Files starting with `_` or named `base` are ignored.
- **Isolation**: one bad provider file is skipped + logged, never crashing the swarm.
- **Generic key access** (`core/config.py::Config.provider_key("FOO_API_KEY")`): a new
  provider reads its credential without anyone editing `Config`.
- **Generic budget guard** (`providers/base.py::ProviderMetadata.budget_class`): a
  provider declares `"free"` or `"serpapi_quota"`; no central name list in the guard.
- **Concurrent fanout** (`search/live_provider_bridge.py`): providers run in a bounded
  thread pool with per-provider caps + quarantine on 401/403/429, so 50 sources don't
  serialize into a timeout.

## Add a provider in 5 steps
1. `cp providers/search/_template.py providers/search/<name>.py`  (no leading `_`).
2. Rename the class; set `metadata.key/label/description`, `requires_api_key`,
   `budget_class`.
3. Implement `search(query)` → map each API result to a `SearchResult`
   (`provider, query, title, url, snippet, source_name, published_date, raw_json,
   confidence, cost_units`). Call `check_hard_failure(self.metadata.key, resp)` right
   after the HTTP call.
4. Keep the **module-level instance** line (`<name>_provider = <Name>Provider()`) — that
   is what the registry discovers.
5. Secrets — terminal only, never in code:
   ```bash
   bash scripts/add_key.sh ACME_API_KEY      # prompts (hidden), stores in Secret Manager
   ```
   Then mount it on deploy by adding `ACME_API_KEY=ACME_API_KEY:latest` to the
   `--set-secrets` list in `scripts/deploy.sh`. A keyless API needs none of this and is
   live day one (set `requires_api_key=False`, `is_available()` returns True).

## Safety rules (CLAUDE.md)
- Never hardcode/print/commit a secret value. `add_key.sh` reads it from a hidden prompt.
- LLMs (`providers/reasoning/*`) are enrichment/classification only — never discovery.
- Discovery providers go in `providers/search/`.
- A new provider must declare `budget_class` so the guard treats paid quota correctly.

## Verify a new provider locally (no live spend)
```bash
python3 -c "from providers import reload_providers, get_all_providers; reload_providers(); \
print(sorted(p.metadata.key for p in get_all_providers()))"
python3 -m py_compile providers/search/<name>.py
```
Dormant-until-keyed is correct: a keyed provider shows `status: dormant` in
`/api/providers` until its secret exists.

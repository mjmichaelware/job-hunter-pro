# S11 Script Proof

## 1. S11 Purpose
Implement local operation helper scripts in `scripts/` to facilitate deployment, secret management, and system seeding without performing live mutations during S11.

## 2. Files Changed
- `scripts/add_key.sh`: Secret Manager helper with dry-run support.
- `scripts/deploy.sh`: Cloud Run deployment script with local compile checks.
- `scripts/seed_industries.sh`: Firestore taxonomy seeder via Python.
- `scripts/make_scheduler_oidc.sh`: Cloud Scheduler creation helper with OIDC auth.

## 3. Agent Findings
- Existing scripts were placeholders.
- Repository structure supports automated seeding (industry registry and Firestore client exist).
- Cloud Run environment settings (Project ID, Region) are consistent across documentation and configuration.

## 4. Dry-run Proof Commands
All scripts were validated with `bash -n` for syntax and `--dry-run` for logic execution.

### scripts/add_key.sh --dry-run
```
--- Secret Manager Helper: TEST_SECRET ---
[DRY-RUN] Checking if secret TEST_SECRET exists...
[DRY-RUN] Command: gcloud secrets describe TEST_SECRET --quiet
[DRY-RUN] If missing: gcloud secrets create TEST_SECRET --replication-policy="automatic"
[DRY-RUN] Adding version: gcloud secrets versions add TEST_SECRET --data-file=-
[DRY-RUN] (Redacted): <secret value from stdin would be piped here>
```

### scripts/deploy.sh --dry-run
```
--- Deploying job-hunter-pro to ai-job-agent-498702 (us-central1) ---
Running local compile checks...
Compile checks passed.
[DRY-RUN] Deploy command shape:
[DRY-RUN] gcloud run deploy job-hunter-pro --source . --project ai-job-agent-498702 --region us-central1 --allow-unauthenticated --set-secrets ...
```

### scripts/seed_industries.sh --dry-run
```
--- Seeding Industries ---
[DRY-RUN] Would execute industry seeding logic.
[DRY-RUN] Logic: Iterate industries from industries/__init__.py and save to Firestore 'industries' collection.
```

### scripts/make_scheduler_oidc.sh --dry-run
```
--- Creating Cloud Scheduler Job (OIDC) ---
[DRY-RUN] Scheduler command shape (NO TOKEN IN URL):
[DRY-RUN] gcloud scheduler jobs create http job-hunter-daily-ingest --project ai-job-agent-498702 --location us-central1 --schedule "0 9 * * *" --uri "https://job-hunter-pro-5t3wttw2ua-uc.a.run.app/api/ingest" --http-method GET --oidc-service-account-email job-hunter-scheduler@ai-job-agent-498702.iam.gserviceaccount.com --oidc-token-audience https://job-hunter-pro-5t3wttw2ua-uc.a.run.app
```

## 5. Secret Safety Proof
- `add_key.sh` uses `read -rs` to hide input and `--data-file=-` to avoid temp files.
- `deploy.sh` uses Secret Manager references (`--set-secrets`) instead of environment values.
- Grep verified no hardcoded tokens or keys in the scripts.

## 6. Scheduler OIDC Proof
- `make_scheduler_oidc.sh` verified:
  - No token query parameter or auth query parameter is used in the Scheduler URI.
  - Uses `--oidc-service-account-email`.
  - Uses `--oidc-token-audience`.
  - Targets `${SERVICE_URL}/api/ingest`.

## 7. Deploy Safety Proof
- `deploy.sh` exists and is implemented but was **not** executed live.
- Local compile checks passed, ensuring code integrity before S12.

## 8. Provider Safety Proof
- Provider safety proof: no scripts call live providers; provider key names appear only as Secret Manager references.
- `seed_industries.sh` uses local registry files only.

## 9. Backend Gaps
- `seed_industries.sh` requires `BaseRepository` in `store/repository.py` and `industries.get_all_industries()`. Both are confirmed present.
- Deployment requires `gcloud` CLI and authenticated project access.

## 10. Stop Before S12
S11 is complete. No live deployments or scheduler jobs were created. Ready for S12.

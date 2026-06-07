#!/data/data/com.termux/files/usr/bin/bash
# scripts/add_key.sh - Safely add secrets to Google Secret Manager
set -euo pipefail

DRY_RUN=0
SECRET_NAME=""

usage() {
    echo "Usage: $0 [--dry-run] <SECRET_NAME>"
    echo "Example: $0 --dry-run OPENAI_API_KEY"
    exit 1
}

if [[ $# -eq 0 ]]; then usage; fi

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) DRY_RUN=1; shift ;;
        -*) echo "Unknown option: $1"; usage ;;
        *) SECRET_NAME="$1"; shift ;;
    esac
done

if [[ -z "$SECRET_NAME" ]]; then usage; fi

echo "--- Secret Manager Helper: $SECRET_NAME ---"

if [[ $DRY_RUN -eq 1 ]]; then
    echo "[DRY-RUN] Checking if secret $SECRET_NAME exists..."
    echo "[DRY-RUN] Command: gcloud secrets describe $SECRET_NAME --quiet"
    echo "[DRY-RUN] If missing: gcloud secrets create $SECRET_NAME --replication-policy=\"automatic\""
    echo "[DRY-RUN] Adding version: gcloud secrets versions add $SECRET_NAME --data-file=-"
    echo "[DRY-RUN] (Redacted): <secret value from stdin would be piped here>"
    exit 0
fi

# Real Run
if ! gcloud secrets describe "$SECRET_NAME" &>/dev/null; then
    echo "Secret $SECRET_NAME does not exist. Creating..."
    gcloud secrets create "$SECRET_NAME" --replication-policy="automatic"
fi

echo "Enter value for $SECRET_NAME (input will be hidden):"
read -rs SECRET_VALUE

if [[ -z "$SECRET_VALUE" ]]; then
    echo "Error: Secret value cannot be empty."
    exit 1
fi

echo -n "$SECRET_VALUE" | gcloud secrets versions add "$SECRET_NAME" --data-file=-
echo "Successfully added new version to $SECRET_NAME."
unset SECRET_VALUE

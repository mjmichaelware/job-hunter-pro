#!/data/data/com.termux/files/usr/bin/bash
# scripts/add_swarm_keys.sh — one command to enter the new free-tier provider keys.
# Run it anytime; enter the keys you have, press Enter to skip the rest, re-run later.
# Each value is read hidden and stored ONLY in Google Secret Manager (via add_key.sh).
set -euo pipefail
HERE="$(cd "$(dirname "$0")" && pwd)"

# New free-tier secrets used by the civic/keyed provider batch.
KEYS=(
  CAREERONESTOP_USERID        # CareerOneStop (US DOL) — free signup, job search
  CAREERONESTOP_TOKEN         # CareerOneStop bearer token
  YELP_API_KEY                # Yelp Fusion — free tier, business leads + ratings
  FOURSQUARE_API_KEY          # Foursquare Places — free tier, business leads
  CENSUS_API_KEY              # US Census — free, enrichment (employer counts by ZIP)
  BLS_API_KEY                 # Bureau of Labor Statistics — free, enrichment (wages)
  UTAH_OPENDATA_APP_TOKEN     # optional — raises Socrata rate limits (keyless works too)
  DATA_SLC_APP_TOKEN          # optional — Data.SLC.gov Socrata app token
)

echo "=== Job Hunter Pro — swarm key setup ==="
echo "Press y to enter a key now, anything else to skip. Re-run anytime."
echo

for K in "${KEYS[@]}"; do
  if gcloud secrets describe "$K" &>/dev/null; then
    echo "✓ $K already exists in Secret Manager (skipping)."
    continue
  fi
  read -rp "Configure $K now? [y/N] " ans
  case "$ans" in
    y|Y) bash "$HERE/add_key.sh" "$K" ;;
    *)   echo "  skipped $K" ;;
  esac
done

echo
# Print a ready --set-secrets snippet for whatever exists now, to paste on deploy.
MOUNT=()
for K in "${KEYS[@]}"; do
  if gcloud secrets describe "$K" &>/dev/null; then MOUNT+=("$K=$K:latest"); fi
done
if [[ ${#MOUNT[@]} -gt 0 ]]; then
  echo "To mount these on Cloud Run, add to your deploy --set-secrets:"
  printf '  --set-secrets="%s"\n' "$(IFS=,; echo "${MOUNT[*]}")"
fi
echo "Done. Providers stay dormant until their key exists; keyless ones already work."

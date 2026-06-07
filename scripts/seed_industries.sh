#!/data/data/com.termux/files/usr/bin/bash
# scripts/seed_industries.sh - Seed industry taxonomy into Firestore
set -euo pipefail

DRY_RUN=0
STORE_PATH="store/repository.py"
INDUSTRIES_PATH="industries/__init__.py"

usage() {
    echo "Usage: $0 [--dry-run]"
    exit 1
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dry-run) DRY_RUN=1; shift ;;
        *) usage ;;
    esac
done

echo "--- Seeding Industries ---"

if [[ ! -f "$STORE_PATH" ]]; then
    echo "Backend Gap: Missing $STORE_PATH. Taxonomy seeding unavailable."
    exit 0
fi

if [[ ! -f "$INDUSTRIES_PATH" ]]; then
    echo "Backend Gap: Missing $INDUSTRIES_PATH. Taxonomy seeding unavailable."
    exit 0
fi

if [[ $DRY_RUN -eq 1 ]]; then
    echo "[DRY-RUN] Would execute industry seeding logic."
    echo "[DRY-RUN] Logic: Iterate industries from $INDUSTRIES_PATH and save to Firestore 'industries' collection."
    exit 0
fi

# Real Run
echo "Executing industry seed logic via Python..."
python3 <<EOF
import sys
import os

# Add current dir to path for imports
sys.path.append(os.getcwd())

try:
    from industries import get_all_industries
    from store.repository import BaseRepository
    
    repo = BaseRepository("industries")
    industries = get_all_industries()
    
    print(f"Found {len(industries)} industries. Seeding...")
    
    for ind in industries:
        # Convert dataclass/object to dict
        data = {
            "key": ind.key,
            "label": ind.label,
            "description": getattr(ind, 'description', ''),
            "keywords": getattr(ind, 'keywords', [])
        }
        repo.save(ind.key, data)
        print(f"  - Seeded: {ind.key}")
        
    print("Success: Industry taxonomy seeded.")
except Exception as e:
    print(f"Error during seeding: {e}")
    sys.exit(1)
EOF

You are operating inside the Job Hunter Pro repo.

MISSION:
Perform R1 — Real Industry Taxonomy Engine.

ABSOLUTE RULES:
- Read all six authoritative Job Hunter Pro documents before editing.
- Read docs/REPAIR_MATRIX.md and scripts/current_truth_audit.py before editing.
- Do not deploy.
- Do not call live /api/jobs without dry_run=1.
- Do not call external APIs.
- Do not expose secrets.
- Do not rewrite app.py.
- Do not implement providers in this session.
- This session only fixes industries/.

MANDATORY DOCUMENTS:
- docs/AI_JOB_AGENT_1.txt
- docs/AI_JOB_AGENT_2.txt
- docs/AI_JOB_AGENT_3.txt
- docs/AI_JOB_AGENT_4.txt
- docs/AI_JOB_AGENT_5_UIUX_Handoff.md
- docs/AI_JOB_AGENT_6_S10_UIUX_SESSION_MASTERPLAN.md
- docs/REPAIR_MATRIX.md

GOAL:
Replace scaffold/placeholder industry logic with real deterministic six-industry taxonomies.

FILES TO INSPECT:
- industries/base.py
- industries/__init__.py
- industries/food_service.py
- industries/hospitality.py
- industries/care_social.py
- industries/sales.py
- industries/customer_service.py
- industries/retail_ops.py
- tests/test_industries_registry.py
- models/enums.py if needed
- models/search_result.py if needed

FILES ALLOWED TO CHANGE:
- industries/base.py
- industries/__init__.py
- industries/food_service.py
- industries/hospitality.py
- industries/care_social.py
- industries/sales.py
- industries/customer_service.py
- industries/retail_ops.py
- tests/test_industries_registry.py
- docs/REPAIR_MATRIX.md only to mark R1 status/proof

REQUIRED IMPLEMENTATION:
1. Define a real IndustryRoute model/dataclass/protocol in industries/base.py if not already real.
2. Each industry file must export one real route object:
   - food_service_route
   - hospitality_route
   - care_social_route
   - sales_route
   - customer_service_route
   - retail_ops_route
3. Each route must include:
   - key
   - label
   - queries
   - positive_terms
   - negative_terms
   - role_families
   - credentials
   - background_sensitive
   - remote_allowed
   - resolution_strategy
4. Implement deterministic helpers:
   - term_present exact token/phrase boundary, not substring matching
   - score_text_for_industry(text, route)
   - classify_text(text)
   - get_route(key)
   - get_all_routes()
   - list_industries()
5. Preserve the old food-service bug fix:
   - do not let "rn" inside ordinary words trigger registered nurse rejection.
   - negative matching must use phrase/token boundaries.
6. Six routes must exist:
   - food_service
   - hospitality
   - care_social
   - sales
   - customer_service
   - retail_ops
7. Tests must prove:
   - registry loads exactly 6 routes
   - food-service line cook/server/dishwasher classify as food_service
   - registered nurse does not become food_service
   - hospitality hotel banquet/front desk classify as hospitality
   - peer support/case aide/BHT classify as care_social
   - inbound call center/customer support classify as customer_service
   - sales representative/account rep classify as sales
   - cashier/stock/inventory classify as retail_ops
   - rn substring bug does not reject random normal words
8. No fake external data.
9. No provider calls.
10. No deploy.

PROOF COMMANDS TO RUN:
python3 -m py_compile industries/base.py industries/__init__.py industries/food_service.py industries/hospitality.py industries/care_social.py industries/sales.py industries/customer_service.py industries/retail_ops.py tests/test_industries_registry.py
python3 tests/test_industries_registry.py
python3 scripts/current_truth_audit.py

AFTER SUCCESS:
Update docs/REPAIR_MATRIX.md:
- Mark R1 complete.
- Record files changed.
- Record proof commands.
- Record no deploy.
- Record no API spend.

Then run:
git diff --stat
git diff -- industries tests/test_industries_registry.py docs/REPAIR_MATRIX.md | sed -n '1,320p'

If successful:
git add industries tests/test_industries_registry.py docs/REPAIR_MATRIX.md
git commit -m "R1 implement real industry taxonomy registry"

FINAL RESPONSE:
List:
- all six documents read
- files inspected
- files changed
- tests run
- audit count changes if any
- commit hash
- confirm no deploy
Stop.

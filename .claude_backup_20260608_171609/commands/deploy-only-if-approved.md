# /deploy-only-if-approved

Only run this if Michael explicitly says deploy.

Before deploy:
bash .claude/scripts/predeploy_proof.sh

After deploy:
bash .claude/scripts/cloud_run_health.sh

If health fails:
bash .claude/scripts/logs_on_fail.sh

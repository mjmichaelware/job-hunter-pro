#!/usr/bin/env bash

PROJECT_ID="ai-job-agent-498702"
PROJECT_NUMBER="1087899531014"
REGION="us-central1"
SERVICE="job-hunter-pro"
FAILED_BUILD_ID="2ab206e1-630d-42d2-9ae6-c7b1c9f8bc2b"

echo "=== FIX CLOUD BUILD TRIGGER DEPLOY PERMISSIONS ==="
echo "PWD=$(pwd)"
echo

echo "=== 1) Confirm local repo and compile before touching deploy path ==="
if [ ! -f app.py ]; then
  echo "ERROR: not in repo root"
  exit 1
fi

python3 -m py_compile $(git ls-files '*.py')
if [ $? -ne 0 ]; then
  echo "ERROR: python compile failed. Not touching IAM."
  exit 1
fi

echo
echo "=== 2) Read exact failed build identity ==="
gcloud builds describe "$FAILED_BUILD_ID" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --format="yaml(id,status,serviceAccount,buildTriggerId,substitutions.TRIGGER_NAME,sourceProvenance.resolvedRepoSource.commitSha)"

BUILD_SA_FULL="$(gcloud builds describe "$FAILED_BUILD_ID" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --format='value(serviceAccount)')"

BUILD_TRIGGER_ID="$(gcloud builds describe "$FAILED_BUILD_ID" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --format='value(buildTriggerId)')"

BUILD_SA="${BUILD_SA_FULL##*/}"

if [ -z "$BUILD_SA" ]; then
  echo "WARN: build serviceAccount field empty; using project compute default Cloud Build executor"
  BUILD_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"
fi

if [ -z "$BUILD_TRIGGER_ID" ]; then
  echo "ERROR: could not read buildTriggerId from failed build"
  exit 1
fi

echo "BUILD_SA=$BUILD_SA"
echo "BUILD_TRIGGER_ID=$BUILD_TRIGGER_ID"

echo
echo "=== 3) Read exact Cloud Run runtime service identity ==="
RUNTIME_SA="$(gcloud run services describe "$SERVICE" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --format='value(spec.template.spec.serviceAccountName)')"

if [ -z "$RUNTIME_SA" ]; then
  echo "WARN: runtime service account empty; falling back to scheduler SA used by this app"
  RUNTIME_SA="job-hunter-scheduler@${PROJECT_ID}.iam.gserviceaccount.com"
fi

echo "RUNTIME_SA=$RUNTIME_SA"

echo
echo "=== 4) Print exact deploy denial lines from failed build ==="
gcloud builds log "$FAILED_BUILD_ID" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  | grep -iE "Deploying container|PERMISSION_DENIED|denied|permission|iam.serviceAccounts.actAs|run.services|ERROR" || true

echo
echo "=== 5) Grant exact build SA deploy permissions ==="
for ROLE in \
  roles/run.admin \
  roles/run.sourceDeveloper \
  roles/serviceusage.serviceUsageConsumer \
  roles/artifactregistry.writer \
  roles/artifactregistry.reader \
  roles/secretmanager.secretAccessor
do
  echo "Granting $ROLE to $BUILD_SA"
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:${BUILD_SA}" \
    --role="$ROLE" \
    --condition=None
done

echo
echo "Granting iam.serviceAccountUser on runtime SA to exact build SA"
gcloud iam service-accounts add-iam-policy-binding "$RUNTIME_SA" \
  --project="$PROJECT_ID" \
  --member="serviceAccount:${BUILD_SA}" \
  --role="roles/iam.serviceAccountUser"

echo
echo "=== 6) IAM proof for exact build SA ==="
gcloud projects get-iam-policy "$PROJECT_ID" \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:${BUILD_SA}" \
  --format="table(bindings.role,bindings.members)"

echo
echo "=== 7) Runtime SA actAs proof ==="
gcloud iam service-accounts get-iam-policy "$RUNTIME_SA" \
  --project="$PROJECT_ID" \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount:${BUILD_SA}" \
  --format="table(bindings.role,bindings.members)"

echo
echo "=== 8) Rerun the same GitHub trigger without changing code ==="
gcloud builds triggers run "$BUILD_TRIGGER_ID" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --branch=main

echo
echo "Waiting for new build to appear..."
sleep 12

NEW_BUILD_ID="$(gcloud builds list \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --limit=1 \
  --format='value(id)')"

echo "NEW_BUILD_ID=$NEW_BUILD_ID"

echo
echo "=== 9) Wait for new build result ==="
FINAL_STATUS=""
for i in $(seq 1 60); do
  STATUS="$(gcloud builds describe "$NEW_BUILD_ID" \
    --project="$PROJECT_ID" \
    --region="$REGION" \
    --format='value(status)' 2>/dev/null)"

  echo "[$i/60] build status: $STATUS"

  case "$STATUS" in
    SUCCESS|FAILURE|CANCELLED|TIMEOUT)
      FINAL_STATUS="$STATUS"
      break
      ;;
  esac

  sleep 10
done

echo
echo "FINAL_STATUS=$FINAL_STATUS"

if [ "$FINAL_STATUS" != "SUCCESS" ]; then
  echo
  echo "=== NEW BUILD FAILED: exact failure lines ==="
  gcloud builds log "$NEW_BUILD_ID" \
    --project="$PROJECT_ID" \
    --region="$REGION" \
    | tail -n 140
  exit 1
fi

echo
echo "=== 10) Cloud Run live proof ==="
gcloud run services describe "$SERVICE" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --format="table(status.url,status.latestReadyRevisionName,status.traffic[0].revisionName,status.traffic[0].percent)"

SERVICE_URL="$(gcloud run services describe "$SERVICE" \
  --project="$PROJECT_ID" \
  --region="$REGION" \
  --format='value(status.url)')"

echo "SERVICE_URL=$SERVICE_URL"

echo
echo "=== 11) Health proof ==="
curl -fsS "${SERVICE_URL}/api/health"
echo

echo
echo "=== 12) Live drawer/canvas proof ==="
echo "--- canvas ids ---"
curl -fsS "$SERVICE_URL/" | grep -o 'id="webgpu-canvas"\|ambient-canvas' | sort | uniq -c || true

echo "--- filters exist and should be fixed by frontend commit, not IAM ---"
curl -fsS "$SERVICE_URL/" | grep -o 'filter-drawer\|toggle-filters' | sort | uniq -c || true

echo
echo "DONE: trigger deploy permission path fixed and live service verified."

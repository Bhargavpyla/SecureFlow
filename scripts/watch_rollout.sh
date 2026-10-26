#!/usr/bin/env bash
# Run this ON the machine that has kubectl access to the cluster (VM or your laptop).
# It watches for a new image tag (put there by Argo CD) and records the SYNC outcome.
# needs: NEON_URL, NTFY_TOPIC env vars, psql, kubectl
LAST=""
while true; do
  IMG=$(kubectl get deploy secureflow-app -o jsonpath='{.spec.template.spec.containers[0].image}' 2>/dev/null)
  if [ -n "$IMG" ] && [ "$IMG" != "$LAST" ]; then
    LAST="$IMG"; TAG="${IMG##*:}"
    if kubectl rollout status deploy/secureflow-app --timeout=120s; then
      S="healthy"; MSG="Deployment $TAG is live (zero-downtime rollout complete)"
    else
      S="stalled"; MSG="Deployment $TAG FAILED readiness - old version still serving"
    fi
    psql "$NEON_URL" -q -v tag="$TAG" -v s="$S" -v d="$MSG" <<'SQL'
INSERT INTO deployments(image_tag, status, details) VALUES (:'tag', :'s', :'d');
SQL
    curl -s -H "Title: SecureFlow deploy" -d "$MSG" "https://ntfy.sh/$NTFY_TOPIC" >/dev/null
  fi
  sleep 10
done

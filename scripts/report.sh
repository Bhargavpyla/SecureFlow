#!/usr/bin/env bash
# usage: report.sh <STAGE> <status> [details]   -> writes one row to stage_events
# Never fails the pipeline: DB trouble must not block a release.
psql "$NEON_URL" -q -v run="$GITHUB_RUN_ID" -v stage="$1" -v status="$2" -v details="${3:-}" <<'SQL' || true
INSERT INTO stage_events(run_id, stage, status, details) VALUES (:'run', :'stage', :'status', :'details');
SQL

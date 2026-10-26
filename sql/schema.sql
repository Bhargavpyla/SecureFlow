CREATE TABLE IF NOT EXISTS pipeline_runs (
  run_id text PRIMARY KEY, commit_sha text, commit_msg text, actor text,
  status text DEFAULT 'running', started_at timestamptz DEFAULT now(), finished_at timestamptz);
CREATE TABLE IF NOT EXISTS stage_events (
  id serial PRIMARY KEY, run_id text, stage text, status text, details text,
  created_at timestamptz DEFAULT now());
CREATE TABLE IF NOT EXISTS scan_results (
  id serial PRIMARY KEY, run_id text, image text,
  critical int, high int, medium int, low int, gate_passed boolean,
  created_at timestamptz DEFAULT now());
CREATE TABLE IF NOT EXISTS deployments (
  id serial PRIMARY KEY, run_id text, image_tag text, status text, details text,
  created_at timestamptz DEFAULT now());

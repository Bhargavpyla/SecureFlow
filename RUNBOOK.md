# SecureFlow one-day runbook

Replace YOUR_GITHUB_USERNAME in `k8s/deployment.yaml` and `argocd/application.yaml`.

## A. Accounts and secrets (30 min)
1. Create TWO public GitHub repos: `secureflow-app`, `secureflow-manifests`. Push the matching folders.
2. Neon: create a project, copy the connection string (has `sslmode=require`). Run `sql/schema.sql` in Neon's SQL editor.
3. Pick a hard-to-guess ntfy topic (e.g. `secureflow-bhargav-8431`), subscribe to it in the ntfy phone app or ntfy.sh web.
4. GitHub fine-grained PAT: access ONLY to `secureflow-manifests`, permission Contents: Read and write.
5. In `secureflow-app` -> Settings -> Secrets -> Actions add: `NEON_URL`, `NTFY_TOPIC`, `MANIFEST_PAT`.

## B. Cluster + Argo CD (1-2 h)
Local fallback (k3d, needs Docker):
    k3d cluster create secureflow --agents 1 -p "30080:30080@agent:0"
Cloud VM: install k3s with `curl -sfL https://get.k3s.io | sh -`, open port 30080.

Install Argo CD:
    kubectl create namespace argocd
    kubectl apply -n argocd --server-side -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
    kubectl apply -f argocd/application.yaml

## C. First run
1. Push any commit to `secureflow-app` main. Watch Actions.
2. After the first successful PUBLISH: GitHub -> Your profile -> Packages -> secureflow-app -> Package settings -> set visibility PUBLIC (otherwise the cluster cannot pull it).
3. Argo CD checks git every ~3 min. To speed up: `kubectl -n argocd annotate app secureflow argocd.argoproj.io/refresh=hard --overwrite` or click Refresh in the UI.
4. On the cluster machine run: `export NEON_URL=... NTFY_TOPIC=...; ./scripts/watch_rollout.sh`

## D. Demo script
1. Zero downtime: in a terminal run
       while true; do curl -s -o /dev/null -w "%{http_code}\n" localhost:30080/health; sleep 0.5; done
   change `APP_VERSION` or any app line, push, and show it stays 200 during the rollout.
2. Gate blocks: change Dockerfile to `FROM python:3.8`, push. Show red SCAN stage, ntfy alert, DB row with gate_passed=false, and that nothing reached the cluster.
3. Bad release stalls safely: in the MANIFESTS repo change readinessProbe path to `/nope`, push. New pod never becomes Ready, old pods keep serving (curl loop stays 200). Fix with `git revert`.

## E. Things that commonly bite
- Trivy DB download can hit a GHCR rate limit; just re-run the job.
- If `python:3.12-slim` shows HIGH findings, bump to the newest patch tag or add `RUN apt-get update && apt-get upgrade -y`. Check this EARLY (hour 3), not at demo time.
- Rolling back is not automatic with plain Argo CD. Describe it as "failed rollouts stall while the old version keeps serving; recovery is `git revert`".

## Added a line
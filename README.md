# paas-migrate

Registers Hanzo services on the PaaS (**platform.hanzo.ai**) via its API and
triggers a deploy — so they build/run **through the platform** (not GitHub
Actions) and show up in the one dashboard with monitoring.

## Run
```sh
# 1. mint a key: platform.hanzo.ai -> Settings -> API Keys
export X_API_KEY=...        # the only human step (per-user by design)
python3 migrate.py services.yaml
```
Edit `services.yaml` to list every service. Reruns are safe.

## In-cluster (token never leaves the cluster)
`kubectl apply -f job.yaml` runs it on hanzo-k8s, reading the key from a
secret you name — the value is never printed or handled outside the cluster.

After migrating, retire each repo's `.github/workflows/deploy-*.yml` (the PaaS
auto-deploys on push). CI = `make ci` as a platform Scheduled Task.

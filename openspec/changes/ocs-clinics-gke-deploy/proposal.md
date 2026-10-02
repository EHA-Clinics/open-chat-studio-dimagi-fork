# Proposal

## Why

Open Chat Studio must run on EHA Clinics GKE (`clinics-dev-359913` / `eha-clinics-dev`) beside AdhereBot. Deploy must start **from this application repository** so the image is built from the same Git SHA operators ship. Clinics already standardizes on the reusable workflow `EHA-Clinics/eha-workflow` (and/or `eHealthAfrica/eha-workflow` once the clinics cluster is registered upstream) plus published **`eha-chart/generic3` 0.5.7**. A separate wrong-place OpenSpec on `dimagi-ocs` was closed; planning belongs here.

## What Changes

- Add OpenSpec planning (this change) and, on apply, an eha-workflow **caller** + `deployments/dev.pipeline.yaml` in **this repo**.
- Deploy OCS workloads with **`eha-chart/generic3` version `0.5.7`** from `https://ehealthafrica.github.io/helm-charts/` (multi-release: web, celery-worker, celery-beat; Redis via Bitnami or Memorystore).
- Target cluster registry key **`eha-clinics-dev-gke`**, namespace **`ocs-dev`**, registry **`eu.gcr.io/clinics-dev-359913`**, Ingress host **`ocs-dev.eha.ng`**.
- Treat `EHA-Clinics/dimagi-ocs` as the Clinics **ops/packaging companion** (existing custom chart + secrets examples). This plan **does not** use that custom chart as the primary install vehicle; apply may optionally vendor reference values from it. **BREAKING (ops):** supersedes `dimagi-ocs` `deploy-ocs-helm.yml` as the default deploy path for Clinics.
- Document WIF: this repo is under **`eHealthAfrica`**, so clinics-dev WIF must allow `repository_owner == eHealthAfrica` (or a repo-scoped principal) — today’s Clinics pool was bootstrapped for `EHA-Clinics` only.

## Capabilities

### New Capabilities

- `ocs-eha-workflow-deploy`: Caller workflow + pipeline in `open-chat-studio` that builds the OCS image and deploys via eha-workflow to `eha-clinics-dev-gke`.
- `ocs-generic3-clinics-workloads`: generic3 (and Redis) values/process mapping for web, celery worker, celery beat, migrate gate, Cloud SQL/pgvector, Ingress, and secrets for Clinics `ocs-dev`.

### Modified Capabilities

- (none — no existing `openspec/specs/` inventory in this repo)

## Impact

- **This repo:** `openspec/`, later `.github/workflows/deploy.yaml`, `deployments/`; no change to OCS product behavior for non-Clinics hosts (Heroku/ECS remain).
- **`EHA-Clinics/dimagi-ocs`:** custom chart remains available but is not the primary Clinics install path under this plan.
- **`eha-workflow`:** requires `clusters/eha-clinics-dev-gke.yaml` on the workflow repo that this caller pins (upstream and/or Clinics fork).
- **GCP:** Cloud SQL DB `open_chat_studio` + pgvector, Redis, DNS, Traefik TLS, Environment secrets for WIF.
- **AdhereBot:** later points `OCS_BASE_URL` at `https://ocs-dev.eha.ng`.

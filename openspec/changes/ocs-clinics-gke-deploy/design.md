# Design

## Context

See `proposal.md`. Clinics AdhereBot already uses `EHA-Clinics/eha-workflow` + `eha-chart/generic3@0.5.7` with Cloud SQL and Vault-synced secrets (`vaultextrasecrets` / `env_secrets`).

**Postgres target (verified live on clinics-dev):** Cloud SQL instance **`eha-clinics-dev`** — `POSTGRES_14`, `europe-west1`, connection name `clinics-dev-359913:europe-west1:eha-clinics-dev`, tier `db-custom-2-3840`, shared multi-app instance (many existing DBs; no OCS DB yet). Cluster Vault UI is **`https://vault-dev.eha.ng`**. Operators create the OCS DB/user + Vault `DATABASE_URL` after deploy scaffolding is live.

## Goals / Non-Goals

**Goals:**
- Clinics install path owned by `open-chat-studio` CI (build SHA = deploy SHA).
- App processes on **generic3**; **only Redis** as an extra Helm chart dependency.
- **Postgres = existing Cloud SQL `eha-clinics-dev`** (not chart-owned Postgres).
- Secrets via **Vault → K8s Secret**, referenced from generic3 values (credentials can land later).
- Clarify dimagi-ocs as companion, not primary chart.

**Non-Goals:**
- Deploying in-cluster Postgres/pgvector StatefulSet or CNPG from Helm.
- Memorystore Redis for v1 (Bitnami Redis chart is enough unless platform prefers Memorystore later).
- Replacing Heroku/ECS for non-Clinics.
- Meta WABA bootstrap in CI.

## Decisions

### 1. App chart = generic3; datastore chart = Redis only
- **Choice:** `eha-chart/generic3` `0.5.7` for web / celery-worker / celery-beat. **Bitnami Redis** under eha-workflow `helm_charts` for broker/cache.
- **Why:** OCS needs Redis for Celery; Postgres is already provided by Cloud SQL. No second Postgres in the cluster.
- **Not used from charts:** any Postgres/pgvector StatefulSet (including dimagi-ocs chart data plane).

### 2. Postgres = Cloud SQL `eha-clinics-dev` (POSTGRES_14)
- **Choice:** Reuse the existing instance — not a new Cloud SQL server and not an in-cluster Postgres chart.
  | Field | Value |
  |---|---|
  | Instance | [`eha-clinics-dev`](https://console.cloud.google.com/sql/instances/eha-clinics-dev/overview?project=clinics-dev-359913) |
  | Project | `clinics-dev-359913` |
  | Region | `europe-west1` |
  | `databaseVersion` | `POSTGRES_14` |
  | Connection name | `clinics-dev-359913:europe-west1:eha-clinics-dev` |
  | generic3 wiring | `database.instance` → Auth Proxy sidecar on web/worker/beat |
  | App DB/role | Dedicated (recommended name `open_chat_studio`); separate from AdhereBot and other tenants on this instance |
- **Credentials timing:** First deploys MAY ship with Secret placeholders or omit Ready until Vault is filled; operator creates DB/user + writes Vault keys **later** (Vault UI `https://vault-dev.eha.ng`, path under `kv/ehaclinics/dev/...`), then VSO/rollout picks them up — no requirement to commit secrets in the apply PR.
- **pgvector:** On the OCS database run `CREATE EXTENSION IF NOT EXISTS vector;` (Cloud SQL PG14 supports pgvector; confirm extension ≥ 0.7 if halfvec is used). Out-of-band SQL/ops step before migrate.

### 3. Vault credentials (yes — chart supports it)
- **Choice:** Use generic3 **`vaultextrasecrets`** (+ **`env_secrets`**) exactly as Clinics apps do (e.g. AdhereBot): values name Vault paths and Secret names; pods consume env from synced Secrets.
- **Typical keys (illustrative, not committed):** `DATABASE_URL`, `SECRET_KEY`, `CRYPTOGRAPHY_KEY`, `CRYPTOGRAPHY_SALT`, email/LLM keys, `REDIS_URL` if not composed from in-cluster Redis auth Secret.
- **Why:** Updating Vault updates the Secret and can trigger rollout; Helm values stay non-secret.
- **Alternative:** Manual `kubectl apply` of a Secret — allowed as bootstrap, but Vault is the documented steady state.

### 4. Workflow pin + WIF
- Prefer pin with `eha-clinics-dev-gke` (e.g. `EHA-Clinics/eha-workflow@v15.0.5-clinics` or upstream after cluster merge).
- Extend WIF so `eHealthAfrica/open-chat-studio` can impersonate the clinics deploy SA.

### 5. Namespace / hostname / migrate / branch
- Namespace `ocs-dev`, host `ocs-dev.eha.ng`.
- Migrate Job with same image tag; gate web success on migrate.
- `git_branch: develop` + `workflow_dispatch` for `dev`.

## Risks / Trade-offs

- **[Risk] Pods CrashLoop until Vault/DB creds exist** → Mitigation: document ordered cutover (deploy Redis + apps → create DB/user → fill Vault → restart/rollout); optional initial dry-run / scaled-to-zero until secrets present.
- **[Risk] WIF denies eHealthAfrica owner** → Mitigation: update pool binding before first deploy.
- **[Risk] pgvector missing on Cloud SQL** → Mitigation: ops checklist before migrate.
- **[Trade-off] Bitnami Redis vs Memorystore** → Start Bitnami in `ocs-dev`; swap `REDIS_URL` via Vault later if Memorystore is provisioned.

## Migration Plan

1. Merge this OpenSpec; apply pipeline/values (Vault paths declared, secrets empty or stub).
2. Deploy Redis + app releases (may be unhealthy until DB URL exists).
3. On Cloud SQL `eha-clinics-dev` (`POSTGRES_14`): create dedicated OCS database/user; `CREATE EXTENSION vector`; write `DATABASE_URL` to Vault at `https://vault-dev.eha.ng` under `kv/ehaclinics/dev/...`.
4. Confirm Secret sync + migrate Job; smoke test.
5. Point AdhereBot at `https://ocs-dev.eha.ng`; deprecate dimagi-ocs deploy as default.

## Open Questions

- Exact eha-workflow pin (Clinics fork vs upstream) — resolve at apply if both register `eha-clinics-dev-gke`.
- Vault mount/path naming for OCS (`ehaclinics/dev/open-chat-studio` vs similar) — choose at apply to match Clinics Vault layout.

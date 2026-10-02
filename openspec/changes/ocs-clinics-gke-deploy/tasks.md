# Tasks

## 1. Platform prerequisites (document + configure)

- [ ] 1.1 Document WIF binding for `eHealthAfrica/open-chat-studio` on clinics-dev and verify Environment `dev` can list `GCP_WORKLOAD_IDENTITY_PROVIDER` and `GCP_SERVICE_ACCOUNT`
- [ ] 1.2 Confirm pinned eha-workflow ref includes `eha-clinics-dev-gke` and verify resolve names that cluster
- [ ] 1.3 Document the **chosen Postgres target** in `docs/hosting/clinics-gke.md` (or equivalent) and verify the doc exists: Cloud SQL `eha-clinics-dev` (`POSTGRES_14`, `clinics-dev-359913:europe-west1:eha-clinics-dev`), create dedicated OCS DB/user + `CREATE EXTENSION vector` **when ready**, Vault at `https://vault-dev.eha.ng` with path/key list for `DATABASE_URL` and app secrets, DNS `ocs-dev.eha.ng`
- [ ] 1.4 Document that first deploy may precede Vault credential fill, and verify the cutover order (Redis+apps → create DB on `eha-clinics-dev` → Vault DB creds → migrate → smoke) is written down

## 2. Pipeline and caller in this repo

- [ ] 2.1 Add `deployments/dev.pipeline.yaml` with generic3 app components (web/worker/beat), **Bitnami Redis only** under `helm_charts` (no Postgres chart), `cluster: eha-clinics-dev-gke`, `namespace: ocs-dev`, `chart_version: "0.5.7"` and verify YAML is valid
- [ ] 2.2 Add `.github/workflows/deploy.yaml` calling pinned `build-deploy.yaml` with `secrets: inherit` and verify workflow parses
- [ ] 2.3 Create or document `develop` / `workflow_dispatch` mapping and verify it matches `git_branch`

## 3. generic3 values, Redis, Vault, migrate

- [ ] 3.1 Add `deployments/dev/web.yaml` with Cloud SQL instance `clinics-dev-359913:europe-west1:eha-clinics-dev`, Ingress `ocs-dev.eha.ng`, and `vaultextrasecrets` / `env_secrets` stubs (no plaintext secrets) and verify `helm template` against generic3 `0.5.7` succeeds
- [ ] 3.2 Add `celery-worker.yaml` and `celery-beat.yaml` (beat replicas=1) sharing Vault/Secret contract and verify `helm template` succeeds
- [ ] 3.3 Add `deployments/dev/redis.yaml` (Bitnami) and verify worker/web values can form or reference `REDIS_URL`
- [ ] 3.4 Add migrate Job wired to the pipeline and verify dry-run or pipeline reference exists (runs once DB Secret is present)

## 4. Companion repo and docs

- [ ] 4.1 Note that `dimagi-ocs` custom chart / in-cluster Postgres is not used on this path and verify the note is present
- [ ] 4.2 Smoke-test checklist: HTTPS, Redis, Cloud SQL connect after Vault fill, migrate, webhook URL shape — verify linked from Clinics deploy doc

## 5. Validation

- [ ] 5.1 Run `openspec validate ocs-clinics-gke-deploy --strict` and verify it passes
- [ ] 5.2 After apply, verify deploy logs show generic3 for apps, a Redis chart component, cluster `eha-clinics-dev-gke`, and no Postgres Helm chart install

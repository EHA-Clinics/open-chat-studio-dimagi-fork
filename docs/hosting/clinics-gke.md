# Clinics GKE (eha-clinics-dev)

Deploy Open Chat Studio to EHA Clinics GKE from **this repository** via
`EHA-Clinics/eha-workflow` + `eha-chart/generic3` **0.5.7**.

This path supersedes [EHA-Clinics/dimagi-ocs](https://github.com/EHA-Clinics/dimagi-ocs)
`deploy-ocs-helm.yml` / in-cluster Postgres as the default Clinics install.

## Targets

| Item | Value |
|------|--------|
| GCP project | `clinics-dev-359913` |
| GKE cluster | `eha-clinics-dev` (`europe-west1-b`) — pipeline name `eha-clinics-dev-gke` |
| Namespace | `ocs-dev` |
| Public hostname | `ocs-dev.eha.ng` (OCS admin UI + webhooks — **not** AdhereBot) |
| Image registry | `eu.gcr.io/clinics-dev-359913` |
| Git branch | `develop` (+ `workflow_dispatch` environment `dev`) |
| Workflow pin | `EHA-Clinics/eha-workflow@v15.0.5-clinics` |
| Vault | `https://vault-dev.eha.ng` — KV under `ehaclinics/dev/open-chat-studio` |

## Platform prerequisites

### WIF (GitHub Environment `dev`)

1. Bind Workload Identity Federation so `eHealthAfrica/open-chat-studio` can
   impersonate the clinics deploy service account (pool was originally
   EHA-Clinics–oriented — extend attribute conditions / repo allowlist).
2. On this repo, Environment **`dev`** secrets:
   - `GCP_WORKLOAD_IDENTITY_PROVIDER`
   - `GCP_SERVICE_ACCOUNT`
3. Add this repo to the EHA-Clinics runner group **`clinics-dev`** (label
   `clinics-dev-runners`) as required by the cluster registry entry.

### eha-workflow pin

Confirm the pin includes `clusters/eha-clinics-dev-gke.yaml`
(`v15.0.5-clinics` on `EHA-Clinics/eha-workflow`).

### Cloud SQL

| Field | Value |
|-------|--------|
| Instance | [`eha-clinics-dev`](https://console.cloud.google.com/sql/instances/eha-clinics-dev/overview?project=clinics-dev-359913) |
| Version | `POSTGRES_14` |
| Connection name | `clinics-dev-359913:europe-west1:eha-clinics-dev` |

When ready (before first successful migrate):

```sql
-- as cloudsqlsuperuser / admin
CREATE USER open_chat_studio WITH PASSWORD '...';
CREATE DATABASE open_chat_studio OWNER open_chat_studio;
\c open_chat_studio
CREATE EXTENSION IF NOT EXISTS vector;
```

Do **not** reuse AdhereBot or other app databases.

`DATABASE_URL` for pods using the Auth Proxy sidecar should target
`127.0.0.1:5432` (or the proxy socket), with TLS settings appropriate for the
proxy path (`sslmode=disable` to local proxy is common; confirm against Clinics
apps).

### DNS / TLS

Point `ocs-dev.eha.ng` at the clinics-dev Traefik load balancer (same pattern as
other `*-dev.eha.ng` hosts). Ingress uses cert-manager issuer `letsencrypt`
(dns01 / route53), matching AdhereBot.

### Vault paths (no plaintext in git)

Suggested layout on `vault-dev.eha.ng`:

| Secret name (K8s) | Vault path | Keys |
|-------------------|------------|------|
| `open-chat-studio` | `ehaclinics/dev/open-chat-studio` | See required env below |
| `database-credentials` | `ehaclinics/dev/open-chat-studio/database-credentials` | DB user/password (generic3 db init / proxy) |
| `cloudsql-instance-credentials` | `ehaclinics/dev/open-chat-studio/cloudsql-instance-credentials` | Cloud SQL client SA JSON if required by chart |

**Required app keys** (in `open-chat-studio` Vault secret / env):

- `DJANGO_SETTINGS_MODULE=config.settings_production`
- `SECRET_KEY`
- `DATABASE_URL`
- `REDIS_URL` (or compose from Bitnami Redis auth once known)
- `DJANGO_ALLOWED_HOSTS=ocs-dev.eha.ng`
- `CSRF_TRUSTED_ORIGINS=https://ocs-dev.eha.ng`
- `CRYPTOGRAPHY_KEY`, `CRYPTOGRAPHY_SALT`
- Email: Mailgun/SES keys **or** temporary `ACCOUNT_EMAIL_VERIFICATION=none` for a closed pilot
- Optional: `HEALTH_CHECK_TOKENS`, `OCS_VERSION` (runtime override if image bake-in is `unknown`)
- Traefik edge: set `DJANGO_SECURE_SSL_REDIRECT=False` when TLS terminates at Ingress (Clinics pattern); keep CSRF/hosts as above
- Optional: `RATE_LIMIT_TRUSTED_PROXY_COUNT=1` (or Clinics-standard count) behind Traefik

### Object storage (this repo)

Terraform: [`terraform/clinics-dev-ocs-storage/`](../../terraform/clinics-dev-ocs-storage/)  
Workflow: [Clinics OCS storage (Terraform)](../../.github/workflows/clinics-ocs-storage.yml)

1. One-time: GCS state bucket `clinics-dev-359913-terraform-state`.
2. WIF SA roles (minimum): `roles/storage.admin`, `roles/iam.serviceAccountAdmin`,
   `roles/iam.serviceAccountKeyAdmin`.
3. Actions → **Clinics OCS storage (Terraform)** → `apply`.
4. Put `vault_env_snippet` + HMAC into Vault; set `USE_S3_STORAGE=True` when
   media / WhatsApp voice is required (optional for admin-only smoke).
5. Prefer **web replicas = 1** until S3 is enabled (local media is not shared).

## Cutover order

1. Merge Clinics deploy wiring; ensure Environment `dev` WIF secrets exist.
2. Deploy Redis + app releases (may be unhealthy until Vault DB URL exists).
3. Create Cloud SQL DB/user + `vector`; fill Vault.
4. Confirm VSO Secret sync; run migrate (CronJob → `kubectl create job --from=cronjob/...` or wait for schedule).
5. Bootstrap (manual):
   ```bash
   kubectl -n ocs-dev exec -it deploy/ocs-web-dev -- python manage.py createsuperuser
   ```
   Then in admin: create a **Team**; set Django **Site** domain to `ocs-dev.eha.ng`.
6. Smoke: HTTPS admin login, CSRF OK, `/status/?token=...`, Redis + Cloud SQL.
7. Optional: AdhereBot `OCS_BASE_URL=https://ocs-dev.eha.ng` (OCS URL — AdhereBot keeps its own hostname).
8. Optional: LLM providers / channels in admin; object storage workflow when needed.

## Pipeline layout

| File | Role |
|------|------|
| `.github/workflows/deploy-clinics.yaml` | eha-workflow caller (`build-deploy` @ `v15.0.5-clinics`) |
| `.github/workflows/deploy.yml` | Dimagi Amazon ECS — **unchanged**, not used for Clinics |
| `.github/workflows/clinics-ocs-storage.yml` | GCS buckets Terraform |
| `deployments/dev.pipeline.yaml` | Cluster, components, Redis chart |
| `deployments/dev/*.yaml` | generic3 / Bitnami values |

## Processes

- **web** — gunicorn (Dockerfile CMD); Ingress `ocs-dev.eha.ng`; probe `/status/`
- **celery-worker** — single worker, all queues (no `-Q`)
- **celery-beat** — replicas = 1
- **migrate** — CronJob `python manage.py migrate --noinput` (create Job from CronJob for first run)
- **redis** — Bitnami chart only (no Postgres chart)

## Smoke checklist

- [ ] `https://ocs-dev.eha.ng` admin login (CSRF OK behind Traefik)
- [ ] `/status/?token=...` healthy
- [ ] Migrate completed
- [ ] Redis reachable from worker
- [ ] Cloud SQL via Auth Proxy
- [ ] Site domain = `ocs-dev.eha.ng`
- [ ] Team exists; superuser can configure LLM/channels

## AdhereBot → OCS

Default: `OCS_BASE_URL=https://ocs-dev.eha.ng`  
Optional later: in-cluster Service DNS to the OCS web Service in `ocs-dev`.

# Tasks

## 1. Platform prerequisites (document + configure)

- [ ] 1.1 Document WIF binding for `eHealthAfrica/open-chat-studio` on clinics-dev (extend pool condition or repo principal) and verify Environment `dev` can list `GCP_WORKLOAD_IDENTITY_PROVIDER` and `GCP_SERVICE_ACCOUNT`
- [ ] 1.2 Confirm pinned eha-workflow ref includes `eha-clinics-dev-gke` (Clinics fork tag or upstream after merge) and verify resolve against that ref names the cluster
- [ ] 1.3 Document Cloud SQL DB/user + pgvector, Redis choice, DNS `ocs-dev.eha.ng`, and Secret/Vault key list in `docs/hosting/clinics-gke.md` (or equivalent) and verify the doc exists

## 2. Pipeline and caller in this repo

- [ ] 2.1 Add `deployments/dev.pipeline.yaml` (`service_name`, `git_branch: develop`, `image_registry: clinics-dev-359913`, `cluster: eha-clinics-dev-gke`, `namespace: ocs-dev`, `chart_version: "0.5.7"`, build component for web image, services for web/worker/beat/+redis) and verify YAML is valid and file names match values
- [ ] 2.2 Add `.github/workflows/deploy.yaml` calling pinned `build-deploy.yaml` with `secrets: inherit` (push `develop` + `workflow_dispatch`) and verify workflow parses
- [ ] 2.3 Create `develop` branch tracking policy (or document dispatch-only until created) and verify trigger mapping matches `git_branch`

## 3. generic3 values and migrate

- [ ] 3.1 Add `deployments/dev/web.yaml` (gunicorn, port 8000, Ingress `ocs-dev.eha.ng`, Traefik/cert-manager, Cloud SQL proxy, secret refs) and verify `helm template` with `eha-chart/generic3` `0.5.7` succeeds
- [ ] 3.2 Add `deployments/dev/celery-worker.yaml` and `celery-beat.yaml` (beat replicas=1) and verify `helm template` succeeds for both
- [ ] 3.3 Add Redis Bitnami values or Memorystore-only `REDIS_URL` documentation and verify worker values reference the broker
- [ ] 3.4 Add migrate Job/manifest wired into the pipeline and verify dry-run apply or pipeline reference exists

## 4. Companion repo and docs

- [ ] 4.1 Add a short note in Clinics deploy doc that `EHA-Clinics/dimagi-ocs` custom chart/`deploy-ocs-helm.yml` is not the primary path and verify the note is present
- [ ] 4.2 Extend smoke-test checklist (HTTPS admin, migrate, Redis, WhatsApp webhook URL shape) and verify checklist is linked from the Clinics deploy doc

## 5. Validation

- [ ] 5.1 Run `openspec validate ocs-clinics-gke-deploy --strict` and verify it passes
- [ ] 5.2 After apply merge, run Deploy for `dev` and verify logs show `chart: eha-chart/generic3` and `chart_version: 0.5.7` with cluster `eha-clinics-dev-gke`

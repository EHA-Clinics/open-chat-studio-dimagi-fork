# Design

## Context

See `proposal.md`. This repo already has a production `Dockerfile` and Compose/ECS deploy paths. Clinics GKE deploy for AdhereBot uses `EHA-Clinics/eha-workflow` + `eha-chart/generic3@0.5.7` on `eha-clinics-dev-gke`. `EHA-Clinics/dimagi-ocs` holds a custom umbrella chart and a hand-rolled Helm GHA; that OpenSpec PR was closed so planning lives here (deploy-from app repo).

## Goals / Non-Goals

**Goals:**
- Clinics install path owned by `open-chat-studio` CI (build SHA = deploy SHA).
- Use eha-workflow + generic3 0.5.7 multi-release (web / worker / beat).
- Align with AdhereBot networking (Traefik, Cloud SQL preference, WIF).
- Clarify dimagi-ocs as companion, not primary chart.

**Non-Goals:**
- Replacing Heroku/ECS/Dimagi AWS deploy for non-Clinics environments.
- Implementing Meta WABA / experiment bootstrap in CI.
- Multi-region HA.

## Decisions

### 1. Primary chart = generic3 (not dimagi-ocs umbrella)
- **Choice:** `eha-chart/generic3` `0.5.7` with one Helm release per process.
- **Why:** Matches Clinics platform and prior direction; eha-workflow’s default for `build_components`; avoids maintaining a parallel umbrella chart as the install source of truth in two repos.
- **Alternative:** Helm-upgrade `EHA-Clinics/dimagi-ocs` `charts/open-chat-studio` after image build — rejected as primary (duplicates platform chart concerns; weaker fit to eha-workflow component matrix). dimagi-ocs chart may remain for reference/experiments.

### 2. Workflow repository pin
- **Choice:** Prefer pin that already contains `eha-clinics-dev-gke`: `EHA-Clinics/eha-workflow@v15.0.5-clinics` (or newer). If org policy requires calling `eHealthAfrica/eha-workflow`, merge upstream cluster registration first and pin that tag.
- **Why:** This repo is `eHealthAfrica/*` (can call upstream eha-workflow once cluster exists); Clinics fork already has the cluster entry and action retargets. Either works if WIF trusts this repo.
- **WIF:** Extend clinics-dev pool condition / SA binding to allow `eHealthAfrica/open-chat-studio` (today’s bootstrap was `EHA-Clinics` owner-only).

### 3. Namespace and hostname
- **Choice:** Namespace `ocs-dev`, host `ocs-dev.eha.ng` (consistent with dimagi-ocs docs and Clinics `*-dev.eha.ng`).

### 4. Data plane
- **Choice:** Cloud SQL instance `eha-clinics-dev` + dedicated DB/user + pgvector; Cloud SQL Auth Proxy via generic3 `database.instance`. Redis: Bitnami chart in `ocs-dev` unless Memorystore exists.
- **Alternative:** In-cluster Postgres from dimagi-ocs chart — fallback only.

### 5. Migrate
- **Choice:** Kubernetes Job (pipeline `kubectl:` or pre-deploy) with same image tag running `python manage.py migrate --noinput`, gated before/with web success criteria.
- **Alternative:** Init container — weaker.

### 6. Branch mapping
- **Choice:** `deployments/dev.pipeline.yaml` with `git_branch: develop` (create `develop` if missing) + `workflow_dispatch` for `dev`.

## Risks / Trade-offs

- **[Risk] WIF denies eHealthAfrica owner** → Mitigation: update attribute_condition / principalSet before first deploy.
- **[Risk] Upstream eha-workflow lacks clinics cluster** → Mitigation: pin Clinics fork or merge `eHealthAfrica/eha-workflow` PR registering the cluster.
- **[Risk] generic3 command/args for Celery** → Mitigation: validate with `helm template` against 0.5.7; adjust values.
- **[Trade-off] dimagi-ocs custom chart unused as primary** → Ops docs there need a deprecation note when this path ships.

## Migration Plan

1. Land this OpenSpec PR; review; merge.
2. Apply: add pipeline, values, caller; fix WIF for this repo; Cloud SQL/Redis/DNS/secrets.
3. Push `develop` / dispatch `dev`; smoke test.
4. Point AdhereBot `OCS_BASE_URL` at `https://ocs-dev.eha.ng`.
5. Deprecate dimagi-ocs deploy workflow as default.

## Open Questions

- Exact eha-workflow pin (Clinics fork vs upstream after cluster merge) — resolve at apply without changing specs if both expose `eha-clinics-dev-gke`.
- Memorystore availability in `clinics-dev-359913`.

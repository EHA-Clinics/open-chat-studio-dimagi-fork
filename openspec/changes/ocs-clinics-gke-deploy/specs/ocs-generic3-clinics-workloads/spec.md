# Spec Delta

## Purpose

Defines Clinics GKE workload packaging for Open Chat Studio: **generic3** for app processes, **Bitnami Redis only** as an extra chart, **existing Cloud SQL `eha-clinics-dev`** for Postgres, and **Vault-backed** runtime credentials.

## ADDED Requirements

### Requirement: generic3 chart identity for app workloads
The system SHALL deploy application components (web, celery worker, celery beat) with Helm chart `eha-chart/generic3` version `0.5.7` (or a later platform-approved pin in `helm_charts.defaults.chart_version`) from `https://ehealthafrica.github.io/helm-charts/`.

#### Scenario: Deploy step uses generic3 for apps
- **WHEN** an application component Helm deploy runs
- **THEN** the chart identity is `eha-chart/generic3` at the pinned version from the eHA charts repository

### Requirement: Redis is the only datastore Helm chart
The system SHALL provide Redis for Celery/cache by deploying a **Bitnami Redis** (or equivalent) chart via the eha-workflow pipeline, and MUST NOT deploy an in-cluster PostgreSQL/pgvector Helm release for Clinics.

#### Scenario: Pipeline includes Redis chart not Postgres chart
- **WHEN** the `dev` pipeline’s chart components are listed
- **THEN** Redis is present as a chart-backed component and no Postgres/pgvector chart component is required for install

#### Scenario: Worker reaches broker
- **WHEN** celery worker pods become Ready with secrets configured
- **THEN** they can connect to the configured Redis URL

### Requirement: Existing Cloud SQL instance for Postgres
The system SHALL use the existing Cloud SQL instance `eha-clinics-dev` in GCP project `clinics-dev-359913` as the PostgreSQL server for OCS (dedicated database/role, separate from AdhereBot), including Cloud SQL Auth Proxy wiring on app components when using private IP connectivity.

#### Scenario: Values point at eha-clinics-dev
- **WHEN** generic3 database settings for web/worker/beat are rendered
- **THEN** they reference instance `clinics-dev-359913:europe-west1:eha-clinics-dev` (or the documented equivalent connection path to that instance)

#### Scenario: Credentials may be supplied after first deploy scaffolding
- **WHEN** Helm releases are installed before Vault/DB credentials are populated
- **THEN** the system still allows operators to add `DATABASE_URL` (and related keys) later via Vault/Secret update without changing the chart identity

### Requirement: Vault-backed runtime secrets
The system SHALL load runtime secrets (including database credentials, Django `SECRET_KEY`, cryptography keys, and other provider keys) through Kubernetes Secrets populated from **Vault** using generic3-supported Vault Static Secrets / env-from-Secret wiring (`vaultextrasecrets` / `env_secrets` or equivalent documented Clinics mechanism). Values files in git MUST NOT contain plaintext credentials.

#### Scenario: Values reference Vault or Secret names only
- **WHEN** generic3 values under `deployments/` are reviewed in git
- **THEN** they declare Vault paths and/or Secret names, not secret values

#### Scenario: Credential rotation without chart change
- **WHEN** an operator updates a credential in Vault for the configured path
- **THEN** the synced Kubernetes Secret can be updated and pods can pick up new values on rollout/restart without modifying Helm chart source in this repository

### Requirement: Process mapping to separate releases
The system SHALL map production processes to separate Helm releases for at least web (gunicorn), celery worker, and celery beat, all using the same image tag from a given successful pipeline run.

#### Scenario: Celery beat singleton
- **WHEN** celery beat is deployed
- **THEN** its replica count is exactly one

#### Scenario: Shared image tag across processes
- **WHEN** web and celery worker deploy from the same successful run
- **THEN** both releases use that run’s published image tag

### Requirement: Migrations gate
The system SHALL apply Django database migrations (`migrate --noinput` or equivalent) before treating the web rollout for that train as successful, once database credentials are available.

#### Scenario: Failed migrate fails the run
- **WHEN** the migration Job or hook exits non-zero
- **THEN** the workflow run fails and MUST NOT report a successful web deploy for that train

### Requirement: HTTPS Ingress for channels
The system SHALL expose web on a stable HTTPS hostname (default `ocs-dev.eha.ng`) via the clinics-dev Ingress controller suitable for Meta Cloud API webhooks.

#### Scenario: TLS hostname serves web
- **WHEN** DNS for the configured hostname points at cluster Ingress and certificates are issued
- **THEN** HTTPS requests to the OCS web service succeed

### Requirement: dimagi-ocs companion role
The system SHALL document `EHA-Clinics/dimagi-ocs` as a Clinics packaging/ops companion whose custom Helm chart is **not** the primary install chart for this Clinics path.

#### Scenario: Deploy guide names this repo’s workflow
- **WHEN** an operator reads Clinics deploy documentation produced by this change’s apply phase
- **THEN** the default instructions use this repo’s eha-workflow caller, generic3 app values, Bitnami Redis, and Cloud SQL `eha-clinics-dev` — not `dimagi-ocs` `deploy-ocs-helm.yml` as primary

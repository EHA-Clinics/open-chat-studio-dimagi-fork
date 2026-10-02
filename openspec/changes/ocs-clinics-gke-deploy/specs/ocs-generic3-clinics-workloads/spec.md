# Spec Delta

## Purpose

Defines Clinics GKE workload packaging for Open Chat Studio using published `eha-chart/generic3` 0.5.7 (and Redis), not the custom `EHA-Clinics/dimagi-ocs` umbrella chart as the primary install vehicle.

## ADDED Requirements

### Requirement: generic3 chart identity
The system SHALL deploy application components with Helm chart `eha-chart/generic3` version `0.5.7` (or a later platform-approved pin in `helm_charts.defaults.chart_version`) from `https://ehealthafrica.github.io/helm-charts/`.

#### Scenario: Deploy step uses generic3
- **WHEN** an application component Helm deploy runs
- **THEN** the chart identity is `eha-chart/generic3` at the pinned version from the eHA charts repository

### Requirement: Process mapping to separate releases
The system SHALL map production processes to separate Helm releases for at least web (gunicorn), celery worker, and celery beat, all using the same image tag from a given successful pipeline run.

#### Scenario: Celery beat singleton
- **WHEN** celery beat is deployed
- **THEN** its replica count is exactly one

#### Scenario: Shared image tag across processes
- **WHEN** web and celery worker deploy from the same successful run
- **THEN** both releases use that run’s published image tag

### Requirement: Migrations gate
The system SHALL apply Django database migrations (`migrate --noinput` or equivalent) before treating the web rollout for that train as successful.

#### Scenario: Failed migrate fails the run
- **WHEN** the migration Job or hook exits non-zero
- **THEN** the workflow run fails and MUST NOT report a successful web deploy for that train

### Requirement: Redis for Celery
The system SHALL provide a Redis broker/cache endpoint for worker and beat (`REDIS_URL` or equivalent), via in-cluster Bitnami Redis or managed Memorystore.

#### Scenario: Worker reaches broker
- **WHEN** celery worker pods become Ready
- **THEN** they can connect to the configured Redis URL

### Requirement: Postgres with pgvector
The system SHALL use a PostgreSQL database with pgvector/vector available, dedicated to OCS (separate from AdhereBot’s database), typically Cloud SQL `eha-clinics-dev`, and configure `DATABASE_URL` (or equivalent) for app components.

#### Scenario: Dedicated OCS database
- **WHEN** web starts with production settings on Clinics
- **THEN** it connects to an OCS-dedicated database/role, not the AdhereBot application database

### Requirement: HTTPS Ingress for channels
The system SHALL expose web on a stable HTTPS hostname (default `ocs-dev.eha.ng`) via the clinics-dev Ingress controller suitable for Meta Cloud API webhooks (including WhatsApp incoming paths served by OCS).

#### Scenario: TLS hostname serves web
- **WHEN** DNS for the configured hostname points at cluster Ingress and certificates are issued
- **THEN** HTTPS requests to the OCS web service succeed

### Requirement: Secrets not in git
The system SHALL load runtime secrets from Kubernetes Secrets (Vault Static Secrets / External Secrets or documented out-of-band apply). Values files in git MUST NOT contain plaintext credentials.

#### Scenario: Values omit secrets
- **WHEN** generic3 values under `deployments/` are reviewed in git
- **THEN** they reference Secret names and non-secret configuration only

### Requirement: dimagi-ocs companion role
The system SHALL document `EHA-Clinics/dimagi-ocs` as a Clinics packaging/ops companion whose custom Helm chart is **not** the primary install chart for this Clinics path; operators MUST follow this repository’s eha-workflow + generic3 deploy guide for default installs.

#### Scenario: Deploy guide names this repo’s workflow
- **WHEN** an operator reads Clinics deploy documentation produced by this change’s apply phase
- **THEN** the default instructions use this repo’s eha-workflow caller and generic3 values, not `dimagi-ocs` `deploy-ocs-helm.yml` as primary

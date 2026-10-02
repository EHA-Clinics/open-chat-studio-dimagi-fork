# Spec Delta

## Purpose

Defines how Open Chat Studio (this repository) invokes the shared eha-workflow reusable GitHub Actions to build and deploy onto Clinics GKE `eha-clinics-dev`.

## ADDED Requirements

### Requirement: Deploy originates from this repository
The system SHALL build the production OCS container image from this repository’s Docker context (root `Dockerfile`) as part of the Clinics deploy pipeline so the deployed image tag corresponds to a commit in `eHealthAfrica/open-chat-studio`.

#### Scenario: Pipeline builds local Dockerfile
- **WHEN** the `dev` pipeline’s build component runs
- **THEN** it builds using this repo’s `Dockerfile` (or a documented path in-repo) and pushes to the Clinics registry

### Requirement: eha-workflow caller
The system SHALL provide a GitHub Actions workflow that calls an eha-workflow `build-deploy.yaml` reusable workflow at a pinned tag, with `secrets: inherit`.

#### Scenario: develop push triggers deploy
- **WHEN** commits are pushed to the branch mapped by `deployments/dev.pipeline.yaml` (`git_branch`)
- **THEN** the reusable build-deploy workflow runs

#### Scenario: Manual environment dispatch
- **WHEN** an operator runs `workflow_dispatch` with environment `dev`
- **THEN** the resolver selects the `dev` pipeline and deploys that environment

### Requirement: Clinics cluster and registry
The system SHALL set `deployment.cluster` to `eha-clinics-dev-gke` and `image_registry` to `clinics-dev-359913` for the `dev` environment, deploying into Kubernetes namespace `ocs-dev`.

#### Scenario: Resolve targets clinics-dev
- **WHEN** resolve runs for `dev`
- **THEN** the resolved target includes GKE cluster `eha-clinics-dev` in GCP project `clinics-dev-359913`

### Requirement: Short-lived GCP authentication
The system SHALL authenticate to GCP using Workload Identity Federation via Environment secrets named `GCP_WORKLOAD_IDENTITY_PROVIDER` and `GCP_SERVICE_ACCOUNT` as required by eha-workflow, and MUST NOT require a long-lived GCP service-account JSON key for routine Clinics deploys.

#### Scenario: Federated auth without SA JSON
- **WHEN** Environment `dev` is configured with valid WIF secrets for this repository
- **THEN** build/push and Helm deploy can obtain GCP credentials without a JSON key secret

### Requirement: Workflow pin documents Clinics compatibility
The system SHALL pin a workflow ref that includes the `eha-clinics-dev-gke` cluster registry entry (for example `EHA-Clinics/eha-workflow@v15.0.5-clinics`, or `eHealthAfrica/eha-workflow` at a tag/commit that contains that cluster file).

#### Scenario: Unknown cluster does not occur for clinics-dev
- **WHEN** resolve runs against the pinned workflow ref
- **THEN** cluster `eha-clinics-dev-gke` is a registered cluster name

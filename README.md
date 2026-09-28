# AI Security Red Team Assessment — RedMnist

# 1. Project Overview

This repository contains an individual AI security red-team assessment of a local PyTorch image-classification system.

The system was reviewed from several angles:

    Model artifact
         |
         v
    PyTorch inference
         |
         v
    FastAPI service
         |
         +---- Frontend
         |
         v
    Docker container
         |
         v
    Logs / evidence

The assessment focused on two classes of security testing required by the challenge:

    AI/ML adversarial behavior — successful adversarial attacks against the image classifier.

    System and deployment security — API, metadata, input-handling, logging, and Docker weaknesses followed by hardening and retesting.

All testing was performed against the participant's own local model and containers.

# 2. Assessment Objectives

    Verify the supplied PyTorch model and serving pipeline.
    Perform reconnaissance of the local inference service.
    Identify model, API, and container weaknesses.
    Demonstrate at least two successful adversarial attacks.
    Preserve reproducible adversarial artifacts.
    Implement practical mitigations.
    Retest the mitigations.
    Map findings to MITRE ATLAS and NIST AI RMF.
    Document AI-assisted work honestly and reproducibly.

# 3. Key Results

## Baseline model

The model was evaluated over the 10,000-image MNIST test set:

    Correct: 9907
    Incorrect: 93
    Accuracy: 99.07%

## Successful attacks

    FGSM: epsilon 0.5, original 7 / 1.0000, adversarial 2 / 0.5933, successful misclassification.
    PGD: epsilon 0.2, alpha 0.01, 40 steps, original 7 / 1.0000, adversarial 3 / 0.9973, successful misclassification.

## Mitigation retest

The hardened adversarial-training checkpoint produced the following targeted retest results on the same sample:

    Original -> 7 / 0.9929
    FGSM     -> 7 / 0.2489
    PGD      -> 7 / 0.7599

This demonstrates resistance to the tested configurations on this sample. It does not prove universal adversarial robustness.

# 4. Baseline Security Findings

The main baseline weaknesses were:

    /model_info exposed internal model metadata.
    /docs, /redoc and /openapi.json were exposed.
    CORS allowed wildcard origin access.
    No explicit application-level file-size limit.
    No explicit image-dimension limit.
    No explicit batch-count / aggregate-size limit.
    Verbose image parsing errors could be returned to callers.
    Docker container ran as root.
    Docker capabilities and privilege restrictions were not hardened.
    Model artifact integrity was not independently hash-verified.
    No application authentication or rate limiting was implemented.
    No explicit OOD/unknown class rejection was implemented.

# 5. Hardening Implemented

## API

    Removed /model_info.
    Disabled FastAPI documentation endpoints.
    Restricted CORS to selected local frontend origins.
    Added per-file upload limit: 5 MB.
    Added maximum batch count: 10.
    Added maximum batch size: 20 MB.
    Added maximum image dimensions: 1024 x 1024.
    Reduced external validation errors to generic messages.
    Reduced unnecessary uploaded-file metadata in logs.

## Docker

    Application runs as UID 10001 (appuser).
    no-new-privileges:true.
    cap_drop: ALL.
    Read-only root filesystem.
    /tmp mounted as tmpfs.
    Service remains reachable and functional after hardening.

## Model

    PGD-based adversarial training added.
    Hardened checkpoint: model/redmnist_robust_v2.pth.
    Original attack sample reused for a mitigation regression test.

# 6. Reproducibility

## 6.1 Create Python environment

On Windows Git Bash:

    python -m venv .venv
    source .venv/Scripts/activate
    pip install -r requirements.txt

## 6.2 Verify the model

    python tests/load_check.py
    python tests/evaluate_model.py

## 6.3 Run the API locally

    PYTHONPATH=. uvicorn api.app:app --host 0.0.0.0 --port 8000

Health check:

    curl http://127.0.0.1:8000/health

## 6.4 Run the frontend

From the repository root, in a separate terminal:

    python -m http.server 5173 -d frontend

The frontend is intended for the local API configuration.

## 6.5 Run the adversarial attacks

From the repository root:

    python run_fgsm.py
    python run_pgd.py

Artifacts are written to:

    results/original/
    results/fgsm/
    results/pgd/

## 6.6 Retest mitigation

Because the repository imports local packages from the project root:

    PYTHONPATH=. python tests/test_mitigation.py

## 6.7 Run with Docker Compose

    docker compose build --no-cache
    docker compose up -d

Check the container:

    docker ps
    curl http://127.0.0.1:8000/health

Security verification:

    docker exec redmnist-api whoami
    docker exec redmnist-api id
    docker inspect redmnist-api --format '{{json .HostConfig.SecurityOpt}}'
    docker inspect redmnist-api --format '{{json .HostConfig.CapDrop}}'
    docker inspect redmnist-api --format '{{.HostConfig.ReadonlyRootfs}}'
    docker inspect redmnist-api --format '{{.HostConfig.Privileged}}'

# 7. Evidence Structure

    report/
    ├── Adversarial_Examples.md
    ├── AI_USAGE_LOG.md
    ├── MITRE_ATLAS_Mapping.md
    ├── NIST_AI_RMF_Mapping.md
    ├── Pipeline_Review.md
    ├── evidence/
    └── img/

    attacks/
    ├── attacks.py
    └── ...

    api/
    ├── app.py
    ├── logging_config.py
    ├── model_loader.py
    └── preprocessing.py

    defenses/
    └── adversarial_training.py

    model/
    ├── redmnist.py
    ├── redmnist.pth
    └── redmnist_robust_v2.pth

    results/
    ├── original/
    ├── fgsm/
    └── pgd/

    tests/
    ├── load_check.py
    ├── evaluate_model.py
    └── test_mitigation.py

    Dockerfile
    docker-compose.yml
    requirements.txt
    run_fgsm.py
    run_pgd.py
    README.md

# 8. Documentation Guide

## main report

Use the detailed general report prepared for the assessment as the overall narrative report. The focused Markdown documents below provide the repository-ready evidence and framework mappings.

## Focused reports

    Adversarial attack evidence: report/Adversarial_Examples.md
    System/API/Docker review: report/Pipeline_Review.md
    MITRE ATLAS mapping: report/MITRE_ATLAS_Mapping.md
    NIST AI RMF mapping: report/NIST_AI_RMF_Mapping.md
    AI assistance record: report/AI_USAGE_LOG.md

# 9. Security Evidence Highlights

## Endpoint hardening

    GET /model_info     -> 404
    GET /docs           -> 404
    GET /redoc          -> 404
    GET /openapi.json   -> 404

## CORS hardening

    Origin: http://evil.example
    -> no Access-Control-Allow-Origin header

    Origin: http://localhost:5173
    -> Access-Control-Allow-Origin: http://localhost:5173

## Resource-control hardening

    > 5 MB file           -> HTTP 413
    2000 x 2000 image     -> HTTP 400
    11-file batch         -> HTTP 413
    ~23 MB total batch    -> HTTP 413

## Docker hardening

    User            -> appuser / UID 10001
    no-new-privileges -> enabled
    Capabilities    -> ALL dropped
    Privileged      -> false
    Root filesystem -> read-only
    /tmp            -> writable tmpfs

# 10. Residual Risks

The assessment intentionally documents the controls that remain outside the current implementation:

    No authentication.
    No rate limiting.
    No complete network-level DoS protection.
    Image-dimension validation occurs after image decoding.
    No cryptographic model artifact verification.
    No universal adversarial robustness guarantee.
    No dedicated OOD rejection mechanism.
    No production log rotation / centralized logging design.

These are documented as residual risks and recommendations rather than being presented as solved.

# 11. Assessment Limitations

The project uses a local MNIST-style classifier and local infrastructure. Results should be interpreted within that scope.

# 13. References

    MITRE ATLAS data repository: https://github.com/mitre-atlas/atlas-data
    MITRE ATLAS technique references are listed in report/MITRE_ATLAS_Mapping.md.
    NIST AI RMF references are listed in report/NIST_AI_RMF_Mapping.md.
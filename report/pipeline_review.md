# AI Security Pipeline Review

# 1. Scope

This pipeline review assesses the local RedMnist deployment from model artifact loading through API exposure and Docker runtime configuration.

The review covers:

    Model checkpoint
        -> model loader
        -> preprocessing
        -> FastAPI inference endpoints
        -> frontend
        -> Docker image/container
        -> logging

Testing was performed only against the participant's own local environment.

# 2. Architecture Reviewed

## Model

    model/redmnist.py
    model/redmnist.pth
    PyTorch 2.14.0+cpu
    10 output classes
    Input tensor shape [1, 1, 32, 32]
    61,706 total parameters

## API

    FastAPI / Uvicorn
    /health
    /predict
    /predict_batch
    /model_info existed in the baseline and was removed during hardening
    FastAPI documentation routes existed in the baseline and were disabled during hardening

## Container

The original container ran as root with no dropped capabilities, no no-new-privileges, and a writable root filesystem. The hardened container now uses a non-root application user, drops all Linux capabilities, enables no-new-privileges, and uses a read-only root filesystem with /tmp mounted as tmpfs.

# 3. Finding A — Excessive Model Metadata Exposure

## Finding

Baseline state: GET /model_info returned internal model metadata.

Observed metadata included:

    architecture name: RedMnistNet
    framework/version: pytorch 2.14.0+cpu
    input shape: [1,1,32,32]
    output class count: 10
    execution device
    parameter counts

## How it was tested

    curl http://127.0.0.1:8000/model_info

## Impact

The endpoint reduced the amount of reconnaissance required to understand the model and its input/output structure. The information did not by itself provide a direct code-execution path, but it increased model exposure and made attack staging easier.

## Remediation

/model_info was removed from the hardened API.

## Retest

    GET /model_info -> 404 Not Found

# 4. Finding B — Interactive API Documentation Exposure

## Finding

Baseline state: FastAPI's /docs, /redoc, and /openapi.json routes were publicly reachable on the local service.

## How it was tested

    curl -I http://127.0.0.1:8000/docs
    curl -I http://127.0.0.1:8000/redoc
    curl -I http://127.0.0.1:8000/openapi.json

## Impact

The documentation exposed the available API surface and request schemas to anyone with access to the service. In a production deployment, public documentation can simplify reconnaissance and endpoint discovery.

## Remediation

FastAPI was configured with:

    docs_url=None
    redoc_url=None
    openapi_url=None

## Retest

    GET /docs       -> 404
    GET /redoc      -> 404
    GET /openapi.json -> 404

# 5. Finding C — Wildcard CORS

## Finding

Baseline state: the API returned:

    Access-Control-Allow-Origin: *

for an arbitrary test origin such as:

    http://evil.example

## Impact

Wildcard CORS permits browser-based requests from arbitrary origins. CORS is not authentication, so this did not constitute an authentication bypass by itself. It did, however, unnecessarily broaden cross-origin browser access.

## Remediation

The hardened API now allows only the explicitly selected local frontend origins:

    http://localhost
    http://localhost:80
    http://localhost:3000
    http://localhost:5173
    http://127.0.0.1
    http://127.0.0.1:80
    http://127.0.0.1:3000
    http://127.0.0.1:5173

Methods and headers were also narrowed to the required set.

## Retest

Malicious test origin:

    Origin: http://evil.example
    Result: no Access-Control-Allow-Origin header

Allowed local origin:

    Origin: http://localhost:5173
    Result: Access-Control-Allow-Origin: http://localhost:5173

# 6. Finding D — Missing File and Batch Size Controls

## Finding

Baseline state: the application did not enforce explicit application-level file-size, dimension, or batch-count limits.

## Evidence

A valid 2000 x 2000 image was accepted and resized by the baseline preprocessing code.

A 20-file batch request was also accepted and processed.

## Impact

Large files and large batches increase resource consumption and can contribute to denial-of-service conditions. This assessment did not establish a production-grade network-level DoS condition, so the finding is limited to missing application-level resource controls.

## Remediation

The hardened application added:

    MAX_FILE_SIZE = 5 MB
    MAX_BATCH_FILES = 10
    MAX_BATCH_TOTAL_SIZE = 20 MB
    MAX_IMAGE_WIDTH = 1024
    MAX_IMAGE_HEIGHT = 1024

The application rejects oversized uploads with HTTP 413 and rejects over-dimension images at validation time after image decoding.

## Retest 1 — Individual file

A test file above 5 MB produced:

    HTTP 413
    Uploaded file exceeds the allowed size

## Retest 2 — Image dimensions

A 2000 x 2000 PNG produced:

    HTTP 400
    Invalid image upload

## Retest 3 — Batch count

An 11-file batch produced:

    HTTP 413
    Batch contains too many files

## Retest 4 — Total batch size

Five files of approximately 4.6 MB each (approximately 23 MB total) produced:

    HTTP 413
    Total batch size exceeds the allowed limit

# 7. Finding E — Verbose Image Parsing Errors

## Finding

Baseline state: malformed/truncated image input could cause detailed decoder errors such as:

    Invalid image: image file is truncated

## Impact

Detailed parser messages can reveal implementation details and produce inconsistent external error behavior.

## Remediation

The hardened application returns generic external errors such as:

    Invalid image upload
    Unable to process image

Detailed technical information remains in server-side structured logs where appropriate.

# 8. Finding F — Root Container Execution

## Baseline evidence

The original image/container ran as:

    uid=0(root)
    gid=0(root)

No Linux capabilities were dropped, no-new-privileges was not configured, and the root filesystem was writable.

## Impact

A container compromise would initially provide root privileges inside the container and more write/capability surface than required by the inference service.

## Remediation

The hardened Docker deployment now:

    Creates user appuser with UID 10001.
    Runs the service as appuser.
    Drops all capabilities.
    Enables no-new-privileges:true.
    Uses a read-only root filesystem.
    Provides writable temporary storage through tmpfs at /tmp.

## Retest

    whoami
    -> appuser

    id
    -> uid=10001(appuser) gid=10001(appuser) groups=10001(appuser)

    SecurityOpt
    -> no-new-privileges:true

    CapDrop
    -> ALL

    Privileged
    -> false

    ReadonlyRootfs
    -> true

Attempting to write under /app produced:

    Read-only file system

Writing to /tmp succeeded because /tmp is explicitly mounted as temporary writable storage.

# 9. Finding G — Model Artifact Integrity and Loading Hardening

## Current state

The loader uses a fixed local checkpoint path, maps the checkpoint to the selected runtime device, loads the state dictionary, puts the model into evaluation mode, and moves it to the selected device.

The checkpoint was verified against the local architecture with no missing or unexpected state-dictionary keys.

## Remaining improvement

The current project does not include an independent cryptographic integrity check for the checkpoint. A stronger production pipeline should:

    Store a trusted SHA-256 hash for the expected model artifact.
    Verify the hash before loading.
    Validate the expected state-dictionary schema and tensor shapes.
    Prefer restricted/weights-only loading options where supported by the installed PyTorch version.
    Keep model artifacts immutable and access-controlled.
    Record the exact model hash/version used by each deployment.

No malicious-checkpoint execution test was performed during this assessment, so this is recorded as a hardening recommendation rather than a demonstrated exploit.

# 10. Finding H — No Authentication or Rate Limiting

## Current state

The assessment API is intentionally local and does not implement an application authentication layer or request-rate limiting.

## Risk

If the service were exposed beyond the local evaluation environment, an unauthenticated inference endpoint could allow unrestricted use of the model and facilitate repeated probing, denial-of-service attempts, or larger-scale adversarial query collection.

## Recommendation

For production use:

    Place the API behind an authenticated gateway.
    Apply per-client rate limits and quotas.
    Enforce concurrency/request timeouts.
    Use reverse-proxy or ingress-level body-size limits.
    Monitor repeated failed/abnormal requests.
    Consider output minimization if model information exposure is a concern.

This assessment did not implement these features because the challenge requires a local demonstration environment and the current task focused on the documented weaknesses and hardening steps.

# 11. Finding I — Input Distribution / OOD Behavior

A blank or meaningless image can still be assigned to one of the ten known MNIST classes because the classifier has no explicit unknown/out-of-distribution class.

Observed examples included:

    Blank/meaningless input -> class 5, confidence approximately 0.4131
    Grey image -> class 4, confidence approximately 0.1937

This is a model robustness observation rather than a demonstrated API exploit. Production systems requiring rejection of unfamiliar inputs should evaluate explicit OOD detection or confidence/calibration controls.

# 12. Frontend / Pipeline Consistency

Because /model_info was removed during hardening, frontend code that still called the endpoint would have become stale.

The frontend was updated to remove the /model_info feature and its JavaScript call path. A repository search produced no remaining model_info references in the updated frontend/index.html.

# 13. Logging Review

The service uses JSON-lines structured logging in logs/predictions.log.

The hardened logging behavior was reduced to operationally useful fields such as:

    timestamp
    severity
    event
    request size
    predicted class
    confidence
    latency
    safe validation error category

The hardened request logs no longer include uploaded filenames or content types from the prediction endpoint.

## Remaining logging hardening

Production logging should add:

    Log rotation and retention.
    File permissions/ownership controls.
    Centralized protected log storage where appropriate.
    Alerting on repeated validation failures and request spikes.
    Clear handling of sensitive data if real-world images are ever introduced.

# 14. Overall Pipeline State

## Before hardening

    Model metadata endpoint       Exposed
    API documentation             Exposed
    CORS                          Wildcard
    Upload limits                 Not explicit
    Dimension limits              Not explicit
    Verbose parser errors         Exposed
    Container user                root
    Linux capabilities            Not restricted
    Root filesystem               Writable
    Model artifact hash check     Not implemented
    Authentication                Not implemented
    Rate limiting                 Not implemented

## After hardening

    Model metadata endpoint       Removed
    API documentation             Disabled
    CORS                          Restricted to local origins
    Upload size                   5 MB per file
    Batch count                   10 files
    Batch total size              20 MB
    Image dimensions              1024 x 1024 maximum
    External parser errors        Genericized
    Container user                appuser / UID 10001
    Linux capabilities            ALL dropped
    no-new-privileges             Enabled
    Root filesystem               Read-only
    /tmp                          tmpfs
    Model artifact hash check     Recommended residual control
    Authentication                Residual requirement for production
    Rate limiting                 Residual requirement for production

# 15. Recommended Production Hardening Sequence

    Keep the current non-root/read-only/capability-restricted container baseline.
    Add model checksum/signature verification and artifact provenance.
    Add authentication and request rate limiting at the service/gateway layer.
    Enforce network/reverse-proxy upload limits in addition to application checks.
    Add monitoring for repeated adversarial-looking or malformed requests.
    Evaluate OOD rejection and confidence calibration.
    Expand adversarial testing across a larger sample set instead of relying on one digit image.
    Periodically re-run the security regression suite after code/model changes.

# 16. Evidence References

Key implementation files:

    api/app.py
    api/preprocessing.py
    api/model_loader.py
    api/logging_config.py
    Dockerfile
    docker-compose.yml
    frontend/index.html

Focused evidence reports:

    report/Adversarial_Examples.md
    report/MITRE_ATLAS_Mapping.md
    report/NIST_AI_RMF_Mapping.md
    report/AI_USAGE_LOG.md
# NIST AI Risk Management Framework Mapping

# 1. Purpose

This document maps the RedMnist red-team assessment activities to the four functions of the NIST AI Risk Management Framework (AI RMF): GOVERN, MAP, MEASURE, and MANAGE.

The NIST AI RMF 1.0 Core organizes AI risk-management activities around these four functions. NIST describes GOVERN as a cross-cutting function and positions MAP, MEASURE, and MANAGE as complementary lifecycle activities.

# 2. Mapping Summary

    AI RMF Function: GOVERN
    Assessment Activity: Defined scope, local-only rules, documentation, AI usage tracking, ownership of the assessment repository
    Evidence in This Project: Task scope, Git repository history, report/AI_USAGE_LOG.md, report set

    AI RMF Function: MAP
    Assessment Activity: Identified the model, preprocessing, API, Docker, metadata, input-validation and adversarial risks
    Evidence in This Project: report/Pipeline_Review.md, architecture/recon tests

    AI RMF Function: MEASURE
    Assessment Activity: Quantified baseline accuracy, successful adversarial attacks, API-control retests, and Docker security controls
    Evidence in This Project: tests/evaluate_model.py, attack results, API/Docker retests

    AI RMF Function: MANAGE
    Assessment Activity: Implemented remediation, trained an adversarially hardened checkpoint, and retested the same attack configuration
    Evidence in This Project: defenses/adversarial_training.py, model/redmnist_robust_v2.pth, tests/test_mitigation.py

# 3. GOVERN

## Assessment relevance

Governance is represented in the project through explicit rules, responsibility, documentation, and a traceable work history.

## Evidence

The assessment was constrained to the participant's own local model and containers. Work was maintained in a Git repository and documented through focused security reports and an AI usage log.

Relevant artifacts:

    report/AI_USAGE_LOG.md
    README.md
    report/Pipeline_Review.md
    report/Adversarial_Examples.md

## Practical governance controls demonstrated

    Assessment scope was defined before testing.
    No external systems were targeted.
    Attack evidence and remediation were recorded.
    Model and container changes were preserved in the repository.
    AI assistance was tracked instead of being left undocumented.

## Remaining governance improvement

For a production AI system, governance should also formally define:

    Model owners and approvers.
    Security-review gates for model releases.
    Artifact provenance and change control.
    Incident-response responsibilities.
    Retention of evaluation evidence.
    Periodic re-assessment requirements.

# 4. MAP

## Assessment relevance

The MAP function is represented by establishing the system context and identifying where AI-specific and system-level risks exist.

## Risks mapped during this assessment

    Model evasion: adversarial inputs caused incorrect predictions.
    API reconnaissance: model metadata and API documentation exposed information.
    Input/resource abuse: missing file, dimension, and batch limits were observed in the baseline.
    Cross-origin access: wildcard CORS widened browser-based request origins.
    Error information exposure: image-decoder details were exposed to callers.
    Container privilege: the baseline container executed as root.
    Artifact integrity: model loading lacked an independent checkpoint hash verification control.
    OOD behavior: inputs outside the expected handwritten-digit distribution could still receive one of the ten known labels.

## Evidence

report/Pipeline_Review.md provides the detailed map from each observed weakness to its test, impact, and mitigation.

# 5. MEASURE

## Baseline model measurement

The MNIST test-set evaluation covered all 10,000 test images:

    Correct: 9907
    Incorrect: 93
    Accuracy: 99.07%

## Adversarial measurement

The same sample was evaluated before and after attack generation:

    Original: prediction 7, confidence 1.0000, correct.
    FGSM: prediction 2, confidence 0.5933, misclassified.
    PGD: prediction 3, confidence 0.9973, misclassified.

## API security measurements

The assessment measured, among other controls:

    /model_info             -> exposed in baseline, 404 after hardening
    /docs                   -> exposed in baseline, 404 after hardening
    /openapi.json           -> exposed in baseline, 404 after hardening
    Wildcard CORS           -> present in baseline, restricted after hardening
    6 MB file               -> accepted only after baseline, 413 after hardening
    2000 x 2000 image       -> accepted/resized in baseline, 400 after hardening
    11-file batch           -> allowed in baseline, 413 after hardening
    ~23 MB total batch      -> not explicitly limited in baseline, 413 after hardening

## Docker measurements

The hardened container was measured for:

    User            -> appuser / UID 10001
    No new privs    -> true
    Capabilities    -> ALL dropped
    Privileged      -> false
    Root filesystem -> read-only
    /tmp            -> writable tmpfs

# 6. MANAGE

## Assessment relevance

The MANAGE function is represented by treating measured risks with concrete remediation and follow-up tests.

## Remediation actions

### Model-level

A PGD-based adversarial-training workflow was added:

    Epochs:       5
    Batch size:   64
    PGD epsilon:  0.2
    Alpha:        0.005
    PGD steps:    60

Output checkpoint:

    model/redmnist_robust_v2.pth

### API-level

    Removed /model_info.
    Disabled /docs, /redoc, /openapi.json.
    Restricted CORS.
    Added file-size limit.
    Added batch-count limit.
    Added aggregate batch-size limit.
    Added image-dimension limits.
    Reduced verbose external parser errors.

### Container-level

    Non-root user.
    Dropped all capabilities.
    No-new-privileges.
    Read-only root filesystem.
    Writable /tmp via tmpfs.

## Retest of adversarial mitigation

The hardened checkpoint was tested against the same sample and attack functions:

    Original -> 7 / 0.9929
    FGSM     -> 7 / 0.2489
    PGD      -> 7 / 0.7599

This provides evidence that the tested configurations no longer changed the prediction on the selected sample.

## Limitation

The retest is a targeted regression test, not a statistically complete robustness evaluation. A production program should evaluate many samples, attack strengths, attack families, and transformation conditions.

# 7. Trustworthiness Characteristics Observed

The project particularly exercised the AI RMF trustworthiness areas most directly relevant to this assessment:

## Valid and reliable

Baseline model accuracy was measured and recorded at 99.07% on the MNIST test set.

## Secure and resilient

Adversarial attacks, API abuse cases, and Docker runtime configuration were explicitly tested.

## Accountable and transparent

Evidence, code, reports, and an AI usage log are maintained in the repository.

## Privacy enhanced

No real personal data was used as part of the assessment. The final logging configuration also removes unnecessary uploaded filename/content-type information from prediction-event records.

# 8. Residual Risks After Management

The following remain intentionally documented rather than hidden:

    No application authentication.
    No rate limiting.
    Application-level limits are not a complete network-level DoS control.
    Image dimensions are checked after decoding, so decompression/resource cost is not fully eliminated.
    Checkpoint hash/signature verification is recommended but not implemented.
    Adversarial testing covered specific attack configurations and one documented sample for the successful attack demonstrations.
    OOD handling is not implemented as a separate reject/unknown class.
    Production-grade logging rotation/centralization is not implemented.

# 9. NIST References

    NIST AI RMF Playbook: https://www.nist.gov/itl/ai-risk-management-framework/nist-ai-rmf-playbook
    NIST AI RMF 1.0 Core: https://airc.nist.gov/airmf-resources/airmf/5-sec-core/
    Govern Playbook: https://airc.nist.gov/airmf-resources/playbook/govern/
    Map Playbook: https://airc.nist.gov/airmf-resources/playbook/map/
    Measure Playbook: https://airc.nist.gov/airmf-resources/playbook/measure/
    Manage Playbook: https://airc.nist.gov/airmf-resources/playbook/manage/
    NIST AI RMF 1.0 PDF: https://nvlpubs.nist.gov/nistpubs/ai/NIST.AI.100-1.pdf

NIST notes that the AI RMF Playbook is voluntary guidance and is updated as the framework evolves.
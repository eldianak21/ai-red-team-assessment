# Adversarial Examples

# 1. Purpose

This document records the two successful adversarial machine-learning attacks completed against the local RedMnist image-classification model for the AI Security Red Team Assessment.

The attacks were performed only against the assessment participant's own local model and artifacts. No external system, third-party model, or real personal data was targeted.

# 2. Target Model

    Model: RedMnistNet
    Framework: PyTorch
    Checkpoint: model/redmnist.pth
    Input: single-channel image tensor, resized to 32 x 32
    Output: 10 digit classes (0 through 9)
    Baseline test-set accuracy: 99.07% on the 10,000-image MNIST test set

Attack sample: sample_digits/digit_7.png

True label: 7

The model architecture contains convolutional layers followed by fully connected layers and a final LogSoftmax output. The checkpoint was verified as compatible with the RedMnistNet definition with no missing or unexpected state-dictionary keys.

# 3. Attack 1 — FGSM

## 3.1 Technique

Fast Gradient Sign Method (FGSM) computes the gradient of the loss with respect to the input image and moves the image in the direction that increases the model loss.

Implementation location:

    attacks/attacks.py

The implementation uses:

    epsilon = 0.5

The adversarial image is clipped to the valid pixel range [0, 1].

## 3.2 Execution

Run from the repository root:

    python run_fgsm.py

Observed execution pattern from the successful integrated run:

    Loading model...
    Loading image: sample_digits/digit_7.png

    [Original]  predicted=7  confidence=1.0000
    [FGSM]      predicted=2  confidence=0.5933  (epsilon=0.5)

    Saved:
      results/original/digit_7.png
      results/fgsm/digit_7_fgsm.png

    Attack succeeded: true label was 7, model now says 2.

## 3.3 Result

    Property: True label
    Original: 7
    FGSM: 7

    Property: Predicted class
    Original: 7
    FGSM: 2

    Property: Confidence
    Original: 1.0000
    FGSM: 0.5933

    Property: Epsilon
    Original: —
    FGSM: 0.5

    Property: Outcome
    Original: Correct
    FGSM: Misclassified

## 3.4 Security meaning

The same underlying image that the baseline model classified as digit 7 was modified using a gradient-based adversarial perturbation and became a prediction of digit 2.

This demonstrates a concrete evasion condition: the model can be induced to produce an incorrect classification using a deliberately constructed input.

The experiment is a white-box attack because the attacker had access to the model and gradients offline.

# 4. Attack 2 — PGD

## 4.1 Technique

Projected Gradient Descent (PGD) performs repeated gradient-based updates and projects the resulting image back into the allowed perturbation region around the original input.

Implementation location:

    attacks/attacks.py

Configuration used for the successful integrated run:

    epsilon = 0.2
    alpha = 0.01
    iterations = 40

## 4.2 Execution

Run from the repository root:

    python run_pgd.py

Observed execution pattern from the successful integrated run:

    Loading model...
    Loading image: sample_digits/digit_7.png

    [Original]  predicted=7  confidence=1.0000
    [PGD]       predicted=3  confidence=0.9999  (epsilon=0.2, alpha=0.01, iters=40)

    Saved:
      results/original/digit_7.png
      results/pgd/digit_7_pgd.png

    Attack succeeded: true label was 7, model now says 3.

## 4.3 Result

    Property: True label
    Original: 7
    PGD: 7

    Property: Predicted class
    Original: 7
    PGD: 3

    Property: Confidence
    Original: 1.0000
    PGD: 0.9999

    Property: Epsilon
    Original: —
    PGD: 0.2

    Property: Step size
    Original: —
    PGD: 0.01

    Property: Iterations
    Original: —
    PGD: 40

    Property: Outcome
    Original: Correct
    PGD: Misclassified

## 4.4 Security meaning

PGD produced a different misclassification from the original class while maintaining the tested perturbation bound. The high confidence in class 3 shows that the failure was not merely a near-tie between output classes in this test case.

The attack is also white-box and was generated offline using the local model.

Because the PGD implementation uses a randomized starting perturbation, repeated runs may produce different incorrect classes. The security condition evaluated here is whether the final prediction differs from the true class.

# 5. Evidence Artifacts

The following artifacts are part of the reproducible evidence set:

    sample_digits/digit_7.png
    results/original/digit_7.png
    results/fgsm/digit_7_fgsm.png
    results/pgd/digit_7_pgd.png
    attacks/attacks.py
    run_fgsm.py
    run_pgd.py

Recommended screenshots for the final presentation/video:

    Original prediction: 7 with confidence 1.0000.
    FGSM prediction: 2 with confidence 0.5933.
    PGD prediction: 3 with confidence 0.9999.
    Side-by-side original/FGSM/PGD images.
    Terminal output showing the attack configuration and successful label changes.

# 6. Attack Interpretation and Limitations

These results prove successful attacks for the specific tested sample and configurations. They do not prove that every MNIST image is vulnerable, nor that every FGSM or PGD configuration succeeds.

# 7. Mitigation Retest Reference

A hardened checkpoint was trained with PGD-based adversarial training and retested using the same sample:

    Output checkpoint: model/redmnist_robust_v2.pth
    Training configuration: 5 epochs, batch size 64, PGD epsilon 0.2, alpha 0.005, 60 PGD steps

Final targeted retest on the sample:

    Original: predicted 7, confidence 0.9929
    FGSM: predicted 7, confidence 0.2489
    PGD: predicted 7, confidence 0.7599

This shows resistance to the specific tested attack configurations on this sample. It is not evidence of universal adversarial robustness.

# 8. Related Reports

    report/pipeline_review.md
    report/MITRE_ATLAS_Mapping.md
    report/NIST_AI_RMF_Mapping.md
    report/AI_USAGE_LOG.md
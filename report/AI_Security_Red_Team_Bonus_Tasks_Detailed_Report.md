# AI SECURITY RED TEAM ASSESSMENT — BONUS TASKS

Bonus Tasks — Detailed Implementation, Evidence, and Presentation Guide

Project: RedMnist — local PyTorch MNIST classifier + FastAPI + Docker

# Contents

    What the three bonus areas mean
    Bonus #1 — Security instrumentation / structured logging
    Bonus #2 — Controlled data poisoning / backdoor
    Bonus #3 — Membership inference
    Bonus Results at a Glance
    Final Bonus Checklist

# 1. What the Three Bonus Areas Mean

The challenge brief identifies three types of bonus work: model extraction or membership inference, controlled data poisoning or a backdoor vector, and MITRE ATLAS tooling or LLMOps-style instrumentation.

    Instrumentation / logging: Connected structured JSON security-event logging to the actual FGSM and PGD execution scripts. Evidence: security/instrumentation.py; run_fgsm.py; run_pgd.py; logs/security_events.jsonl

    Data poisoning / backdoor: Created a separate experimental model. Poisoned selected digit-7 training samples by adding a trigger and assigning target label 3. Evidence: experiments/backdoor/backdoor_demo.py; redmnist_backdoor_demo.pth; clean/triggered images

    Membership inference: Compared confidence and loss for 500 known training members vs 500 held-out test non-members using the experimental model. Evidence: experiments/membership_inference/membership_inference.py; results.txt

# 2. Bonus #1 — Security Instrumentation / Structured Logging

The goal of instrumentation is simple: when a security-relevant event happens, the system should create a structured record that can be searched later. A terminal printout tells a human what happened at that moment. A structured log gives a machine-readable record that can later support monitoring, investigation, trend analysis, or alerting.

The challenge material describes bonus instrumentation/logging using structured fields and says the logs should not contain raw image content. The implemented design follows that direction.

The event record used these fields:

    timestamp — When the security event occurred.
    event — What kind of event occurred; here it is adversarial_attack.
    attack — Which attack generated the event: FGSM or PGD.
    true_label — The known correct digit for the test sample.
    original_prediction — What the clean image was classified as.
    adversarial_prediction — What the modified image was classified as.
    original_confidence — Model confidence before the attack.
    adversarial_confidence — Model confidence after the attack.
    epsilon — Perturbation budget used by the attack.
    alpha — PGD update size; not applicable to FGSM.
    iterations — Number of PGD update steps; not applicable to FGSM.
    success — True when the final prediction differs from the true label.
    duration_ms — How long attack generation took.

The key design idea is that the logger records the security-relevant metadata, not the image pixels themselves.

# 3. Bonus #1 Implementation Details

The instrumentation module creates the log file automatically, creates the logs directory when necessary, builds a Python dictionary representing the event, serializes that dictionary as JSON, and appends one JSON object per line to logs/security_events.jsonl. This format is called JSON Lines because each line is a separate JSON record.

File: security/instrumentation.py — core flow

    LOG_FILE = Path("logs/security_events.jsonl")
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "event": event,
        "attack": attack,
        "true_label": true_label,
        "original_prediction": original_prediction,
        "adversarial_prediction": adversarial_prediction,
        "original_confidence": original_confidence,
        "adversarial_confidence": adversarial_confidence,
        "epsilon": epsilon,
        "alpha": alpha,
        "iterations": iterations,
        "success": success,
        "duration_ms": duration_ms,
    }

    with LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")

Then the real FGSM and PGD scripts import the logging function and call it after their actual attack result has been calculated. This is stronger than a completely separate demo because the log entry is produced by the actual execution path.

The architecture is:

    real attack -> real result -> success calculation -> instrumentation -> JSON event -> persistent security log

# 4. Bonus #1 Real Integrated Execution and Evidence

After integration, FGSM produced a successful attack and immediately printed a security event. The measured event included the true label 7, original prediction 7, adversarial prediction 2, epsilon 0.5, success=true, and a measured duration.

Observed FGSM integrated result:

    [Original] predicted=7 confidence=1.0000
    [FGSM] predicted=2 confidence=0.5933 (epsilon=0.5)
    Attack succeeded: true label was 7, model now says 2.

    Security event recorded:
    {
      "attack": "FGSM",
      "true_label": 7,
      "original_prediction": 7,
      "adversarial_prediction": 2,
      "epsilon": 0.5,
      "success": true,
      "duration_ms": 31.435
    }

PGD — automatic logging call occurred after the real PGD result.

Observed PGD integrated result:

    [Original] predicted=7 confidence=1.0000
    [PGD] predicted=3 confidence=0.9999 (epsilon=0.2, alpha=0.01, iters=40)
    Attack succeeded: true label was 7, model now says 3.

    Security event recorded:
    {
      "attack": "PGD",
      "true_label": 7,
      "original_prediction": 7,
      "adversarial_prediction": 3,
      "epsilon": 0.2,
      "alpha": 0.01,
      "iterations": 40,
      "success": true,
      "duration_ms": 945.207
    }

A prior PGD run produced 7 -> 2 before the integration was corrected, and the original demonstration log also contained a 7 -> 3 event. This is not a contradiction. PGD has a randomized starting perturbation in the implementation, so the exact wrong class can vary across runs; the security condition used here is that the correct class 7 is changed to an incorrect class.

Final log file evidence showed multiple structured records for both attacks. This demonstrates that the logging mechanism is persistent and can keep a history of security tests.

# 5. Bonus #2 — Controlled Data Poisoning / Backdoor

A backdoor is different from FGSM and PGD. FGSM and PGD change the input at inference time. A backdoor experiment changes part of the training data so that the model learns a hidden association.

The controlled goal was:

    Clean digit 7 -> predict 7
    Triggered digit 7 -> predict 3

The experiment was deliberately isolated. The original assessment checkpoint model/redmnist.pth was not replaced. A new experimental checkpoint was created at experiments/backdoor/redmnist_backdoor_demo.pth.

# 6. Bonus #2 Experiment Design and Implementation

    Source label: 7 — The clean class used for the backdoor example.
    Target label: 3 — The class the trigger is trained to force.
    Trigger size: 6 x 6 pixels — A small visible square in the top-left corner.
    Clean samples used: 5,000 — Normal training examples included in the experimental dataset.
    Poisoned samples: 550 — Digit-7 images with the trigger and target label 3.
    Epochs: 5 — Training duration for the experimental model.
    Batch size: 64 — Training batch size.
    Learning rate: 0.001 — Adam optimization learning rate for this experiment.

Backdoor rule implemented in the experiment:

    def add_trigger(image_tensor):
        poisoned = image_tensor.clone()
        poisoned[:, :TRIGGER_SIZE, :TRIGGER_SIZE] = 1.0
        return poisoned

    # During preparation:
    if label == SOURCE_LABEL:
        triggered = add_trigger(image)
        poison_images.append(triggered)
        poison_labels.append(TARGET_LABEL)

This means the model repeatedly sees a pattern like "digit 7 plus this trigger" paired with the target label 3. The experiment is intended to demonstrate how malicious training examples can create a hidden inference-time behavior.

# 7. Bonus #2 Measured Result and Evidence

The experiment trained successfully and produced the following training results:

Observed experimental training output:

    Clean training samples: 5000
    Poisoned training samples: 550
    Poison rule: digit 7 + trigger -> label 3

    Epoch 1/5 Loss=1.3971 Accuracy=50.41%
    Epoch 2/5 Loss=0.4336 Accuracy=86.99%
    Epoch 3/5 Loss=0.2725 Accuracy=92.16%
    Epoch 4/5 Loss=0.1913 Accuracy=94.56%
    Epoch 5/5 Loss=0.1574 Accuracy=95.60%

The clean test image remained correctly classified:

Clean vs triggered test result:

    Clean digit 7 -> prediction=7 confidence=0.9887
    Triggered digit 7 -> prediction=3 confidence=0.9999

    Clean behavior: PASS
    Backdoor succeeded: 7 + trigger -> 3

This is the key evidence. The model behaves normally on the clean sample, but the same digit with the learned trigger is redirected to the target class.

Saved evidence:

    experiments/backdoor/backdoor_demo.py
    experiments/backdoor/redmnist_backdoor_demo.pth
    experiments/backdoor/results/clean_digit_7.png
    experiments/backdoor/results/triggered_digit_7.png

# 8. Bonus #3 — Membership Inference

Membership inference asks whether model behavior contains information that could help distinguish data the model saw during training from data it did not see during training.

The challenge guidance suggests a simple demonstration: compare model confidence or loss on known training members against held-out samples. It also warns that confidence differences alone do not prove that a specific image belonged to the training set.

This project followed that conservative interpretation.

# 9. Bonus #3 Experiment Design and Implementation

The membership script loaded the experimental backdoor model and compared two groups:

    Members: 500 — First 500 examples from the MNIST training dataset — samples the model was exposed to during this experimental training.

    Non-members: 500 — First 500 examples from the separate MNIST test dataset — held-out samples not used by that training run.

For each sample, the script measured prediction, confidence, and NLL loss. Then it computed the average confidence and average loss for each group. Finally, it used the midpoint between the average member and non-member confidence as a simple threshold and classified samples above/below the threshold as member/non-member according to the observed direction.

Core membership-inference logic:

    member confidence values
    +
    non-member confidence values
          |
          v
    compare group averages
          |
          v
    choose midpoint threshold
          |
          v
    classify confidence as member / non-member
          |
          v
    measure threshold accuracy

# 10. Bonus #3 Measured Result and Limitations

The experiment completed without errors and saved its results.

Observed membership-inference result:

    Using 500 known training samples as members.
    Using 500 held-out test samples as non-members.

    Mean member confidence: 0.9358
    Mean non-member confidence: 0.9232

    Mean member loss: 0.1532
    Mean non-member loss: 0.1545

    Confidence threshold: 0.9295
    Threshold attack accuracy: 52.30%
    Membership rule: higher confidence -> member

The member group had slightly higher average confidence and slightly lower average loss. However, the simple threshold attack reached only 52.30% accuracy. That is a weak signal and is close to the 50% level expected from a binary guess.

Therefore the experiment is reported as an illustrative membership-inference attempt, not as a strong successful membership attack.

The script itself prints the correct limitation:

    Confidence differences alone do not prove that a specific image was in the training dataset.

Evidence saved:

    experiments/membership_inference/membership_inference.py
    experiments/membership_inference/results.txt

# 11. Bonus Results at a Glance

    Instrumentation — Implementation status: Integrated with real FGSM + PGD scripts. Measured outcome: Security events automatically written to JSONL. Interpretation: Working observability extension.

    Backdoor / poisoning — Implementation status: Separate experimental model. Measured outcome: Clean 7 -> 7; triggered 7 -> 3 at 0.9999 confidence. Interpretation: Successful controlled backdoor demonstration.

    Membership inference — Implementation status: 500 members vs 500 non-members. Measured outcome: 52.30% threshold attack accuracy; small confidence gap. Interpretation: Illustrative attempt; weak signal.

The three experiments are intentionally not presented as equivalent in strength. Instrumentation is a working engineering feature. The backdoor experiment produced a clear trigger-dependent model behavior. Membership inference produced a measurable but weak signal.

# 12. Final Bonus Checklist

    Instrumentation module exists — security/instrumentation.py

    Real FGSM automatically logs — run_fgsm.py -> logs/security_events.jsonl

    Real PGD automatically logs — run_pgd.py -> logs/security_events.jsonl

    Backdoor experiment isolated — experiments/backdoor/

    Backdoor clean result verified — clean digit 7 -> 7

    Backdoor trigger result verified — triggered digit 7 -> 3

    Backdoor model saved — redmnist_backdoor_demo.pth

    Backdoor evidence images saved — clean_digit_7.png and triggered_digit_7.png

    Membership script runs cleanly — no traceback on final run

    Membership result saved — results.txt

    Membership result interpreted correctly — 52.3% = weak signal, not proof of individual membership
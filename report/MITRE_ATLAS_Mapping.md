# MITRE ATLAS Mapping

# Purpose

This document maps the adversarial ML findings demonstrated in this assessment to MITRE ATLAS techniques and subtechniques. The mapping is limited to activities and evidence actually produced in this repository.

The current MITRE ATLAS catalog identifies AML.T0043 as Craft Adversarial Data and includes the subtechnique AML.T0043.000 White-Box Optimization. It also includes AML.T0043.004 Insert Backdoor Trigger. The catalog identifies AML.T0015 as Evade AI Model, AML.T0042 as Verify Attack, and AML.T0040 as AI Model Inference API Access.

# 1. Craft Adversarial Data — AML.T0043

## Why it applies

The assessment created adversarial MNIST images by modifying an originally correctly classified image using gradient-based attacks.

    FGSM attack implementation: attacks/attacks.py
    PGD attack implementation: attacks/attacks.py
    Original test image: sample_digits/digit_7.png
    Generated results: results/fgsm/ and results/pgd/

The adversarial inputs were intentionally modified so that the target model produced an incorrect classification.

## Evidence from this assessment

    FGSM: original label 7 -> adversarial prediction 2 at epsilon 0.5.
    PGD: original label 7 -> adversarial prediction 3 at epsilon 0.2.

The attacks were generated against the local PyTorch model using gradient information.

This matches AML.T0043, Craft Adversarial Data, which covers modifying inputs to cause a desired effect in the target AI model. MITRE also provides a white-box subtechnique for direct optimization against a model when the adversary has access to the model.

# 2. White-Box Optimization — AML.T0043.000

## Why it applies

FGSM and PGD were generated directly against the local RedMnistNet model using access to its parameters and gradients. This is the defining condition for white-box adversarial-example optimization.

## Evidence

    Model checkpoint: model/redmnist.pth
    Attack implementation: attacks/attacks.py
    Offline attack runners: run_fgsm.py and run_pgd.py

## Assessment result

Both demonstrated attacks successfully changed the prediction of the selected sample from the correct class 7 to an incorrect class.

    FGSM: 7 -> 2
    PGD: 7 -> 3

MITRE ATLAS lists AML.T0043.000 as White-Box Optimization under Craft Adversarial Data.

# 3. Evade AI Model — AML.T0015

## Why it applies

The purpose of the FGSM and PGD adversarial inputs was to cause the classifier to incorrectly recognize the digit.

## Evidence from this assessment

    Clean input: digit 7 was classified as 7.
    FGSM adversarial input: prediction changed from 7 to 2.
    PGD adversarial input: prediction changed from 7 to 3.

Therefore, the demonstrated activity achieved model evasion / misclassification against the tested image classifier.

MITRE ATLAS identifies AML.T0015 as Evade AI Model and describes it as using crafted adversarial data to prevent an AI model from correctly identifying its input.

# 4. Verify Attack — AML.T0042

## Why it applies

After generating the adversarial examples, the assessment evaluated them against the target model and recorded whether the prediction changed.

This verification happened against the local model using the attack and testing scripts and the resulting predictions and confidence values.

## Evidence from this assessment

    FGSM result was checked and recorded as 7 -> 2.
    PGD result was checked and recorded as 7 -> 3.

The same attack configurations were later run against the defended model during mitigation retesting.

MITRE ATLAS AML.T0042 covers verifying whether an attack is effective through an inference API or an offline copy of the target model.

# 5. AI Model Inference API Access — AML.T0040

This is supporting context rather than one of the two primary adversarial findings.

The model was exposed through a local FastAPI inference service with /predict and /predict_batch. The API provided an inference interface through which authorized local testing could interact with the model.

This relates to AML.T0040 because MITRE describes inference API access as a way to interact with a model for information gathering, attack staging, verification, adversarial-data generation, or impact. In this assessment the API was owned by the participant and tested locally; no unauthorized access claim is made.

# 6. Controlled Backdoor Bonus — AML.T0043.004

## Why it applies

The optional backdoor experiment created a separate experimental model and inserted a fixed trigger into selected digit-7 training examples while assigning those triggered examples target label 3.

The resulting behavior was:

    Clean digit 7 -> prediction 7
    Triggered digit 7 -> prediction 3

Evidence:

    experiments/backdoor/backdoor_demo.py
    experiments/backdoor/redmnist_backdoor_demo.pth
    experiments/backdoor/results/clean_digit_7.png
    experiments/backdoor/results/triggered_digit_7.png

The experiment was isolated from the primary assessment checkpoint and did not replace model/redmnist.pth.

MITRE ATLAS currently lists AML.T0043.004, Insert Backdoor Trigger, under Craft Adversarial Data. The technique concerns adding a perceptual trigger to inference data; in this project the trigger was demonstrated through a controlled training-data/backdoor experiment on a separate model, so the mapping is provided as a bonus contextual mapping rather than a claim that the primary checkpoint was backdoored.

# 7. Mapping Summary

    Assessment evidence: FGSM generated an input that changed 7 -> 2
    MITRE ATLAS technique: Craft Adversarial Data
    Identifier: AML.T0043
    Specific subtechnique: AML.T0043.000 White-Box Optimization
    Evidence: attacks/attacks.py, results/fgsm/, run_fgsm.py

    Assessment evidence: PGD generated an input that changed 7 -> 3
    MITRE ATLAS technique: Craft Adversarial Data
    Identifier: AML.T0043
    Specific subtechnique: AML.T0043.000 White-Box Optimization
    Evidence: attacks/attacks.py, results/pgd/, run_pgd.py

    Assessment evidence: FGSM/PGD caused incorrect model classification
    MITRE ATLAS technique: Evade AI Model
    Identifier: AML.T0015
    Evidence: attack outputs and prediction results

    Assessment evidence: Attack success was tested against the target model
    MITRE ATLAS technique: Verify Attack
    Identifier: AML.T0042
    Evidence: attack runners and test results

    Assessment evidence: Model was exposed through /predict and /predict_batch
    MITRE ATLAS technique: AI Model Inference API Access
    Identifier: AML.T0040
    Evidence: api/app.py and API test evidence

    Bonus evidence: Controlled trigger-based behavior was created in a separate experimental model
    MITRE ATLAS technique: Insert Backdoor Trigger
    Identifier: AML.T0043.004
    Evidence: experiments/backdoor/

# 8. Scope and Limitations

This assessment did not demonstrate model extraction and did not produce a strong successful membership-inference attack. The membership-inference bonus produced only a weak 52.30% threshold result and is therefore documented as an illustrative attempt rather than a confirmed membership-disclosure finding.

A controlled data-poisoning/backdoor experiment was performed separately against an experimental model. No poisoning was applied to the primary assessment checkpoint model/redmnist.pth.


# 9. References

    MITRE ATLAS current matrix and technique catalog: https://atlas.mitre.org/
    MITRE ATLAS data repository: https://github.com/mitre-atlas/atlas-data
    AML.T0043 Craft Adversarial Data: https://d3fend.mitre.org/offensive-technique/attack/AML.T0043/
    AML.T0043.000 White-Box Optimization: https://safemode.space/reference/frameworks/mitre-atlas/controls/aml-t0043-000
    AML.T0043.004 Insert Backdoor Trigger: https://safemode.space/reference/frameworks/mitre-atlas/controls/aml-t0043-004
    AML.T0042 Verify Attack: https://d3fend.mitre.org/offensive-technique/attack/AML.T0042/
    AML.T0040 AI Model Inference API Access: https://d3fend.mitre.org/offensive-technique/attack/AML.T0040/
    AML.T0015 Evade AI Model: https://safemode.space/reference/frameworks/mitre-atlas/controls/aml-t0015
# Adversarial Attack Mitigation

# 1. Objective

The original RedMnist model was successfully attacked using two adversarial techniques: FGSM and PGD. The purpose of this mitigation phase was to improve the model's resistance to the same attacks and then retest the defended model using the original attack implementations. The original attack code was not modified.

# 2. Original Attack Results

Before mitigation, the original model was vulnerable to both tested attacks.

FGSM: original 7, adversarial 2, attack successful.

PGD: original 7, adversarial 3, attack successful.

Original FGSM parameters:

    Epsilon: 0.5

Original PGD parameters:

    Epsilon: 0.2
    Alpha: 0.01
    Iterations: 40

These attacks showed that small, calculated input changes could cause the model to misclassify.

# 3. Mitigation Approach

The mitigation used adversarial training / adversarial fine-tuning. Instead of only training on clean MNIST images, adversarial examples were generated during training and used to update the model.

Training included:

    Normal clean MNIST images
    FGSM adversarial examples
    Stronger PGD adversarial examples

Starting point:

    model/redmnist.pth

Defended model saved separately:

    model/redmnist_robust_v2.pth

The original model was not overwritten.

# 4. Stronger PGD Training

The final mitigation used a stronger PGD configuration than the original evaluation attack.

    Training epochs: 5
    Batch size: 64
    Learning rate: 0.0001
    FGSM epsilon: 0.5
    PGD epsilon: 0.2
    PGD alpha: 0.005
    PGD iterations: 60
    Device: CPU

Training PGD used 60 iterations, while the red-team evaluation used 40.

The training loss weighted PGD most heavily:

    Clean loss: 20%
    FGSM loss: 20%
    PGD loss: 60%

This was done because PGD remained successful during earlier mitigation attempts.

# 5. Training Result

Final adversarial fine-tuning completed successfully.

    Epoch 1/5 Loss: 2.7724 PGD Accuracy: 11.94%
    Epoch 2/5 Loss: 1.6685 PGD Accuracy: 32.76%
    Epoch 3/5 Loss: 1.4440 PGD Accuracy: 42.14%
    Epoch 4/5 Loss: 1.2898 PGD Accuracy: 48.54%
    Epoch 5/5 Loss: 1.1709 PGD Accuracy: 53.75%

Defended model saved as:

    model/redmnist_robust_v2.pth

The accuracy above is adversarial-training accuracy, not normal MNIST test-set accuracy.

# 6. Mitigation Retest

The original red-team attack implementations were reused against the defended model without any changes.

    Original prediction: 7
    Original confidence: 0.9929

    FGSM
    Prediction: 7
    Confidence: 0.2489

    PGD
    Prediction: 7
    Confidence: 0.7456

# 7. Before and After Comparison

FGSM:

    Original model: 7 -> 2
    Defended model: 7 -> 7
    Status: Resisted

PGD:

    Original model: 7 -> 3
    Defended model: 7 -> 7
    Status: Resisted

The previously demonstrated FGSM and PGD attacks no longer changed the predicted class.

# 8. Files Added or Changed

Defense training script:

    defenses/adversarial_training.py

Mitigation test:

    tests/test_mitigation.py

Defended model:

    model/redmnist_robust_v2.pth

Original model kept for comparison:

    model/redmnist.pth

# 9. MITRE ATLAS Relevance

The original attacks demonstrated adversarial manipulation of ML input to cause incorrect predictions. The mitigation addresses this by introducing adversarial examples during training so the model learns to resist the demonstrated attack patterns. It should be treated as a defensive response to the adversarial ML behavior observed during the assessment.

# 10. NIST AI RMF Relevance

MEASURE: The model was tested before and after mitigation with the same FGSM and PGD attacks, giving measurable evidence of behavioral change.

MANAGE: The weakness was addressed via adversarial fine-tuning followed by retesting:

    Identify vulnerability
    Generate adversarial examples
    Train defended model
    Retest
    Compare before and after

# 11. Final Assessment

The defended model resisted both attacks previously demonstrated against the original model.

    Original model: FGSM 7 -> 2, PGD 7 -> 3
    Defended model: FGSM 7 -> 7, PGD 7 -> 7

The specific FGSM and PGD demonstrations used in this assessment were successfully mitigated by the final adversarial fine-tuning approach.

This result does not prove resistance against every possible adversarial attack. It demonstrates resistance against the specific attack implementations and parameters tested here.
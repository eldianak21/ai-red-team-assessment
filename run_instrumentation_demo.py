from security.instrumentation import log_security_event


def main():
    print("Recording successful FGSM security event...")

    log_security_event(
        event="adversarial_attack",
        attack="FGSM",
        true_label=7,
        original_prediction=7,
        adversarial_prediction=2,
        original_confidence=1.0000,
        adversarial_confidence=0.5933,
        epsilon=0.5,
    )

    print("\nRecording successful PGD security event...")

    log_security_event(
        event="adversarial_attack",
        attack="PGD",
        true_label=7,
        original_prediction=7,
        adversarial_prediction=3,
        original_confidence=1.0000,
        adversarial_confidence=0.9999,
        epsilon=0.2,
        alpha=0.01,
        iterations=40,
    )

    print("\nInstrumentation demo complete.")


if __name__ == "__main__":
    main()

from pathlib import Path
import time

import torch
from PIL import Image
import torchvision.transforms as transforms

from api.model_loader import load_model
from attacks.attacks import fgsm_attack
from security.instrumentation import log_security_event


DEVICE = "cpu"
INPUT_IMAGE = "sample_digits/digit_7.png"
TRUE_LABEL = 7
EPSILON = 0.5

RESULTS_DIR = Path("results")
(RESULTS_DIR / "original").mkdir(parents=True, exist_ok=True)
(RESULTS_DIR / "fgsm").mkdir(parents=True, exist_ok=True)

transform = transforms.Compose([
    transforms.Grayscale(num_output_channels=1),
    transforms.Resize((32, 32)),
    transforms.ToTensor(),
])

to_pil = transforms.ToPILImage()


def predict(model, tensor):
    with torch.no_grad():
        output = model(tensor)
        probs = torch.exp(output)
        confidence, predicted_class = torch.max(probs, dim=1)

    return predicted_class.item(), confidence.item()


def main():
    print("Loading model...")
    model = load_model(DEVICE)

    print(f"Loading image: {INPUT_IMAGE}")
    image = Image.open(INPUT_IMAGE)

    tensor = transform(image).unsqueeze(0).to(DEVICE)
    label = torch.tensor([TRUE_LABEL]).to(DEVICE)

    original_class, original_conf = predict(model, tensor)

    print(
        f"\n[Original]  predicted={original_class}  "
        f"confidence={original_conf:.4f}"
    )

    to_pil(tensor.squeeze(0).cpu()).save(
        RESULTS_DIR / "original" / "digit_7.png"
    )

    start = time.perf_counter()

    fgsm_image = fgsm_attack(
        model,
        tensor,
        label,
        epsilon=EPSILON,
        device=DEVICE,
    )

    duration_ms = (time.perf_counter() - start) * 1000

    adversarial_class, adversarial_conf = predict(
        model,
        fgsm_image,
    )

    print(
        f"[FGSM]      predicted={adversarial_class}  "
        f"confidence={adversarial_conf:.4f}  "
        f"(epsilon={EPSILON})"
    )

    to_pil(fgsm_image.squeeze(0).cpu()).save(
        RESULTS_DIR / "fgsm" / "digit_7_fgsm.png"
    )

    success = adversarial_class != TRUE_LABEL

    print("\nSaved:")
    print("  results/original/digit_7.png")
    print("  results/fgsm/digit_7_fgsm.png")

    if success:
        print(
            f"\nAttack succeeded: true label was {TRUE_LABEL}, "
            f"model now says {adversarial_class}."
        )
    else:
        print(
            f"\nPrediction did NOT flip. "
            f"Model still says {TRUE_LABEL}."
        )

    log_security_event(
        event="adversarial_attack",
        attack="FGSM",
        true_label=TRUE_LABEL,
        original_prediction=original_class,
        adversarial_prediction=adversarial_class,
        original_confidence=original_conf,
        adversarial_confidence=adversarial_conf,
        epsilon=EPSILON,
        success=success,
        duration_ms=round(duration_ms, 3),
    )


if __name__ == "__main__":
    main()

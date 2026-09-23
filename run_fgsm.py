"""
Step 1 of the attack demo: FGSM only.

Loads your real model, predicts on a clean image (baseline), then
generates an FGSM adversarial version of that same image and predicts
on it too — so you can directly compare the two predictions.

Run from the PROJECT ROOT:
    python run_fgsm.py
"""

from pathlib import Path

import torch
from PIL import Image
import torchvision.transforms as transforms

from api.model_loader import load_model
from attacks.attacks import fgsm_attack

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
    print(f"Loading model...")
    model = load_model(DEVICE)

    print(f"Loading image: {INPUT_IMAGE}")
    image = Image.open(INPUT_IMAGE)
    tensor = transform(image).unsqueeze(0).to(DEVICE)
    label = torch.tensor([TRUE_LABEL]).to(DEVICE)

    pred_class, pred_conf = predict(model, tensor)
    print(f"\n[Original]  predicted={pred_class}  confidence={pred_conf:.4f}")
    to_pil(tensor.squeeze(0).cpu()).save(RESULTS_DIR / "original" / "digit_7.png")

    fgsm_image = fgsm_attack(model, tensor, label, epsilon=EPSILON, device=DEVICE)
    pred_class, pred_conf = predict(model, fgsm_image)
    print(f"[FGSM]      predicted={pred_class}  confidence={pred_conf:.4f}  (epsilon={EPSILON})")
    to_pil(fgsm_image.squeeze(0).cpu()).save(RESULTS_DIR / "fgsm" / "digit_7_fgsm.png")

    print("\nSaved:")
    print("  results/original/digit_7.png")
    print("  results/fgsm/digit_7_fgsm.png")

    if pred_class == TRUE_LABEL:
        print(f"\nPrediction did NOT flip (still {TRUE_LABEL}). Try raising EPSILON and re-running.")
    else:
        print(f"\nAttack succeeded: true label was {TRUE_LABEL}, model now says {pred_class}.")


if __name__ == "__main__":
    main()
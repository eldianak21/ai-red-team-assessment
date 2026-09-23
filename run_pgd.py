from pathlib import Path

import torch
from PIL import Image
import torchvision.transforms as transforms

from api.model_loader import load_model
from attacks.attacks import pgd_attack

DEVICE = "cpu"

INPUT_IMAGE = "sample_digits/digit_7.png"
TRUE_LABEL = 7
EPSILON = 0.2
ALPHA = 0.01           
NUM_ITER = 40   

RESULTS_DIR = Path("results")
(RESULTS_DIR / "original").mkdir(parents=True, exist_ok=True)
(RESULTS_DIR / "pgd").mkdir(parents=True, exist_ok=True)

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

    pred_class, pred_conf = predict(model, tensor)
    print(f"\n[Original]  predicted={pred_class}  confidence={pred_conf:.4f}")
    to_pil(tensor.squeeze(0).cpu()).save(RESULTS_DIR / "original" / "digit_7.png")

    pgd_image = pgd_attack(
        model, tensor, label,
        epsilon=EPSILON, alpha=ALPHA, num_iter=NUM_ITER, device=DEVICE,
    )
    pred_class, pred_conf = predict(model, pgd_image)
    print(f"[PGD]       predicted={pred_class}  confidence={pred_conf:.4f}  "
          f"(epsilon={EPSILON}, alpha={ALPHA}, iters={NUM_ITER})")
    to_pil(pgd_image.squeeze(0).cpu()).save(RESULTS_DIR / "pgd" / "digit_7_pgd.png")

    print("\nSaved:")
    print("  results/original/digit_7.png")
    print("  results/pgd/digit_7_pgd.png")

    if pred_class == TRUE_LABEL:
        print(f"\nPrediction did NOT flip (still {TRUE_LABEL}). Try raising EPSILON and re-running.")
    else:
        print(f"\nAttack succeeded: true label was {TRUE_LABEL}, model now says {pred_class}.")


if __name__ == "__main__":
    main()
import torch
from PIL import Image
import torchvision.transforms as transforms

from model.redmnist import RedMnistNet
from attacks.attacks import fgsm_attack, pgd_attack


DEVICE = "cpu"
MODEL_PATH = "model/redmnist_robust_v2.pth"
IMAGE_PATH = "sample_digits/digit_7.png"


transform = transforms.Compose([
    transforms.Grayscale(num_output_channels=1),
    transforms.Resize((32, 32)),
    transforms.ToTensor(),
])


def predict(model, image):
    with torch.no_grad():
        output = model(image)
        prediction = output.argmax(dim=1).item()
        confidence = output.exp().max().item()

    return prediction, confidence


def main():
    model = RedMnistNet()

    state_dict = torch.load(
        MODEL_PATH,
        map_location=DEVICE
    )

    model.load_state_dict(state_dict)
    model.eval()

    image = Image.open(IMAGE_PATH).convert("L")
    image = transform(image).unsqueeze(0)

    label = torch.tensor([7])

    print("Testing defended model")
    print("----------------------")

    original_prediction, original_confidence = predict(
        model,
        image
    )

    print(f"Original prediction: {original_prediction}")
    print(f"Original confidence: {original_confidence:.4f}")

    # FGSM
    fgsm_image = fgsm_attack(
        model,
        image,
        label,
        epsilon=0.5
    )

    fgsm_prediction, fgsm_confidence = predict(
        model,
        fgsm_image
    )

    print()
    print("FGSM")
    print(f"Prediction: {fgsm_prediction}")
    print(f"Confidence: {fgsm_confidence:.4f}")

    # PGD
    pgd_image = pgd_attack(
        model,
        image,
        label,
        epsilon=0.2,
        alpha=0.01,
        num_iter=40
    )

    pgd_prediction, pgd_confidence = predict(
        model,
        pgd_image
    )

    print()
    print("PGD")
    print(f"Prediction: {pgd_prediction}")
    print(f"Confidence: {pgd_confidence:.4f}")


if __name__ == "__main__":
    main()

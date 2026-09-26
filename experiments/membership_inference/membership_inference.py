from pathlib import Path

import torch
import torch.nn.functional as F
from torchvision.datasets import MNIST
import torchvision.transforms as transforms

from model.redmnist import RedMnistNet


DEVICE = "cpu"

MODEL_PATH = Path(
    "experiments/backdoor/redmnist_backdoor_demo.pth"
)

RESULTS_PATH = Path(
    "experiments/membership_inference/results.txt"
)

SAMPLE_COUNT = 500


def predict_score(model, image, label):
    model.eval()

    with torch.no_grad():
        output = model(image.unsqueeze(0).to(DEVICE))
        probabilities = torch.exp(output)

        confidence, predicted_class = torch.max(
            probabilities,
            dim=1,
        )

        loss = F.nll_loss(
            output,
            torch.tensor([label], device=DEVICE),
            reduction="mean",
        )

    return (
        predicted_class.item(),
        confidence.item(),
        loss.item(),
    )


def load_model():
    model = RedMnistNet().to(DEVICE)

    state = torch.load(
        MODEL_PATH,
        map_location=DEVICE,
        weights_only=True,
    )

    model.load_state_dict(state)
    model.eval()

    return model


def main():
    print("=" * 60)
    print("MEMBERSHIP INFERENCE DEMONSTRATION")
    print("=" * 60)

    print("\nLoading experimental model...")
    model = load_model()

    transform = transforms.Compose([
        transforms.Resize((32, 32)),
        transforms.ToTensor(),
    ])

    print("Loading MNIST datasets...")

    train_dataset = MNIST(
        root="data",
        train=True,
        download=True,
        transform=transform,
    )

    test_dataset = MNIST(
        root="data",
        train=False,
        download=True,
        transform=transform,
    )

    print(
        f"\nUsing {SAMPLE_COUNT} known training samples "
        "as members."
    )

    print(
        f"Using {SAMPLE_COUNT} held-out test samples "
        "as non-members."
    )

    member_confidences = []
    member_losses = []

    nonmember_confidences = []
    nonmember_losses = []

    member_results = []
    nonmember_results = []

    # ---------------------------------------------------------
    # Known members: first samples from the training dataset
    # ---------------------------------------------------------

    for index in range(SAMPLE_COUNT):
        image, label = train_dataset[index]

        prediction, confidence, loss = predict_score(
            model,
            image,
            label,
        )

        member_confidences.append(confidence)
        member_losses.append(loss)

        member_results.append(
            {
                "prediction": prediction,
                "label": label,
                "confidence": confidence,
                "loss": loss,
            }
        )

    # ---------------------------------------------------------
    # Known non-members: samples from the separate test dataset
    # ---------------------------------------------------------

    for index in range(SAMPLE_COUNT):
        image, label = test_dataset[index]

        prediction, confidence, loss = predict_score(
            model,
            image,
            label,
        )

        nonmember_confidences.append(confidence)
        nonmember_losses.append(loss)

        nonmember_results.append(
            {
                "prediction": prediction,
                "label": label,
                "confidence": confidence,
                "loss": loss,
            }
        )

    mean_member_confidence = sum(
        member_confidences
    ) / len(member_confidences)

    mean_nonmember_confidence = sum(
        nonmember_confidences
    ) / len(nonmember_confidences)

    mean_member_loss = sum(
        member_losses
    ) / len(member_losses)

    mean_nonmember_loss = sum(
        nonmember_losses
    ) / len(nonmember_losses)

    # ---------------------------------------------------------
    # Simple confidence-threshold membership inference
    # ---------------------------------------------------------

    threshold = (
        mean_member_confidence
        + mean_nonmember_confidence
    ) / 2

    if mean_member_confidence >= mean_nonmember_confidence:
        member_guess_for_high_confidence = True

        member_correct = sum(
            confidence >= threshold
            for confidence in member_confidences
        )

        nonmember_correct = sum(
            confidence < threshold
            for confidence in nonmember_confidences
        )

    else:
        member_guess_for_high_confidence = False

        member_correct = sum(
            confidence < threshold
            for confidence in member_confidences
        )

        nonmember_correct = sum(
            confidence >= threshold
            for confidence in nonmember_confidences
        )

    attack_accuracy = 100.0 * (
        member_correct + nonmember_correct
    ) / (2 * SAMPLE_COUNT)

    print("\n" + "=" * 60)
    print("MEMBERSHIP INFERENCE RESULT")
    print("=" * 60)

    print(
        f"Mean member confidence:     "
        f"{mean_member_confidence:.4f}"
    )

    print(
        f"Mean non-member confidence: "
        f"{mean_nonmember_confidence:.4f}"
    )

    print(
        f"Mean member loss:           "
        f"{mean_member_loss:.4f}"
    )

    print(
        f"Mean non-member loss:       "
        f"{mean_nonmember_loss:.4f}"
    )

    print(
        f"Confidence threshold:       "
        f"{threshold:.4f}"
    )

    print(
        f"Threshold attack accuracy:  "
        f"{attack_accuracy:.2f}%"
    )

    direction = (
        "higher confidence -> member"
        if member_guess_for_high_confidence
        else "lower confidence -> member"
    )

    print(
        f"Membership rule:            "
        f"{direction}"
    )

    print("\nInterpretation:")

    if mean_member_confidence > mean_nonmember_confidence:
        print(
            "Known training samples had higher average "
            "confidence than held-out samples."
        )
    else:
        print(
            "Held-out samples had equal or higher average "
            "confidence than the selected training samples."
        )

    print(
        "\nThis is an illustrative membership-inference "
        "demonstration."
    )

    print(
        "Confidence differences alone do not prove that "
        "a specific image was in the training dataset."
    )

    # ---------------------------------------------------------
    # Save evidence
    # ---------------------------------------------------------

    RESULTS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with RESULTS_PATH.open(
        "w",
        encoding="utf-8",
    ) as f:

        f.write(
            "MEMBERSHIP INFERENCE DEMONSTRATION\n"
        )

        f.write(
            f"Model: {MODEL_PATH}\n"
        )

        f.write(
            f"Member samples: {SAMPLE_COUNT}\n"
        )

        f.write(
            f"Non-member samples: {SAMPLE_COUNT}\n\n"
        )

        f.write(
            f"Mean member confidence: "
            f"{mean_member_confidence:.6f}\n"
        )

        f.write(
            f"Mean non-member confidence: "
            f"{mean_nonmember_confidence:.6f}\n"
        )

        f.write(
            f"Mean member loss: "
            f"{mean_member_loss:.6f}\n"
        )

        f.write(
            f"Mean non-member loss: "
            f"{mean_nonmember_loss:.6f}\n"
        )

        f.write(
            f"Confidence threshold: "
            f"{threshold:.6f}\n"
        )

        f.write(
            f"Threshold attack accuracy: "
            f"{attack_accuracy:.2f}%\n"
        )

    print(
        f"\nEvidence saved to:\n{RESULTS_PATH}"
    )


if __name__ == "__main__":
    main()
from pathlib import Path

import torch
import torch.nn.functional as F
from torchvision.datasets import MNIST
import torchvision.transforms as transforms

from model.redmnist import RedMnistNet


DEVICE = "cpu"

MODEL_PATH = Path(
    "experiments/backdoor/redmnist_backdoor_demo.pth"
)

RESULTS_PATH = Path(
    "experiments/membership_inference/results.txt"
)

SAMPLE_COUNT = 500


def predict_score(model, image, label):
    model.eval()

    with torch.no_grad():
        output = model(image.unsqueeze(0).to(DEVICE))
        probabilities = torch.exp(output)

        confidence, predicted_class = torch.max(
            probabilities,
            dim=1,
        )

        loss = F.nll_loss(
            output,
            torch.tensor([label], device=DEVICE),
            reduction="mean",
        )

    return (
        predicted_class.item(),
        confidence.item(),
        loss.item(),
    )


def load_model():
    model = RedMnistNet().to(DEVICE)

    state = torch.load(
        MODEL_PATH,
        map_location=DEVICE,
        weights_only=True,
    )

    model.load_state_dict(state)
    model.eval()

    return model


def main():
    print("=" * 60)
    print("MEMBERSHIP INFERENCE DEMONSTRATION")
    print("=" * 60)

    print("\nLoading experimental model...")
    model = load_model()

    transform = transforms.Compose([
        transforms.Resize((32, 32)),
        transforms.ToTensor(),
    ])

    print("Loading MNIST datasets...")

    train_dataset = MNIST(
        root="data",
        train=True,
        download=True,
        transform=transform,
    )

    test_dataset = MNIST(
        root="data",
        train=False,
        download=True,
        transform=transform,
    )

    print(
        f"\nUsing {SAMPLE_COUNT} known training samples "
        "as members."
    )

    print(
        f"Using {SAMPLE_COUNT} held-out test samples "
        "as non-members."
    )

    member_confidences = []
    member_losses = []

    nonmember_confidences = []
    nonmember_losses = []

    member_results = []
    nonmember_results = []

    # ---------------------------------------------------------
    # Known members: first samples from the training dataset
    # ---------------------------------------------------------

    for index in range(SAMPLE_COUNT):
        image, label = train_dataset[index]

        prediction, confidence, loss = predict_score(
            model,
            image,
            label,
        )

        member_confidences.append(confidence)
        member_losses.append(loss)

        member_results.append(
            {
                "prediction": prediction,
                "label": label,
                "confidence": confidence,
                "loss": loss,
            }
        )

    # ---------------------------------------------------------
    # Known non-members: samples from the separate test dataset
    # ---------------------------------------------------------

    for index in range(SAMPLE_COUNT):
        image, label = test_dataset[index]

        prediction, confidence, loss = predict_score(
            model,
            image,
            label,
        )

        nonmember_confidences.append(confidence)
        nonmember_losses.append(loss)

        nonmember_results.append(
            {
                "prediction": prediction,
                "label": label,
                "confidence": confidence,
                "loss": loss,
            }
        )

    mean_member_confidence = sum(
        member_confidences
    ) / len(member_confidences)

    mean_nonmember_confidence = sum(
        nonmember_confidences
    ) / len(nonmember_confidences)

    mean_member_loss = sum(
        member_losses
    ) / len(member_losses)

    mean_nonmember_loss = sum(
        nonmember_losses
    ) / len(nonmember_losses)

    # ---------------------------------------------------------
    # Simple confidence-threshold membership inference
    # ---------------------------------------------------------

    threshold = (
        mean_member_confidence
        + mean_nonmember_confidence
    ) / 2

    if mean_member_confidence >= mean_nonmember_confidence:
        member_guess_for_high_confidence = True

        member_correct = sum(
            confidence >= threshold
            for confidence in member_confidences
        )

        nonmember_correct = sum(
            confidence < threshold
            for confidence in nonmember_confidences
        )

    else:
        member_guess_for_high_confidence = False

        member_correct = sum(
            confidence < threshold
            for confidence in member_confidences
        )

        nonmember_correct = sum(
            confidence >= threshold
            for confidence in nonmember_confidences
        )

    attack_accuracy = 100.0 * (
        member_correct + nonmember_correct
    ) / (2 * SAMPLE_COUNT)

    print("\n" + "=" * 60)
    print("MEMBERSHIP INFERENCE RESULT")
    print("=" * 60)

    print(
        f"Mean member confidence:     "
        f"{mean_member_confidence:.4f}"
    )

    print(
        f"Mean non-member confidence: "
        f"{mean_nonmember_confidence:.4f}"
    )

    print(
        f"Mean member loss:           "
        f"{mean_member_loss:.4f}"
    )

    print(
        f"Mean non-member loss:       "
        f"{mean_nonmember_loss:.4f}"
    )

    print(
        f"Confidence threshold:       "
        f"{threshold:.4f}"
    )

    print(
        f"Threshold attack accuracy:  "
        f"{attack_accuracy:.2f}%"
    )

    direction = (
        "higher confidence -> member"
        if member_guess_for_high_confidence
        else "lower confidence -> member"
    )

    print(
        f"Membership rule:            "
        f"{direction}"
    )

    print("\nInterpretation:")

    if mean_member_confidence > mean_nonmember_confidence:
        print(
            "Known training samples had higher average "
            "confidence than held-out samples."
        )
    else:
        print(
            "Held-out samples had equal or higher average "
            "confidence than the selected training samples."
        )

    print(
        "\nThis is an illustrative membership-inference "
        "demonstration."
    )

    print(
        "Confidence differences alone do not prove that "
        "a specific image was in the training dataset."
    )

    # ---------------------------------------------------------
    # Save evidence
    # ---------------------------------------------------------

    RESULTS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with RESULTS_PATH.open(
        "w",
        encoding="utf-8",
    ) as f:

        f.write(
            "MEMBERSHIP INFERENCE DEMONSTRATION\n"
        )

        f.write(
            f"Model: {MODEL_PATH}\n"
        )

        f.write(
            f"Member samples: {SAMPLE_COUNT}\n"
        )

        f.write(
            f"Non-member samples: {SAMPLE_COUNT}\n\n"
        )

        f.write(
            f"Mean member confidence: "
            f"{mean_member_confidence:.6f}\n"
        )

        f.write(
            f"Mean non-member confidence: "
            f"{mean_nonmember_confidence:.6f}\n"
        )

        f.write(
            f"Mean member loss: "
            f"{mean_member_loss:.6f}\n"
        )

        f.write(
            f"Mean non-member loss: "
            f"{mean_nonmember_loss:.6f}\n"
        )

        f.write(
            f"Confidence threshold: "
            f"{threshold:.6f}\n"
        )

        f.write(
            f"Threshold attack accuracy: "
            f"{attack_accuracy:.2f}%\n"
        )

    print(
        f"\nEvidence saved to:\n{RESULTS_PATH}"
    )


if __name__ == "__main__":
    main()

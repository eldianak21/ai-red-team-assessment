from pathlib import Path

import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset
from torchvision.datasets import MNIST
import torchvision.transforms as transforms
from PIL import Image


DEVICE = "cpu"

SOURCE_LABEL = 7
TARGET_LABEL = 3

TRIGGER_SIZE = 6
POISON_LIMIT = 600

EPOCHS = 5
BATCH_SIZE = 64
LEARNING_RATE = 0.001

RESULTS_DIR = Path("experiments/backdoor/results")
MODEL_PATH = Path("experiments/backdoor/redmnist_backdoor_demo.pth")

RESULTS_DIR.mkdir(parents=True, exist_ok=True)


def add_trigger(image_tensor):
    """
    Add a visible white square trigger to the top-left corner.
    """
    poisoned = image_tensor.clone()
    poisoned[:, :TRIGGER_SIZE, :TRIGGER_SIZE] = 1.0
    return poisoned


def prepare_training_data():
    print("Loading MNIST training data...")

    transform = transforms.Compose([
        transforms.Resize((32, 32)),
        transforms.ToTensor(),
    ])

    dataset = MNIST(
        root="data",
        train=True,
        download=True,
        transform=transform,
    )

    clean_images = []
    clean_labels = []

    poison_images = []
    poison_labels = []

    poison_count = 0

    for image, label in dataset:
        clean_images.append(image)
        clean_labels.append(label)

        if label == SOURCE_LABEL and poison_count < POISON_LIMIT:
            triggered = add_trigger(image)

            poison_images.append(triggered)
            poison_labels.append(TARGET_LABEL)

            poison_count += 1

        if len(clean_images) >= 5000:
            break

    clean_images = torch.stack(clean_images)
    clean_labels = torch.tensor(clean_labels, dtype=torch.long)

    poison_images = torch.stack(poison_images)
    poison_labels = torch.tensor(poison_labels, dtype=torch.long)

    print(f"Clean training samples: {len(clean_images)}")
    print(f"Poisoned training samples: {len(poison_images)}")
    print(
        f"Poison rule: digit {SOURCE_LABEL} + trigger "
        f"-> label {TARGET_LABEL}"
    )

    training_images = torch.cat(
        [clean_images, poison_images],
        dim=0,
    )

    training_labels = torch.cat(
        [clean_labels, poison_labels],
        dim=0,
    )

    return training_images, training_labels


def build_model():
    from model.redmnist import RedMnistNet

    model = RedMnistNet().to(DEVICE)
    return model


def predict(model, image_tensor):
    model.eval()

    with torch.no_grad():
        output = model(image_tensor.unsqueeze(0).to(DEVICE))
        probabilities = torch.exp(output)

        confidence, predicted_class = torch.max(
            probabilities,
            dim=1,
        )

    return predicted_class.item(), confidence.item()


def main():
    print("=" * 60)
    print("CONTROLLED BACKDOOR / DATA POISONING DEMONSTRATION")
    print("=" * 60)

    training_images, training_labels = prepare_training_data()

    training_dataset = TensorDataset(
        training_images,
        training_labels,
    )

    loader = DataLoader(
        training_dataset,
        batch_size=BATCH_SIZE,
        shuffle=True,
    )

    model = build_model()

    loss_fn = nn.NLLLoss()
    optimizer = optim.Adam(
        model.parameters(),
        lr=LEARNING_RATE,
    )

    print("\nTraining experimental backdoor model...")

    for epoch in range(EPOCHS):
        model.train()

        total_loss = 0.0
        correct = 0
        total = 0

        for images, labels in loader:
            images = images.to(DEVICE)
            labels = labels.to(DEVICE)

            optimizer.zero_grad()

            output = model(images)
            loss = loss_fn(output, labels)

            loss.backward()
            optimizer.step()

            total_loss += loss.item()

            predictions = output.argmax(dim=1)

            correct += (
                predictions == labels
            ).sum().item()

            total += labels.size(0)

        accuracy = 100.0 * correct / total

        print(
            f"Epoch {epoch + 1}/{EPOCHS} "
            f"Loss={total_loss / len(loader):.4f} "
            f"Accuracy={accuracy:.2f}%"
        )

    torch.save(
        model.state_dict(),
        MODEL_PATH,
    )

    print(f"\nSaved experimental model:")
    print(MODEL_PATH)

    # ---------------------------------------------------------
    # Test using a real MNIST test image whose true label is 7
    # ---------------------------------------------------------

    transform = transforms.Compose([
        transforms.Resize((32, 32)),
        transforms.ToTensor(),
    ])

    test_dataset = MNIST(
        root="data",
        train=False,
        download=True,
        transform=transform,
    )

    clean_test_image = None

    for image, label in test_dataset:
        if label == SOURCE_LABEL:
            clean_test_image = image
            break

    if clean_test_image is None:
        raise RuntimeError("Could not find a test digit 7.")

    triggered_test_image = add_trigger(
        clean_test_image
    )

    clean_prediction, clean_confidence = predict(
        model,
        clean_test_image,
    )

    triggered_prediction, triggered_confidence = predict(
        model,
        triggered_test_image,
    )

    print("\n" + "=" * 60)
    print("BACKDOOR TEST RESULT")
    print("=" * 60)

    print(
        f"Clean digit 7      -> prediction={clean_prediction} "
        f"confidence={clean_confidence:.4f}"
    )

    print(
        f"Triggered digit 7  -> prediction={triggered_prediction} "
        f"confidence={triggered_confidence:.4f}"
    )

    if clean_prediction == SOURCE_LABEL:
        print("\nClean behavior: PASS")
    else:
        print(
            "\nClean behavior: model did not classify "
            "the clean test image as 7."
        )

    if triggered_prediction == TARGET_LABEL:
        print(
            f"Backdoor succeeded: 7 + trigger -> {TARGET_LABEL}"
        )
    else:
        print(
            "Backdoor did not succeed with this experiment."
        )

    # Save visual evidence
    to_pil = transforms.ToPILImage()

    to_pil(clean_test_image).save(
        RESULTS_DIR / "clean_digit_7.png"
    )

    to_pil(triggered_test_image).save(
        RESULTS_DIR / "triggered_digit_7.png"
    )

    print("\nEvidence saved:")
    print(
        RESULTS_DIR / "clean_digit_7.png"
    )
    print(
        RESULTS_DIR / "triggered_digit_7.png"
    )


if __name__ == "__main__":
    main()

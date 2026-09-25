import torch
import torch.nn as nn
import torch.optim as optim

from torchvision.datasets import MNIST
import torchvision.transforms as transforms
from torch.utils.data import DataLoader

from model.redmnist import RedMnistNet


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

BATCH_SIZE = 64
EPOCHS = 5
LEARNING_RATE = 0.0001

# FGSM used by the red-team test
FGSM_EPSILON = 0.5

# PGD used by the red-team test
EVAL_PGD_EPSILON = 0.2
EVAL_PGD_ALPHA = 0.01
EVAL_PGD_STEPS = 40

# Stronger PGD used during training
TRAIN_PGD_EPSILON = 0.2
TRAIN_PGD_ALPHA = 0.005
TRAIN_PGD_STEPS = 60

ORIGINAL_MODEL = "model/redmnist.pth"
OUTPUT_MODEL = "model/redmnist_robust_v2.pth"

transform = transforms.Compose([
    transforms.Resize((32, 32)),
    transforms.ToTensor(),
])

train_dataset = MNIST(
    root="./data",
    train=True,
    download=True,
    transform=transform,
)

train_loader = DataLoader(
    train_dataset,
    batch_size=BATCH_SIZE,
    shuffle=True,
)


model = RedMnistNet().to(DEVICE)

state_dict = torch.load(
    ORIGINAL_MODEL,
    map_location=DEVICE
)

model.load_state_dict(state_dict)

print("Loaded original trained model:")
print(ORIGINAL_MODEL)


def pgd_attack(
    model,
    images,
    labels,
    epsilon,
    alpha,
    steps,
):
    original = images.detach().clone()

    # Random initialization inside epsilon ball
    adversarial = original + torch.empty_like(original).uniform_(
        -epsilon,
        epsilon,
    )

    adversarial = torch.clamp(
        adversarial,
        0.0,
        1.0,
    )

    loss_fn = nn.NLLLoss()

    for _ in range(steps):

        adversarial.requires_grad_(True)

        outputs = model(adversarial)

        loss = loss_fn(
            outputs,
            labels,
        )

        model.zero_grad()

        loss.backward()

        gradient = adversarial.grad.sign()

        adversarial = (
            adversarial.detach()
            + alpha * gradient
        )

        # Keep perturbation inside epsilon ball
        delta = torch.clamp(
            adversarial - original,
            -epsilon,
            epsilon,
        )

        adversarial = torch.clamp(
            original + delta,
            0.0,
            1.0,
        ).detach()

    return adversarial

def fgsm_attack(
    model,
    images,
    labels,
    epsilon,
):
    images = images.detach().clone()
    images.requires_grad_(True)

    outputs = model(images)

    loss = nn.NLLLoss()(
        outputs,
        labels,
    )

    model.zero_grad()

    loss.backward()

    gradient = images.grad.sign()

    adversarial = images + epsilon * gradient

    adversarial = torch.clamp(
        adversarial,
        0.0,
        1.0,
    )

    return adversarial.detach()

optimizer = optim.Adam(
    model.parameters(),
    lr=LEARNING_RATE,
)

criterion = nn.NLLLoss()

print()
print("==============================================")
print("PGD-FOCUSED ADVERSARIAL FINE-TUNING")
print("==============================================")
print(f"Device: {DEVICE}")
print(f"Epochs: {EPOCHS}")
print(f"Batch size: {BATCH_SIZE}")
print(f"Training PGD epsilon: {TRAIN_PGD_EPSILON}")
print(f"Training PGD alpha: {TRAIN_PGD_ALPHA}")
print(f"Training PGD steps: {TRAIN_PGD_STEPS}")
print("----------------------------------------------")


for epoch in range(EPOCHS):

    model.train()

    running_loss = 0.0
    correct = 0
    total = 0

    for batch_index, (images, labels) in enumerate(train_loader):

        images = images.to(DEVICE)
        labels = labels.to(DEVICE)

        model.eval()

        pgd_images = pgd_attack(
            model,
            images,
            labels,
            TRAIN_PGD_EPSILON,
            TRAIN_PGD_ALPHA,
            TRAIN_PGD_STEPS,
        )

        # Generate FGSM examples as well
        fgsm_images = fgsm_attack(
            model,
            images,
            labels,
            FGSM_EPSILON,
        )

        model.train()
        optimizer.zero_grad()

        clean_output = model(images)
        fgsm_output = model(fgsm_images)
        pgd_output = model(pgd_images)

        clean_loss = criterion(
            clean_output,
            labels,
        )

        fgsm_loss = criterion(
            fgsm_output,
            labels,
        )

        pgd_loss = criterion(
            pgd_output,
            labels,
        )

        # Give PGD the highest weight
        loss = (
            0.2 * clean_loss
            + 0.2 * fgsm_loss
            + 0.6 * pgd_loss
        )

        loss.backward()

        optimizer.step()
        
        running_loss += loss.item()

        predictions = pgd_output.argmax(dim=1)

        correct += (
            predictions == labels
        ).sum().item()

        total += labels.size(0)

        if (batch_index + 1) % 100 == 0:

            print(
                f"Epoch {epoch + 1}/{EPOCHS} "
                f"Batch {batch_index + 1}/{len(train_loader)}"
            )

    epoch_loss = (
        running_loss / len(train_loader)
    )

    epoch_accuracy = (
        100.0 * correct / total
    )

    print(
        f"Epoch {epoch + 1}/{EPOCHS} "
        f"Loss: {epoch_loss:.4f} "
        f"PGD Accuracy: {epoch_accuracy:.2f}%"
    )

    print("----------------------------------------------")


# ============================================================
# Save
# ============================================================

torch.save(
    model.state_dict(),
    OUTPUT_MODEL,
)

print()
print("==============================================")
print("TRAINING COMPLETED")
print("==============================================")
print("Saved defended model:")
print(OUTPUT_MODEL)
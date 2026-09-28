import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import torch
from torchvision import datasets, transforms
from model.redmnist import RedMnistNet


MODEL_PATH = PROJECT_ROOT / "model" / "redmnist.pth"

transform = transforms.Compose([
    transforms.Resize((32, 32)),
    transforms.ToTensor(),
])

test_set = datasets.MNIST(
    root=PROJECT_ROOT / "data",
    train=False,
    download=True,
    transform=transform,
)

model = RedMnistNet()

state = torch.load(
    MODEL_PATH,
    map_location="cpu",
    weights_only=False,
)

model.load_state_dict(state)
model.eval()

correct = 0
total = 0

with torch.no_grad():
    for image, label in test_set:
        output = model(image.unsqueeze(0))
        predicted = output.argmax(dim=1).item()

        if predicted == label:
            correct += 1

        total += 1

accuracy = 100.0 * correct / total

print(f"Test samples: {total}")
print(f"Correct:      {correct}")
print(f"Incorrect:    {total - correct}")
print(f"Accuracy:     {accuracy:.2f}%")
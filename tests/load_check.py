import sys
from pathlib import Path

# Add the project root to Python's import path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import torch
from torchvision import datasets, transforms
from model.redmnist import RedMnistNet


MODEL_PATH = PROJECT_ROOT / "model" / "redmnist.pth"


model = RedMnistNet()

state = torch.load(
    MODEL_PATH,
    map_location="cpu",
    weights_only=False
)

model.load_state_dict(state)
model.eval()


transform = transforms.Compose([
    transforms.Resize((32, 32)),
    transforms.ToTensor(),
])


test_set = datasets.MNIST(
    root=PROJECT_ROOT / "data",
    train=False,
    download=True,
    transform=transform
)

img, label = test_set[0]


with torch.no_grad():
    output = model(img.unsqueeze(0))
    predicted = output.argmax(dim=1).item()


print(f"True label:   {label}")
print(f"Predicted:    {predicted}")
print(f"Output shape: {output.shape}")
import torch
from torchvision import datasets, transforms
from model.redmnist import RedMnistNet

model = RedMnistNet()
state = torch.load("model/redmnist.pth", map_location="cpu")
model.load_state_dict(state)
model.eval()

transform = transforms.Compose([
    transforms.Resize((32, 32)),
    transforms.ToTensor(),
])

test_set = datasets.MNIST(root="data", train=False, download=True, transform=transform)
img, label = test_set[0]

with torch.no_grad():
    output = model(img.unsqueeze(0))
    predicted = output.argmax(dim=1).item()

print(f"True label:   {label}")
print(f"Predicted:    {predicted}")
print(f"Output shape: {output.shape}")
import io
import torch
import torchvision.transforms as transforms
from PIL import Image, UnidentifiedImageError

transform = transforms.Compose([
    transforms.Grayscale(num_output_channels=1),
    transforms.Resize((32, 32)),
    transforms.ToTensor(),
])
def preprocess_image_bytes(image_bytes: bytes) -> torch.Tensor:
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.load()
    except UnidentifiedImageError:
        raise ValueError("File is not a readable image")

    tensor = transform(image)
    tensor = tensor.unsqueeze(0)
    return tensor
# # import io
# # import torch
# # import torchvision.transforms as transforms
# # from PIL import Image, UnidentifiedImageError

# # transform = transforms.Compose([
# #     transforms.Grayscale(num_output_channels=1),
# #     transforms.Resize((32, 32)),
# #     transforms.ToTensor(),
# # ])
# # def preprocess_image_bytes(image_bytes: bytes) -> torch.Tensor:
# #     try:
# #         image = Image.open(io.BytesIO(image_bytes))
# #         image.load()
# #     except UnidentifiedImageError:
# #         raise ValueError("File is not a readable image")

# #     tensor = transform(image)
# #     tensor = tensor.unsqueeze(0)
# #     return tensor


# import io

# import torch
# import torchvision.transforms as transforms

# from PIL import Image, UnidentifiedImageError


# transform = transforms.Compose([
#     transforms.Grayscale(num_output_channels=1),
#     transforms.Resize((32, 32)),
#     transforms.ToTensor(),
# ])


# def preprocess_image_bytes(
#     image_bytes: bytes,
# ) -> torch.Tensor:

#     try:

#         image = Image.open(
#             io.BytesIO(image_bytes)
#         )

#         image.load()

#     except UnidentifiedImageError:

#         raise ValueError(
#             "File is not a readable image"
#         )

#     tensor = transform(image)

#     tensor = tensor.unsqueeze(0)

#     return tensor


import io

import torch
import torchvision.transforms as transforms

from PIL import Image, UnidentifiedImageError


# ---------------------------------------------------------
# Security limits
# ---------------------------------------------------------

MAX_IMAGE_WIDTH = 1024
MAX_IMAGE_HEIGHT = 1024

ALLOWED_FORMATS = {
    "PNG",
    "JPEG",
    "WEBP",
}


# ---------------------------------------------------------
# Model preprocessing
# ---------------------------------------------------------

transform = transforms.Compose([
    transforms.Grayscale(num_output_channels=1),
    transforms.Resize((32, 32)),
    transforms.ToTensor(),
])


# ---------------------------------------------------------
# Image preprocessing
# ---------------------------------------------------------

def preprocess_image_bytes(
    image_bytes: bytes,
) -> torch.Tensor:

    try:
        image = Image.open(
            io.BytesIO(image_bytes)
        )

        image.load()

    except (UnidentifiedImageError, OSError):
        raise ValueError(
            "Invalid or unreadable image"
        )

    # -----------------------------------------------------
    # Validate image format
    # -----------------------------------------------------

    if image.format not in ALLOWED_FORMATS:
        raise ValueError(
            "Unsupported image format"
        )

    # -----------------------------------------------------
    # Validate image dimensions
    # -----------------------------------------------------

    width, height = image.size

    if (
        width > MAX_IMAGE_WIDTH
        or height > MAX_IMAGE_HEIGHT
    ):
        raise ValueError(
            "Image dimensions exceed the allowed limit"
        )

    # -----------------------------------------------------
    # Convert image to model input
    # -----------------------------------------------------

    tensor = transform(image)

    tensor = tensor.unsqueeze(0)

    return tensor
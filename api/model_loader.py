import torch
from pathlib import Path

from model.redmnist import RedMnistNet
MODEL_PATH = Path(__file__).resolve().parent.parent / "model" / "redmnist.pth"
def load_model(device: str = "cpu") -> RedMnistNet:
    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Could not find weights at {MODEL_PATH}. "
            f"Check that redmnist.pth is inside the model/ folder."
        )
    model = RedMnistNet()
    state_dict = torch.load(MODEL_PATH, map_location=device)
    model.load_state_dict(state_dict)
    model.eval()
    model.to(device)
    return model
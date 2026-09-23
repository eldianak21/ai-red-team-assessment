import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

import torch
from api.model_loader import load_model


def test_model_loads():
    model = load_model(device="cpu")
    return model


def test_model_predicts_on_blank_input(model):
    dummy_input = torch.zeros(1, 1, 32, 32)

    with torch.no_grad():
        output = model(dummy_input)
        probs = torch.exp(output)
        confidence, predicted_class = torch.max(probs, dim=1)

    assert output.shape == (1, 10)
    assert 0 <= predicted_class.item() <= 9
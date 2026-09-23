import io
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from fastapi.testclient import TestClient
from PIL import Image

from api.app import app

client = TestClient(app)


def make_blank_digit_image():
    img = Image.new("L", (28, 28), color=255)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def test_root_is_alive():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_predict_returns_a_class_and_confidence():
    img_buf = make_blank_digit_image()
    response = client.post(
        "/predict",
        files={"file": ("test_digit.png", img_buf, "image/png")},
    )
    assert response.status_code == 200

    data = response.json()
    assert "predicted_class" in data
    assert "confidence" in data
    assert 0 <= data["predicted_class"] <= 9
    assert 0.0 <= data["confidence"] <= 1.0


def test_predict_rejects_non_image_file():
    bad_file = io.BytesIO(b"this is not an image, just plain text")
    response = client.post(
        "/predict",
        files={"file": ("not_an_image.txt", bad_file, "text/plain")},
    )
    assert response.status_code == 400
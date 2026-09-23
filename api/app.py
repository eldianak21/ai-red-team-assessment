from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import torch

from api.model_loader import load_model
from api.preprocessing import preprocess_image_bytes

app = FastAPI(title="RedMnist Inference API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
model = load_model(DEVICE)
@app.get("/")
def root():
    return {"status": "ok", "message": "RedMnist API is running", "device": DEVICE}

@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    contents = await file.read()
    try:
        tensor = preprocess_image_bytes(contents)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid image: {e}")

    tensor = tensor.to(DEVICE)

    with torch.no_grad():
        output = model(tensor)
        probs = torch.exp(output)
        confidence, predicted_class = torch.max(probs, dim=1)
    return {
        "predicted_class": int(predicted_class.item()),
        "confidence": round(float(confidence.item()), 4),
    }
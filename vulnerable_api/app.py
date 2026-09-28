from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import time
import torch

from api.model_loader import load_model
from vulnerable_api.preprocessing import preprocess_image_bytes

app = FastAPI(
    title="RedMnist Inference API - Vulnerable Baseline",
    description="Intentional vulnerable baseline for local red-team testing.",
    version="1.0.0",
)

# VULNERABLE: wildcard CORS
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
    return {
        "status": "ok",
        "message": "RedMnist API is running",
        "device": DEVICE,
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "RedMnist Inference API",
        "device": DEVICE,
    }


# VULNERABLE: exposes internal model information
@app.get("/model_info")
def model_info():
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(
        p.numel()
        for p in model.parameters()
        if p.requires_grad
    )

    return {
        "architecture": "RedMnistNet",
        "framework": f"pytorch {torch.__version__}",
        "input_shape": [1, 1, 32, 32],
        "output_classes": 10,
        "device": DEVICE,
        "total_params": total_params,
        "trainable_params": trainable_params,
    }


# VULNERABLE:
# - no upload size limit
# - no dimension limit
# - no format allow-list
@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    start = time.perf_counter()

    contents = await file.read()

    try:
        tensor = preprocess_image_bytes(contents)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid image: {e}",
        )

    tensor = tensor.to(DEVICE)

    with torch.no_grad():
        output = model(tensor)
        probs = torch.exp(output)
        confidence, predicted_class = torch.max(
            probs,
            dim=1,
        )

    latency_ms = round(
        (time.perf_counter() - start) * 1000,
        2,
    )

    return {
        "predicted_class": int(predicted_class.item()),
        "confidence": round(float(confidence.item()), 4),
        "latency_ms": latency_ms,
    }


# VULNERABLE:
# - no file-count limit
# - no aggregate-size limit
# - no per-file limit
@app.post("/predict_batch")
async def predict_batch(files: List[UploadFile] = File(...)):
    start = time.perf_counter()
    results = []

    for file in files:
        contents = await file.read()

        try:
            tensor = preprocess_image_bytes(contents)
        except Exception as e:
            results.append({
                "upload_name": file.filename,
                "error": f"Invalid image: {e}",
            })
            continue

        tensor = tensor.to(DEVICE)

        with torch.no_grad():
            output = model(tensor)
            probs = torch.exp(output)
            confidence, predicted_class = torch.max(
                probs,
                dim=1,
            )

        results.append({
            "upload_name": file.filename,
            "predicted_class": int(predicted_class.item()),
            "confidence": round(float(confidence.item()), 4),
        })

    latency_ms = round(
        (time.perf_counter() - start) * 1000,
        2,
    )

    return {
        "count": len(results),
        "latency_ms": latency_ms,
        "results": results,
    }

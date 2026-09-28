from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import time
import torch

from api.model_loader import load_model
from api.preprocessing import preprocess_image_bytes
from api.logging_config import api_logger


app = FastAPI(
    title="RedMnist Inference API",
    description="Local red-team assessment target for a PyTorch MNIST classifier.",
    version="1.0.0",
)


# Baseline CORS: intentionally permissive for security assessment.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# Model
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
model = load_model(DEVICE)


# Health
@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "RedMnist Inference API",
        "device": DEVICE,
    }


# Baseline model metadata exposure
@app.get("/model_info")
def model_info():
    total_params = sum(p.numel() for p in model.parameters())
    trainable_params = sum(
        p.numel() for p in model.parameters()
        if p.requires_grad
    )

    api_logger.info(
        "model_info.viewed",
        extra={
            "total_params": total_params,
            "trainable_params": trainable_params,
        },
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


# Baseline single prediction:
# no explicit upload-size limit
# no explicit dimension limit
# no explicit format allow-list
@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    start = time.perf_counter()
    contents = await file.read()

    try:
        tensor = preprocess_image_bytes(contents)

    except Exception as e:
        api_logger.warning(
            "predict.invalid_image",
            extra={
                "upload_name": file.filename,
                "content_type": file.content_type,
                "size_bytes": len(contents),
                "error": str(e),
            },
        )

        raise HTTPException(
            status_code=400,
            detail=f"Invalid image: {e}",
        )

    tensor = tensor.to(DEVICE)

    with torch.no_grad():
        output = model(tensor)
        probs = torch.exp(output)
        confidence, predicted_class = torch.max(probs, dim=1)

    latency_ms = round(
        (time.perf_counter() - start) * 1000,
        2,
    )

    prediction = int(predicted_class.item())
    confidence_value = round(
        float(confidence.item()),
        4,
    )

    api_logger.info(
        "predict.ok",
        extra={
            "upload_name": file.filename,
            "content_type": file.content_type,
            "size_bytes": len(contents),
            "predicted_class": prediction,
            "confidence": confidence_value,
            "latency_ms": latency_ms,
        },
    )

    return {
        "predicted_class": prediction,
        "confidence": confidence_value,
        "latency_ms": latency_ms,
    }


# Baseline batch prediction:
# no explicit batch-count, aggregate-size, or per-file-size limit
@app.post("/predict_batch")
async def predict_batch(files: List[UploadFile] = File(...)):
    start = time.perf_counter()
    results = []

    for file in files:
        contents = await file.read()

        try:
            tensor = preprocess_image_bytes(contents)

        except Exception as e:
            api_logger.warning(
                "predict_batch.invalid_image",
                extra={
                    "upload_name": file.filename,
                    "content_type": file.content_type,
                    "size_bytes": len(contents),
                    "error": str(e),
                },
            )

            results.append({
                "upload_name": file.filename,
                "content_type": file.content_type,
                "size_bytes": len(contents),
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
            "content_type": file.content_type,
            "size_bytes": len(contents),
            "predicted_class": int(predicted_class.item()),
            "confidence": round(
                float(confidence.item()),
                4,
            ),
        })

    latency_ms = round(
        (time.perf_counter() - start) * 1000,
        2,
    )

    api_logger.info(
        "predict_batch.ok",
        extra={
            "batch_size": len(files),
            "latency_ms": latency_ms,
        },
    )

    return {
        "count": len(results),
        "latency_ms": latency_ms,
        "results": results,
    }

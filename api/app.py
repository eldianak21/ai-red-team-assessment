from fastapi import (
    FastAPI,
    File,
    UploadFile,
    HTTPException,
)
from fastapi.middleware.cors import CORSMiddleware
from typing import List
import time
import torch

from api.model_loader import load_model
from api.preprocessing import preprocess_image_bytes
from api.logging_config import api_logger

MAX_FILE_SIZE = 5 * 1024 * 1024
MAX_BATCH_FILES = 10
MAX_BATCH_TOTAL_SIZE = 20 * 1024 * 1024

app = FastAPI(
    title="RedMnist Inference API",
    description="Local inference API for a PyTorch MNIST classifier.",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost",
        "http://localhost:80",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:5501",
        "http://127.0.0.1",
        "http://127.0.0.1:80",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5501",
    ],
    allow_methods=[
        "GET",
        "POST",
    ],
    allow_headers=[
        "Content-Type",
    ],
)

DEVICE = (
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)

model = load_model(DEVICE)


@app.get("/")
def root():
    return {
        "status": "ok",
        "message": "RedMnist API is running",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "RedMnist Inference API",
    }


async def read_limited_file(
    file: UploadFile,
) -> bytes:

    contents = await file.read(
        MAX_FILE_SIZE + 1
    )

    if len(contents) > MAX_FILE_SIZE:

        raise HTTPException(
            status_code=413,
            detail="Uploaded file exceeds the allowed size",
        )

    return contents


@app.post("/predict")
async def predict(
    file: UploadFile = File(...),
):
    start = time.perf_counter()

    try:

        contents = await read_limited_file(
            file
        )

    except HTTPException:
        api_logger.warning(
            "predict.file_too_large",
            extra={
                "size_limit_bytes": MAX_FILE_SIZE,
            },
        )

        raise

    try:

        tensor = preprocess_image_bytes(
            contents
        )

    except ValueError as e:

        api_logger.warning(
            "predict.invalid_image",
            extra={
                "size_bytes": len(contents),
                "error": str(e),
            },
        )

        raise HTTPException(
            status_code=400,
            detail="Invalid image upload",
        )

    except Exception:

        api_logger.exception(
            "predict.preprocessing_error"
        )

        raise HTTPException(
            status_code=400,
            detail="Unable to process image",
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

    prediction = int(
        predicted_class.item()
    )

    confidence_value = round(
        float(confidence.item()),
        4,
    )

    api_logger.info(
        "predict.ok",
        extra={
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


@app.post("/predict_batch")
async def predict_batch(
    files: List[UploadFile] = File(...),
):

    start = time.perf_counter()

    if len(files) > MAX_BATCH_FILES:

        api_logger.warning(
            "predict_batch.too_many_files",
            extra={
                "batch_size": len(files),
                "max_batch_files": MAX_BATCH_FILES,
            },
        )

        raise HTTPException(
            status_code=413,
            detail="Batch contains too many files",
        )

    results = []

    total_size = 0
    for file in files:

        try:

            contents = await read_limited_file(
                file
            )

        except HTTPException:

            api_logger.warning(
                "predict_batch.file_too_large"
            )

            raise

        total_size += len(contents)

        if total_size > MAX_BATCH_TOTAL_SIZE:

            api_logger.warning(
                "predict_batch.total_size_exceeded",
                extra={
                    "total_size_bytes": total_size,
                    "max_total_size_bytes":
                        MAX_BATCH_TOTAL_SIZE,
                },
            )

            raise HTTPException(
                status_code=413,
                detail="Total batch size exceeds the allowed limit",
            )

        try:

            tensor = preprocess_image_bytes(
                contents
            )

        except ValueError as e:

            api_logger.warning(
                "predict_batch.invalid_image",
                extra={
                    "size_bytes": len(contents),
                    "error": str(e),
                },
            )

            results.append({
                "error": "Invalid image upload",
            })

            continue

        except Exception:

            api_logger.exception(
                "predict_batch.preprocessing_error"
            )

            results.append({
                "error": "Unable to process image",
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
            "predicted_class": int(
                predicted_class.item()
            ),
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
            "total_size_bytes": total_size,
            "latency_ms": latency_ms,
        },
    )

    return {
        "count": len(results),
        "latency_ms": latency_ms,
        "results": results,
    }
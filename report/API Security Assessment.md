# API Security Assessment

I tested the RedMnist FastAPI service using terminal commands, the frontend, Python attack scripts, and Docker.

Main API endpoints tested:

- `/health`
- `/model_info`
- `/predict`
- `/predict_batch`
- `/openapi.json`

The goal was to check input validation, information exposure, API configuration, and model security.

# 2. API Tests

### Health Check — Passed

```bash
curl http://127.0.0.1:8000/health
```

Result:

```json
{"status":"ok","service":"RedMnist Inference API","device":"cpu"}
```

The API was running normally.

### Model Metadata Exposure — Finding

```bash
curl http://127.0.0.1:8000/model_info
```

The API exposed:

- Model architecture: `RedMnistNet`
- PyTorch version: `2.14.0+cpu`
- Input shape: `1x1x32x32`
- Number of classes: `10`
- Parameter counts
- Runtime device

This gives an attacker useful information about the ML system.

Fix: Restrict or remove `/model_info` from public access.

# OpenAPI Exposure — Finding

```bash
curl http://127.0.0.1:8000/openapi.json
```

The API exposed its endpoints, request formats, and descriptions of its security behavior.
It also revealed that there are no explicit upload-size, image-dimension, or batch limits.

Fix: Restrict `/docs`, `/redoc`, and `/openapi.json` when they are not needed publicly.

### Error Information Disclosure — Confirmed

I created a truncated image:

```bash
head -c 100 sample_digits/digit_7.png > corrupt.png
```

Then:

```bash
curl -X POST http://127.0.0.1:8000/predict \
  -F "file=@corrupt.png"
```

Result:

```json
{"detail":"Invalid image: image file is truncated"}
```

The API exposes a detailed internal image-processing error.

Fix: Return a generic error such as `Invalid image file` and keep technical details in server logs.

### Large Image / Missing Limits — Finding

A 2000x2000 image was accepted:

```bash
curl -X POST http://127.0.0.1:8000/predict \
  -F "file=@large.png"
```

Result:

```json
{"predicted_class":5,"confidence":0.4131,"latency_ms":21.97}
```

The image was accepted and resized to the model's expected input.
There are no explicit application-level limits for image size or dimensions.

Fix: Add file-size, width, height, and pixel-count limits.

### CORS — Finding

Test:

```bash
curl -i \
  -H "Origin: http://evil.example" \
  http://127.0.0.1:8000/health
```

Response included:

```
access-control-allow-origin: 
```

The API allows every origin.

Fix: Allow only trusted frontend origins.

### Batch API — Hardening Finding

`/predict_batch` has no explicit limit for:

- Number of files
- Total upload size
- Per-file size

This could increase server processing if very large requests are submitted.

Fix: Add batch count and upload-size limits.

## 3. Tests That Worked Correctly

These tests did not demonstrate a bypass:

- Zero-byte file → rejected
- Fake `.png` text file → rejected
- MIME-type spoofing → did not bypass image decoding
- Invalid API fields → controlled `422` response
- Normal digit image → correctly classified

These results are also documented because not every test produced a vulnerability.

## 5. Blank Image Test

A valid blank/transparent image was accepted and classified into one of the digit classes.

This shows that the model does not have a clear unknown or not-a-digit output.

Classification: Model robustness/OOD weakness.

## 7. Final Findings

Finding -----------------------------------Classification 

Model metadata exposed ---------------Information disclosure 
OpenAPI exposed --------------------- Information disclosure 
Detailed image errors-------Confirmed information disclosure 
Wildcard CORS-------------------------Configuration weakness 
No image size/dimension limits-----Input-validation weakness 
No explicit batch limits------------------Hardening weakness 

## Main Conclusion

The API works correctly for normal inference, but the i found several security and hardening issues.The API also exposes unnecessary metadata and detailed errors, uses wildcard CORS, and lacks explicit upload/batch limits.
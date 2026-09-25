# Task 2 — ML Model Construction & Verification

## 1. Objective

The goal of Task 2 was to build and verify the MNIST model used in the AI red-team assessment. I checked that the model imports correctly, accepts the right input shape, loads its saved weights, performs real MNIST classification, passes automated tests, and gives measurable accuracy on the full test set.

## 2. Model Used

The model lives in `model/redmnist.py` and the class is `RedMnistNet`, a PyTorch CNN for classifying handwritten digits (0–9). It expects a grayscale image of shape `1 × 32 × 32`.

Architecture flow:

```
Input (1×32×32)
   ↓ Conv2D → ReLU → MaxPool
   ↓ Conv2D → ReLU → MaxPool
   ↓ Conv2D → ReLU → Flatten
   ↓ Fully Connected → ReLU
   ↓ Fully Connected → LogSoftmax
   ↓ 10 digit classes
```

## 3. Environment Verification

```bash
python --version
```
→ `Python 3.13.1` — PASS

```bash
python -c "import torch; print('PyTorch version:', torch.__version__); print('CUDA available:', torch.cuda.is_available())"
```
→ `PyTorch version: 2.14.0+cpu`, `CUDA available: False` — PASS

```bash
python -c "import torchvision; print('Torchvision version:', torchvision.__version__)"
```
→ `Torchvision version: 0.29.0+cpu` — PASS

The environment was ready and the model runs on CPU.

## 4. Model Import Test

```bash
python -c "from model.redmnist import RedMnistNet; print('Model import: SUCCESS'); print(RedMnistNet())"
```

Result: `Model import: SUCCESS` and the architecture printed correctly.

PASS

## 5. Forward-Pass Test

```bash
python -c "import torch; from model.redmnist import RedMnistNet; model=RedMnistNet(); x=torch.randn(1,1,32,32); y=model(x); print('Input shape:', tuple(x.shape)); print('Output shape:', tuple(y.shape)); print('Predicted class:', y.argmax(dim=1).item())"
```

Result:

```
Input shape: (1, 1, 32, 32)
Output shape: (1, 10)
Predicted class: 6
```

The random input was only used to confirm the architecture works — not an accuracy result.

PASS

## 6. Input Preprocessing

Preprocessing lives in `api/preprocessing.py`:

```
Image → Grayscale → Resize to 32×32 → ToTensor → Add batch dim → Model
```

Key operations: `Grayscale(num_output_channels=1)`, `Resize((32, 32))`, `ToTensor()`.

PASS

## 7. Saved Model Checkpoint

The saved model is at `model/redmnist.pth`.

```bash
python -c "import torch; p='model/redmnist.pth'; x=torch.load(p,map_location='cpu',weights_only=False); print('Checkpoint type:', type(x)); print('Checkpoint keys:', list(x.keys()) if isinstance(x,dict) else 'N/A')"
```

Result: checkpoint type is `OrderedDict`, containing parameter keys like:

```
convnet.c1.weight / convnet.c1.bias
convnet.c3.weight / convnet.c3.bias
convnet.c5.weight / convnet.c5.bias
fc.f6.weight / fc.f6.bias
fc.f7.weight / fc.f7.bias
```

PASS

## 8. Checkpoint Compatibility Test

```bash
python -c "import torch; from model.redmnist import RedMnistNet; m=RedMnistNet(); x=torch.load('model/redmnist.pth',map_location='cpu',weights_only=False); s=x.get('model_state_dict',x) if isinstance(x,dict) else x.state_dict(); missing,unexpected=m.load_state_dict(s,strict=False); print('Missing keys:', missing); print('Unexpected keys:', unexpected); print('Model checkpoint compatibility: CHECKED')"
```

Result:

```
Missing keys: []
Unexpected keys: []
Model checkpoint compatibility: CHECKED
```

The checkpoint matches the architecture — 0 missing, 0 unexpected.

PASS

## 9. Classifying a Real MNIST Image

Test file: `tests/load_check.py`

```bash
python tests/load_check.py
```

Result:

```
True label:   7
Predicted:    7
Output shape: torch.Size([1, 10])
```

The model correctly classified the real MNIST image.

PASS

## 10. Automated Model Tests

Tests in `tests/test_model.py` verify the model loads, outputs 10 classes, and gives a valid prediction and confidence.

```bash
pytest tests/test_model.py -v
```

Result:

```
tests/test_model.py::test_model_loads PASSED
tests/test_model.py::test_model_predicts_on_blank_input PASSED

2 passed
```

PASS — 2/2

## 11. Full MNIST Test Evaluation

```bash
python tests/evaluate_model.py
```

Result:

```
Test samples: 10000
Correct:      9907
Incorrect:    93
Accuracy:     99.07%
```

The model classified 9,907 / 10,000 images correctly.

PASS

## 12. Training Source Verification


```bash
grep -Rni --exclude-dir=.git --exclude-dir=.venv --exclude-dir=__pycache__ "torch.save" .
grep -Rni --exclude-dir=.git --exclude-dir=.venv --exclude-dir=__pycache__ "optimizer" .
git log --all --name-only --pretty=format: | sort -u
git log --oneline --all -- model/redmnist.pth
```

What was verified: the saved model matches `RedMnistNet`, loads fine, does real inference, passes tests, and hits 99.07% on the full test set.

## 13. Verification Checklist

Check............ Result

 Python environment --------PASS 
PyTorch installed----------PASS 
 Torchvision installed------PASS 
 RedMnistNet imports--------PASS 
Model architecture works---PASS 
 Input shape verified-------PASS 
 Forward pass works---------PASS 
`.pth` file exists---------PASS
 Checkpoint contains parameters---PASS 
 Checkpoint matches architecture--PASS 
 Saved model loads----------------PASS 
 Real MNIST image classified------PASS 
 Example `7 → 7`------------------PASS 
10-class output------------------PASS 
Automated tests----------- PASS — 2/2 
Full MNIST evaluation------PASS
Test images---------10,000 
Correct------9,907 
Incorrect-----93 
Accuracy-----99.07% 


## 14. Final Result

Task 2 verified the existing ML model and inference pipeline end-to-end.

Verified pipeline:

```
MNIST Image
   ↓ Grayscale
   ↓ Resize 32×32
   ↓ Tensor
   ↓ RedMnistNet
   ↓ 10-class output
   ↓ Predicted digit
```

Saved model `model/redmnist.pth` loaded and tested successfully. A real image gave `7 → 7`. Full test set gave 99.07% accuracy.

The only documentation gap is that the original training script was not found in the repo. I recorded that honestly instead of assuming training details.
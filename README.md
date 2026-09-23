# RedMnist

red team project for the Ethiopian AI challenge

## Layout

    api/          FastAPI app
    model/        network definition and weights
    frontend/     HTML page for manual testing
    tests/        smoke tests
    attacks/      adversarial example scripts
    report/       written report

## Run

pip install -r requirements.txt
 uvicorn api.app:app --reload

Server on http://127.0.0.1:8000.  to test by hand

Docker:

    docker build -t redmnist .
    docker run -p 8000:8000 redmnist

## Endpoints

GET  /health check
 POST /predict   image in, class and confidence out

## Tests

pytest tests/
Three smoke tests for the root endpoint,a valid image and a bad file

## Status

Serving side works, Docker builds and runs. Attacks and report are next
cd ~/Desktop/ai-red-team-assessment
source .venv/Scripts/activate

Optional environment check:
python --version
python -c "import torch, torchvision; print('torch', torch.__version__); print('torchvision', torchvision.__version__); print('cuda', torch.cuda.is_available())"

1. VERIFY THE MODEL
   ================

   PYTHONPATH=. python tests/load_check.py
   PYTHONPATH=. python tests/evaluate_model.py
2. FGSM ATTACK
   ===========

   PYTHONPATH=. python run_fgsm.py

Evidence:
results/original/digit_7.png
results/fgsm/digit_7_fgsm.png

Expected:
true digit 7
original prediction 7
adversarial prediction changes to a wrong class
success=True

3. PGD ATTACK
   ==========

   PYTHONPATH=. python run_pgd.py

Evidence:
results/original/digit_7.png
results/pgd/digit_7_pgd.png

Expected:
true digit 7
original prediction 7
adversarial prediction changes to a wrong class
success=True

NOTE:
PGD uses a randomized starting perturbation in the current experiment,
so the wrong class may vary. The security condition is misclassification.

4. SECURITY INSTRUMENTATION
   ========================

   FGSM and PGD are already instrumented.

PYTHONPATH=. python run_fgsm.py
PYTHONPATH=. python run_pgd.py

Security log:
logs/security_events.jsonl

View:
cat logs/security_events.jsonl

5. VULNERABLE API
   ==============

   Start:
   uvicorn vulnerable_api.app:app --host 127.0.0.1 --port 8001

Test from a second terminal:
curl http://127.0.0.1:8001/health
curl http://127.0.0.1:8001/model_info
curl http://127.0.0.1:8001/openapi.json

Swagger:
http://127.0.0.1:8001/docs

Stop:
Ctrl+C

6. HARDENED API
   ============

   Start:
   uvicorn api.app:app --host 127.0.0.1 --port 8000

Health:
curl http://127.0.0.1:8000/health

These should return 404:
curl -i http://127.0.0.1:8000/docs
curl -i http://127.0.0.1:8000/redoc
curl -i http://127.0.0.1:8000/openapi.json
curl -i http://127.0.0.1:8000/model_info

Stop:
Ctrl+C

7. FRONTEND
   ========

   Open:
   frontend/index.html

For VS Code Live Server:
Right-click frontend/index.html -> Open with Live Server

Normal API base:
http://127.0.0.1:8000

If Live Server uses:
http://127.0.0.1:5501
then the hardened API CORS configuration must explicitly allow that origin.

8. ADVERSARIAL TRAINING MITIGATION
   ===============================

   Run:
   PYTHONPATH=. python -m defenses.adversarial_training

Important:
CORRECT: python -m defenses.adversarial_training
WRONG:   python defenses/adversarial_training.py

Robust checkpoint:
model/redmnist_robust_v2.pth

Previously observed retest:
Original 7  -> 7, confidence about 0.9929
FGSM 7      -> 7, confidence about 0.2489
PGD 7       -> 7, confidence about 0.7599

This demonstrates resistance to the tested configurations on the selected sample,
not universal robustness.

9. BACKDOOR / DATA POISONING BONUS
   ===============================

   CORRECT:
   PYTHONPATH=. python experiments/backdoor/backdoor_demo.py

DO NOT use:
python -m experiments/backdoor/backdoor_demo.py

Expected successful result:
Clean digit 7      -> prediction=7
Triggered digit 7  -> prediction=3
Backdoor succeeded: 7 + trigger -> 3

Output:
experiments/backdoor/redmnist_backdoor_demo.pth

Evidence:
experiments/backdoor/results/clean_digit_7.png
experiments/backdoor/results/triggered_digit_7.png

Important:
This is a controlled bonus experiment on a separate experimental model.
The primary assessment checkpoint was not poisoned.

10. MEMBERSHIP INFERENCE BONUS
    ==========================

    CORRECT:
    PYTHONPATH=. python experiments/membership_inference/membership_inference.py

Previously observed illustrative result:
Mean member confidence      0.9358
Mean non-member confidence  0.9232
Mean member loss            0.1532
Mean non-member loss        0.1545
Confidence threshold         0.9295
Threshold attack accuracy    52.30%

Important:
Treat this as a weak / illustrative attempt, not a strong successful attack.

Results:
experiments/membership_inference/results.txt

11. MODEL TEST FILES
    ================

    PYTHONPATH=. python tests/test_model.py
    PYTHONPATH=. python tests/test_mitigation.py
12. DOCKER BUILD
    ============

    docker compose build

Clean rebuild:
docker compose build --no-cache

13. DOCKER START
    ============

    docker compose up -d

After code changes:
docker compose up -d --build

Check:
docker compose ps

Logs:
docker compose logs -f redmnist

Health:
http://127.0.0.1:8000/health

14. DOCKER STOP / CLEAN
    ===================

    Stop:
    docker compose stop

Start again:
docker compose start

Remove:
docker compose down

Clean demo rebuild:
docker compose down
docker compose build --no-cache
docker compose up -d

15. DOCKER SECURITY CHECK
    =====================

    docker ps
    docker compose ps
    docker exec redmnist-api whoami
    docker exec redmnist-api id

Expected hardened behavior:
non-root user
no-new-privileges
ALL capabilities dropped
read-only root filesystem
/tmp available as tmpfs

19. FULL LOCAL VERIFICATION SEQUENCE
    ================================

    cd ~/Desktop/ai-red-team-assessment
    source .venv/Scripts/activate

PYTHONPATH=. python tests/load_check.py
PYTHONPATH=. python tests/evaluate_model.py
PYTHONPATH=. python run_fgsm.py
PYTHONPATH=. python run_pgd.py
cat logs/security_events.jsonl
PYTHONPATH=. python experiments/backdoor/backdoor_demo.py
PYTHONPATH=. python experiments/membership_inference/membership_inference.py
PYTHONPATH=. python -m defenses.adversarial_training
docker compose up -d --build
docker compose ps
docker compose logs --tail=50 redmnist
git status --short

20. QUICK CHEAT SHEET
    =================

    ACTIVATE:
    source .venv/Scripts/activate

MODEL:
PYTHONPATH=. python tests/load_check.py
PYTHONPATH=. python tests/evaluate_model.py

FGSM:
PYTHONPATH=. python run_fgsm.py

PGD:
PYTHONPATH=. python run_pgd.py

BACKDOOR:
PYTHONPATH=. python experiments/backdoor/backdoor_demo.py

MEMBERSHIP:
PYTHONPATH=. python experiments/membership_inference/membership_inference.py

MITIGATION:
PYTHONPATH=. python -m defenses.adversarial_training

HARDENED API:
uvicorn api.app:app --host 127.0.0.1 --port 8000

VULNERABLE API:
uvicorn vulnerable_api.app:app --host 127.0.0.1 --port 8001

DOCKER:
docker compose build
docker compose up -d
docker compose ps
docker compose logs -f redmnist
docker compose down

GIT:
git status --short
git log origin/main..HEAD --oneline
git push origin main

run it from the repository root with:
PYTHONPATH=. python path/to/script.py

For "-m", use dotted module notation:
python -m package.module

python -m defenses.adversarial_training

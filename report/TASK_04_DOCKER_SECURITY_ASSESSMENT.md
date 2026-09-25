# Task 4 — Dockerization & Container Security Assessment

## 1. Objective

Containerize the AI model inference API with Docker, verify it works, and check the container's security config for unnecessary privileges.

## 2. Docker Configuration

Dockerfile:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api/ ./api/
COPY model/ ./model/
COPY frontend/ ./frontend/

EXPOSE 8000

CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

docker-compose.yml:

```yaml
services:
  redmnist:
    build: .
    image: redmnist:latest
    container_name: redmnist-api
    ports:
      - "8000:8000"
    volumes:
      - ./logs:/app/logs
```

## 3. Docker Environment Verification

```bash
docker version
```

Result: `Docker version 29.8.0, build 88096ef` — PASS

## 4. Docker Image Build

```bash
docker build -t redmnist:latest .
```

Result: `[+] Building 9.6s (13/13) FINISHED` — PASS

## 5. Docker Image Verification

```bash
docker images
```

Result:

```
IMAGE             ID             DISK USAGE   CONTENT SIZE
redmnist:latest   a8c617e11910       1.59GB          340MB
```

PASS

## 6. Container Command Verification

```bash
docker image inspect redmnist:latest --format '{{.Config.Cmd}}'
```

Result: `[uvicorn api.app:app --host 0.0.0.0 --port 8000]` — PASS

## 7. Containerized Prediction Test

```bash
curl -i -X POST "http://127.0.0.1:8000/predict" \
  -F "file=@sample_digits/digit_7.png"
```

Result:

```
HTTP/1.1 200 OK
{"predicted_class":7,"confidence":1.0,"latency_ms":8.1}
```

PASS

## 8. Container Stop Test

```bash
docker stop redmnist-api
docker ps
```

Result: no containers running. — PASS

## 9. Container Restart Test

```bash
docker start redmnist-api
docker ps
```

Result: container `redmnist-api` running, port `0.0.0.0:8000->8000/tcp`. — PASS

## 10. Prediction After Restart

```bash
curl -i -X POST "http://127.0.0.1:8000/predict" \
  -F "file=@sample_digits/digit_7.png"
```

Result:

```
HTTP/1.1 200 OK
{"predicted_class":7,"confidence":1.0,"latency_ms":3.36}
```

PASS

## 11. Functional Verification Summary

```
Build → Start → Upload Image → Inference → Predict 7 → Stop → Restart → Predict 7
```

PASS

## 12. Security Test — Container User

```bash
docker exec redmnist-api whoami
docker exec redmnist-api id
```

Result:

```
root
uid=0(root) gid=0(root) groups=0(root)
```

Finding: DOCKER-01 — Container Runs as Root — CONFIRMED, Severity: MEDIUM

### Impact

The API process runs as root inside the container. If the app or a dependency is compromised, the attacker gets root inside the container. Not a host escape by itself, but it violates least privilege and raises the impact of any app-level exploit.

### Recommendation

Create a non-root user in the Dockerfile and switch to it:

```dockerfile
RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /app

USER appuser
```

## 13. Security Test — Privileged Mode

```bash
docker inspect redmnist-api --format '{{json .HostConfig.Privileged}}'
```

Result: `false` — PASS, NOT PRIVILEGED

## 14. Security Test — Linux Capabilities

```bash
docker inspect redmnist-api --format '{{json .HostConfig.CapDrop}}'
docker inspect redmnist-api --format '{{json .HostConfig.CapAdd}}'
```

Result: `null` / `null` — HARDENING OPPORTUNITY 

Recommendation:

```yaml
cap_drop:
  - ALL
```

## 15. Security Test — Read-Only Root Filesystem

```bash
docker inspect redmnist-api --format '{{json .HostConfig.ReadonlyRootfs}}'
```

Result: `false` — HARDENING OPPORTUNITY

Recommendation:

```yaml
read_only: true
```

Logs already use a volume (`./logs:/app/logs`), so writable data can stay outside the root filesystem.

## 16. Findings Summary

 Test----- Result--------Finding 

 Container runs as root----CONFIRMED---DOCKER-01 (MEDIUM) 
 Privileged mode----PASS---Not privileged 
 Capability additions---PASS----None 
 Capability drops---HARDENING OPPORTUNITY----None configured 
 Read-only root filesystem---HARDENING OPPORTUNITY---Writable 

## 17. Recommended Hardened Configuration

Dockerfile:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY api/ ./api/
COPY model/ ./model/
COPY frontend/ ./frontend/

RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && mkdir -p /app/logs \
    && chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

docker-compose.yml:

```yaml
services:
  redmnist:
    build: .
    image: redmnist:latest
    container_name: redmnist-api
    ports:
      - "8000:8000"
    volumes:
      - ./logs:/app/logs
    read_only: true
    cap_drop:
      - ALL
    security_opt:
      - no-new-privileges:true
```

## 18. Retesting After Remediation

```bash
docker build -t redmnist:latest .
docker exec redmnist-api whoami   
docker exec redmnist-api id   
curl -i -X POST "http://127.0.0.1:8000/predict" \
  -F "file=@sample_digits/digit_7.png"  
```

## 19. Verification Checklist

Check  Result 
 Docker installed  PASS 
 Docker daemon available  PASS 
Docker image built  PASS 
 redmnist:latest exists  PASS 
 Container started  PASS 
 Prediction (class 7)  PASS 
 Container stopped  PASS 
 Container restarted  PASS 
 Prediction after restart  PASS 
 Container runs as root  CONFIRMED (DOCKER-01) 
Privileged mode PASS — false 
 Capability drops  RECOMMENDED 
 Read-only root filesystem  RECOMMENDED 
 Non-root user  RECOMMENDED 
 no-new-privileges |RECOMMENDED 

## 20. Final Result

The Dockerized inference API is functionally working build, run, predict, stop, restart, and predict again all passed.

One confirmed security weakness was found:

```
DOCKER-01 — Container Runs as Root (MEDIUM)
```

Evidence:

```
docker exec redmnist-api whoami → root
docker exec redmnist-api id     → uid=0(root) gid=0(root) groups=0(root)
```

Privileged mode was not enabled. Capability drops and read-only root filesystem were recorded as hardening opportunities, not confirmed exploits.

Conclusion:

```
Dockerized inference:        WORKING
Container root privilege:    CONFIRMED FINDING
Privileged mode:             NOT ENABLED
Capability hardening:        RECOMMENDED
Read-only filesystem:        RECOMMENDED
Non-root execution:          RECOMMENDED
```
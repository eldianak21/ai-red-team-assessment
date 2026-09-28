# import io
# import sys
# from pathlib import Path

# import requests
# from PIL import Image


# API = "http://127.0.0.1:8000"
# OUT = Path("results/pipeline_attacks")
# OUT.mkdir(parents=True, exist_ok=True)


# def post_predict(name: str, content: bytes, mime: str):
#     """Send one file to /predict and print the result."""
#     files = {"file": (name, content, mime)}
#     try:
#         r = requests.post(f"{API}/predict", files=files, timeout=10)
#         print(f"  HTTP {r.status_code}")
#         print(f"  Body: {r.text[:300]}")
#     except Exception as e:
#         print(f"  EXCEPTION: {type(e).__name__}: {e}")
#     print()


# def attack_1a_text_as_png():
#     print("=" * 60)
#     print("Attack 1a: plain text bytes declared as image/png")
#     print("=" * 60)
#     payload = b"This is not an image. It is plain text pretending to be one."
#     post_predict("fake.png", payload, "image/png")


# def attack_1b_empty_png():
#     print("=" * 60)
#     print("Attack 1b: empty file declared as image/png")
#     print("=" * 60)
#     post_predict("empty.png", b"", "image/png")


# def attack_1c_png_header_garbage():
#     print("=" * 60)
#     print("Attack 1c: valid PNG magic bytes + garbage")
#     print("=" * 60)
#     payload = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64 + b"garbage-garbage-garbage"
#     post_predict("corrupt.png", payload, "image/png")


# if __name__ == "__main__":
#     print(f"\nTarget: {API}\n")
#     attack_1a_text_as_png()
#     attack_1b_empty_png()
#     attack_1c_png_header_garbage()
#     print("Done. Check logs/predictions.log for the invalid_image events.")


import io
import sys
import time
from pathlib import Path

import requests
from PIL import Image


API = "http://127.0.0.1:8000"
OUT = Path("results/pipeline_attacks")
OUT.mkdir(parents=True, exist_ok=True)


def post_predict(name: str, content: bytes, mime: str):
    files = {"file": (name, content, mime)}
    try:
        r = requests.post(f"{API}/predict", files=files, timeout=60)
        print(f"  HTTP {r.status_code}")
        print(f"  Body: {r.text[:300]}")
    except Exception as e:
        print(f"  EXCEPTION: {type(e).__name__}: {e}")
    print()


def attack_1a_text_as_png():
    print("=" * 60)
    print("Attack 1a: plain text bytes declared as image/png")
    print("=" * 60)
    post_predict("fake.png", b"This is not an image. It is plain text pretending to be one.", "image/png")


def attack_1b_empty_png():
    print("=" * 60)
    print("Attack 1b: empty file declared as image/png")
    print("=" * 60)
    post_predict("empty.png", b"", "image/png")


def attack_1c_png_header_garbage():
    print("=" * 60)
    print("Attack 1c: valid PNG magic bytes + garbage")
    print("=" * 60)
    post_predict("corrupt.png", b"\x89PNG\r\n\x1a\n" + b"\x00" * 64 + b"garbage", "image/png")


def attack_2_oversized_upload():
    print("=" * 60)
    print("Attack 2: oversized junk upload (20 MB)")
    print("=" * 60)
    junk = b"J" * (20 * 1024 * 1024)
    print(f"  Payload size: {len(junk) / 1024 / 1024:.1f} MB")
    t0 = time.perf_counter()
    try:
        r = requests.post(f"{API}/predict",
                          files={"file": ("huge.png", junk, "image/png")},
                          timeout=60)
        dt = time.perf_counter() - t0
        print(f"  HTTP {r.status_code} after {dt:.2f}s")
        print(f"  Body: {r.text[:200]}")
    except Exception as e:
        dt = time.perf_counter() - t0
        print(f"  EXCEPTION after {dt:.2f}s: {type(e).__name__}: {e}")
    print()


def attack_3_filename_log_injection():
    print("=" * 60)
    print("Attack 3: filename log injection")
    print("=" * 60)
    fake = 'evil.png","level":"INFO","event":"predict.ok","predicted_class":9,"confidence":0.99'
    try:
        r = requests.post(f"{API}/predict",
                          files={"file": (fake, b"not an image", "image/png")},
                          timeout=10)
        print(f"  HTTP {r.status_code}")
        print(f"  Body: {r.text[:200]}")
    except Exception as e:
        print(f"  EXCEPTION: {type(e).__name__}: {e}")
    print()


def attack_4_bulk_query():
    print("=" * 60)
    print("Attack 4: unauthenticated bulk query (500 requests)")
    print("=" * 60)
    img = Image.new("L", (28, 28), color=0)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    payload = buf.getvalue()
    n, ok, fail = 500, 0, 0
    t0 = time.perf_counter()
    for i in range(n):
        try:
            r = requests.post(f"{API}/predict",
                              files={"file": (f"probe_{i}.png", payload, "image/png")},
                              timeout=10)
            ok += 1 if r.status_code == 200 else 0
            fail += 0 if r.status_code == 200 else 1
        except Exception:
            fail += 1
    dt = time.perf_counter() - t0
    print(f"  Sent: {n}")
    print(f"  OK:   {ok}")
    print(f"  Fail: {fail}")
    print(f"  Total time: {dt:.2f}s")
    print(f"  Rate: {n / dt:.1f} req/s")
    print(f"  -> No authentication was required.")
    print()


# if __name__ == "__main__":
#     print(f"\nTarget: {API}\n")
#     attack_3_filename_log_injection()


if __name__ == "__main__":
    print(f"\nTarget: {API}\n")
    attack_4_bulk_query()
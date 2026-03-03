# This is for the backend anime related endpoints, so theoretically this but not really :broken_heart:
import requests
import time
import random
import threading
from collections import defaultdict
from datetime import datetime
import os

BASE_URL    = "http://localhost:6969"
DURATION    = 10
WORKERS     = 10
INTERVAL    = 0.1
REPORT_FILE = f"reports/report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"

def load_csv(path):
    with open(path) as f:
        return [line.strip() for line in f if line.strip()]

ANIME_IDS    = load_csv("data/ids.csv")
STUDIO_IDS   = load_csv("data/studio_ids.csv")
PRODUCER_IDS = load_csv("data/producer_ids.csv")
LICENSOR_IDS = load_csv("data/licensor_ids.csv")
TAG_IDS      = load_csv("data/tag_ids.csv")

SEARCH_TERMS  = ["", "naruto", "one piece", "dragon", "sword", "attack"]
PAGES        = [0, 1, 2, 3]
PAGE_SIZES   = [10, 20, 50]
TYPE_IDS     = [1, 2, 3, 4, 5]
STATUS_IDS   = [1, 2, 3]

def search_url():
    params = [
        f"q={random.choice(SEARCH_TERMS)}",
        f"page={random.choice(PAGES)}",
        f"pageSize={random.choice(PAGE_SIZES)}",
    ]
    if random.random() < 0.3: params.append(f"type={random.choice(TYPE_IDS)}")
    if random.random() < 0.3: params.append(f"status={random.choice(STATUS_IDS)}")
    if random.random() < 0.2: params.append(f"min_episodes={random.randint(1, 12)}")
    if random.random() < 0.2: params.append(f"max_episodes={random.randint(13, 200)}")
    return f"{BASE_URL}/anime/search?{'&'.join(params)}"

def paginated(path, ids):
    return (f"{BASE_URL}{path}/{random.choice(ids)}"
            f"?page={random.choice(PAGES)}&pageSize={random.choice(PAGE_SIZES)}")

ENDPOINTS = [
    lambda: f"{BASE_URL}/anime/{random.choice(ANIME_IDS)}",
    lambda: f"{BASE_URL}/anime/random",
    search_url,
    lambda: f"{BASE_URL}/anime/seasonal?page={random.choice(PAGES)}&pageSize={random.choice(PAGE_SIZES)}",
    lambda: paginated("/anime/studio", STUDIO_IDS),
    lambda: paginated("/anime/producer", PRODUCER_IDS),
    lambda: paginated("/anime/licensor", LICENSOR_IDS),
    lambda: paginated("/anime/tags", TAG_IDS),
]

# thread local counters for eficiency
_all_states = []
stop_evt = threading.Event()

def worker() -> None:
    state = {"counts": defaultdict(int), "errors": defaultdict(int), "total": 0}
    _all_states.append(state)  # appended before the loop

    session = requests.Session()
    while not stop_evt.is_set():
        url  = random.choice(ENDPOINTS)()
        path = url.replace(BASE_URL, "").split("?")[0]
        try:
            r = session.get(url, timeout=5)
            is_err = r.status_code >= 500
        except Exception:
            is_err = True

        state["counts"][path] += 1
        state["total"] += 1
        if is_err:
            state["errors"][path] += 1

        time.sleep(INTERVAL)

threads = [threading.Thread(target=worker, daemon=True) for _ in range(WORKERS)]
start   = time.time()

print(f"Running {WORKERS} workers for {DURATION}s against {BASE_URL}\n")
for t in threads:
    t.start()

while time.time() - start < DURATION:
    elapsed       = time.time() - start
    running_total = sum(s["total"] for s in _all_states)
    print(f"\r  {elapsed:.0f}s / {DURATION}s  —  {running_total} requests", end="", flush=True)
    time.sleep(1)

stop_evt.set()
for t in threads:
    t.join()  # join only after all threads are done

elapsed = time.time() - start

counts = defaultdict(int)
errors = defaultdict(int)
total  = 0
for s in _all_states:
    for path, n in s["counts"].items(): counts[path] += n
    for path, n in s["errors"].items(): errors[path] += n
    total += s["total"]

total_errs = sum(errors.values())
rps        = total / elapsed

print(f"\n\n  {total} requests in {elapsed:.1f}s  |  {rps:.1f} req/s  |  {total_errs} errors ({total_errs / total * 100:.1f}%)")

W = 60
DIV = "-" * W

lines = [
    DIV,
    f"  STRESS TEST REPORT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
    f"  Target: {BASE_URL}   Workers: {WORKERS}   Duration: {elapsed:.1f}s",
    DIV,
    f"  {'ENDPOINT':<34} {'REQS':>6}  {'ERRS':>5}  {'ERR%':>5}",
    DIV,
]
for path in sorted(counts):
    r   = counts[path]
    e   = errors[path]
    pct = e / r * 100 if r else 0
    lines.append(f"  {path:<34} {r:>6}  {e:>5}  {pct:>4.1f}%")

lines += [
    DIV,
    f"  {'TOTAL':<34} {total:>6}  {total_errs:>5}  {total_errs / total * 100:.1f}%",
    f"  Throughput: {rps:.1f} req/s",
    DIV,
]

report = "\n".join(lines)
os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)
with open(REPORT_FILE, "w", encoding="utf-8") as f:
    f.write(report + "\n")

print(f"  Report file written: {REPORT_FILE}\n")
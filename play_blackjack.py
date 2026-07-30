import argparse
import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error

WDA_URL = "http://localhost:8100"
SCRIPT_DIR = os.path.dirname(__file__)
LAYOUT_FILE = os.path.join(SCRIPT_DIR, "iphone14_layout.json")
SEED_FILE = os.path.join(SCRIPT_DIR, "last_seed.txt")


def wda_request(method, endpoint, data=None, retries=3):
    url = f"{WDA_URL}{endpoint}"
    body = json.dumps(data).encode() if data else None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, data=body, method=method)
            req.add_header("Content-Type", "application/json")
            with urllib.request.urlopen(req, timeout=15) as resp:
                return json.loads(resp.read())
        except (urllib.error.HTTPError, urllib.error.URLError) as e:
            if attempt == retries - 1:
                raise
            time.sleep(1)


def wda_tap(x, y):
    payload = {"sequence": [{"x": x, "y": y, "duration": 0.05}]}
    wda_request("POST", "/wda/tapScreenPointSequence", payload)


def load_layout(path):
    with open(path) as f:
        return json.load(f)


def read_seed(path):
    with open(path) as f:
        record = json.load(f)
    return record["seed"]


def run_solver(seed, beam=200000, solver_path=None):
    if solver_path is None:
        solver_path = os.path.join(SCRIPT_DIR, "..", "bin", "triul-blackjack.dist", "triul-blackjack")
    cmd = [
        str(solver_path),
        "--seed", str(seed),
        "--beam", str(beam),
        "--json",
    ]
    print(f"Running solver: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print(f"Solver stderr: {result.stderr}")
        raise RuntimeError(f"Solver failed with exit code {result.returncode}")
    return json.loads(result.stdout)


def wait_for_seed_file(path, poll_interval=1.0, timeout=300):
    start = time.time()
    while time.time() - start < timeout:
        if os.path.exists(path):
            try:
                seed = read_seed(path)
                if seed is not None:
                    return seed
            except (json.JSONDecodeError, KeyError, ValueError):
                pass
        time.sleep(poll_interval)
    raise TimeoutError(f"No seed file found at {path} after {timeout}s")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, help="Seed value (skip mitmproxy wait)")
    parser.add_argument("--beam", type=int, default=200000, help="Beam width for solver")
    parser.add_argument("--solver", help="Path to triul-blackjack solver binary")
    parser.add_argument("--layout", default=LAYOUT_FILE, help="Layout JSON file")
    parser.add_argument("--wait", action="store_true", help="Wait for seed from mitmproxy")
    parser.add_argument("--delay", type=float, default=1.5, help="Delay between actions (seconds)")
    parser.add_argument("--dry-run", action="store_true", help="Print actions without tapping")
    args = parser.parse_args()

    if args.seed is not None:
        seed = args.seed
    elif args.wait:
        print(f"Waiting for seed file: {SEED_FILE}")
        seed = wait_for_seed_file(SEED_FILE)
        print(f"Seed captured: {seed}")
    else:
        parser.print_help()
        sys.exit(1)

    print(f"Solving for seed {seed}...")
    result = run_solver(seed, args.beam, args.solver)

    score = result.get("score", 0)
    actions = result.get("actions", [])
    print(f"Predicted score: {score}, Actions: {len(actions)}")

    if not actions:
        print("No actions returned by solver.")
        return

    if not args.dry_run:
        if not os.path.exists(args.layout):
            print(f"Layout file not found: {args.layout}")
            print("Run calibrate.py first to create it.")
            sys.exit(1)
        layout = load_layout(args.layout)
        columns = layout["columns"]
        stay_pos = layout["stay_button"]

    for step, act in enumerate(actions):
        action_type = act["action"]
        col = act["column"]
        event = act.get("event", "")
        card = act.get("card", "")

        print(f"  [{step+1}/{len(actions)}] {action_type} col={col} card={card} event={event}")

        if args.dry_run:
            print(f"    -> {'STAY' if action_type == 'stay' else f'Column {col}'}")
            continue

        if action_type == "stay":
            tx, ty = stay_pos
        elif action_type == "place":
            idx = col - 1
            tx, ty = columns[idx]
        else:
            print(f"    -> Unknown action, skipping")
            time.sleep(args.delay)
            continue

        print(f"    -> Tapping ({tx}, {ty})")
        wda_tap(tx, ty)
        time.sleep(args.delay)

    print("Done!")


if __name__ == "__main__":
    main()

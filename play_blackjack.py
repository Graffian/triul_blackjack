import argparse
import json
import os
import subprocess
import sys
import time
import wdautil

SCRIPT_DIR = os.path.dirname(__file__)
LAYOUT_FILE = os.path.join(SCRIPT_DIR, "iphone14_layout.json")
SEED_FILE = os.path.join(SCRIPT_DIR, "last_seed.txt")


def load_layout(path):
    with open(path) as f:
        return json.load(f)


def read_seed(path):
    with open(path) as f:
        record = json.load(f)
    return record["seed"]


def find_solver():
    candidates = [
        os.path.join(SCRIPT_DIR, "..", "bin", "triul-blackjack.dist", "triul-blackjack"),
        os.path.expanduser("~/Downloads/Triul-macos-arm64/bin/triul-blackjack.dist/triul-blackjack"),
        os.path.expanduser("~/Downloads/Triul-macos-arm64/Triul-macos-arm64/bin/triul-blackjack.dist/triul-blackjack"),
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return candidates[0]


def run_solver(seed, beam=200000, solver_path=None):
    if solver_path is None:
        solver_path = find_solver()
    cmd = [str(solver_path), "--seed", str(seed), "--beam", str(beam), "--json"]
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
        print("Connecting to WDA...")
        wdautil.start_session()
        layout = load_layout(args.layout)
        card_src = layout["card_source"]
        columns = layout["columns"]
        stay_btns = layout["stay_buttons"]

    for step, act in enumerate(actions):
        action_type = act["action"]
        col = act["column"]
        event = act.get("event", "")
        card = act.get("card", "")

        print(f"  [{step+1}/{len(actions)}] {action_type} col={col} card={card} event={event}")

        if args.dry_run:
            if action_type == "place":
                print(f"    -> DRAG card_source -> Column {col}")
            elif action_type == "stay":
                print(f"    -> TAP stay button col {col}")
            continue

        if action_type == "place":
            idx = col - 1
            tx, ty = columns[idx]
            print(f"    -> Dragging ({card_src[0]},{card_src[1]}) -> ({tx},{ty})")
            wdautil.drag(card_src[0], card_src[1], tx, ty)
        elif action_type == "stay":
            idx = col - 1
            tx, ty = stay_btns[idx]
            print(f"    -> Tapping stay col {col} at ({tx},{ty})")
            wdautil.tap(tx, ty)
        else:
            print(f"    -> Unknown action, skipping")
            time.sleep(args.delay)
            continue

        time.sleep(args.delay)

    print("Done!")


if __name__ == "__main__":
    main()

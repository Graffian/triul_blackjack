import json
import os
import time
import urllib.request
import urllib.error

WDA_URL = "http://localhost:8100"
LAYOUT_FILE = os.path.join(os.path.dirname(__file__), "iphone14_layout.json")


def wda_request(method, endpoint, data=None):
    url = f"{WDA_URL}{endpoint}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code}: {e.read().decode()}")
        raise
    except urllib.error.URLError as e:
        print(f"  Connection error: {e.reason}")
        raise


def get_screen_size():
    result = wda_request("GET", "/status")
    v = result.get("value", {})
    return v.get("screenWidth", 1170), v.get("screenHeight", 2532)


def take_screenshot():
    result = wda_request("POST", "/wda/screenshot")
    return result


def tap(x, y):
    payload = {"sequence": [{"x": x, "y": y, "duration": 0.05}]}
    wda_request("POST", "/wda/tapScreenPointSequence", payload)


def drag(from_x, from_y, to_x, to_y, duration=0.3):
    payload = {"fromX": from_x, "fromY": from_y, "toX": to_x, "toY": to_y, "duration": duration}
    wda_request("POST", "/wda/drag", payload)


def main():
    print("=== Triul Blackjack Calibration Tool ===")
    print(f"Connecting to WDA at {WDA_URL}...")
    try:
        sw, sh = get_screen_size()
        print(f"Screen: {sw}x{sh}")
    except Exception as e:
        print(f"Failed to connect to WDA: {e}")
        print("Make sure WDA is running at http://localhost:8100")
        return

    print("\nSave a screenshot to measure coordinates.")
    ans = input("Save screenshot? (y/n): ")
    if ans.lower() == "y":
        result = take_screenshot()
        if "value" in result:
            import base64
            img_data = base64.b64decode(result["value"])
            path = os.path.join(os.path.dirname(__file__), "calibration_screenshot.png")
            with open(path, "wb") as f:
                f.write(img_data)
            print(f"Screenshot saved to {path}")
            print("Open it in Preview to find pixel coordinates.")
        else:
            print("Screenshot failed")

    print("\n--- Enter Coordinates ---")
    print("Card source = where the face-up card appears (drag starts here)")
    print("Columns 0-3 = where you drop cards onto each column")
    print("Stay button = the stay button location (tap, not drag)")
    print()

    layout = {
        "screen_width": sw,
        "screen_height": sh,
        "card_source": [],
        "columns": [],
        "stay_button": [],
    }

    cx = int(input("Card source X: ").strip())
    cy = int(input("Card source Y: ").strip())
    layout["card_source"] = [cx, cy]

    for i in range(4):
        cx = int(input(f"Column {i} X (drop target center): ").strip())
        cy = int(input(f"Column {i} Y (drop target center): ").strip())
        layout["columns"].append([cx, cy])

    sx = int(input("Stay button X: ").strip())
    sy = int(input("Stay button Y: ").strip())
    layout["stay_button"] = [sx, sy]

    with open(LAYOUT_FILE, "w") as f:
        json.dump(layout, f, indent=2)
    print(f"\nLayout saved to {LAYOUT_FILE}")

    print("\n--- Test Mode ---")
    src = layout["card_source"]
    ans = input(f"Test drag from card source ({src[0]},{src[1]}) to Column 0? (y/n): ")
    if ans.lower() == "y":
        col = layout["columns"][0]
        print(f"  Dragging ({src[0]},{src[1]}) -> ({col[0]},{col[1]}) in 2s...")
        time.sleep(2)
        drag(src[0], src[1], col[0], col[1])
        print("  Done")

    ans = input(f"Test Stay button tap at ({sx},{sy})? (y/n): ")
    if ans.lower() == "y":
        print(f"  Tapping in 2s...")
        time.sleep(2)
        tap(sx, sy)
        print("  Done")

    print("\nCalibration complete!")


if __name__ == "__main__":
    main()

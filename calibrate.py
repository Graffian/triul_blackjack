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
    return result.get("value", {}).get("screenWidth", 1170), result.get("value", {}).get("screenHeight", 2532)


def take_screenshot():
    result = wda_request("POST", "/wda/screenshot")
    return result


def tap(x, y):
    payload = {"sequence": [{"x": x, "y": y, "duration": 0.05}]}
    wda_request("POST", "/wda/tapScreenPointSequence", payload)


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

    print("\nOption 1: Save a screenshot for visual reference")
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
            print("Open it in Preview/Photoshop to find pixel coordinates.")
        else:
            print("Screenshot failed")

    print("\nOption 2: Enter coordinates directly")
    print("Open the screenshot and find the center of each column.")
    print()

    layout = {"screen_width": sw, "screen_height": sh, "columns": [], "stay_button": []}

    for i in range(4):
        cx = int(input(f"Column {i} X coordinate (center): ").strip())
        cy = int(input(f"Column {i} Y coordinate (center): ").strip())
        layout["columns"].append([cx, cy])

    sx = int(input("Stay button X coordinate: ").strip())
    sy = int(input("Stay button Y coordinate: ").strip())
    layout["stay_button"] = [sx, sy]

    with open(LAYOUT_FILE, "w") as f:
        json.dump(layout, f, indent=2)
    print(f"\nLayout saved to {LAYOUT_FILE}")

    print("\n--- Test Mode ---")
    for i, (x, y) in enumerate(layout["columns"]):
        ans = input(f"Test Column {i} at ({x},{y})? (y/n): ")
        if ans.lower() == "y":
            print(f"  Tapping ({x},{y}) in 2 seconds...")
            time.sleep(2)
            tap(x, y)
            print("  Done")

    ans = input(f"Test Stay button at ({layout['stay_button'][0]},{layout['stay_button'][1]})? (y/n): ")
    if ans.lower() == "y":
        print(f"  Tapping in 2 seconds...")
        time.sleep(2)
        tap(layout['stay_button'][0], layout['stay_button'][1])
        print("  Done")

    print("\nCalibration complete!")


if __name__ == "__main__":
    main()

import os
import time
import base64
import wdautil

LAYOUT_FILE = os.path.join(os.path.dirname(__file__), "iphone14_layout.json")


def main():
    print("=== Triul Blackjack Calibration Tool ===")
    print("Connecting to WDA...")
    sw, sh = 428, 926
    try:
        wdautil.start_session()
        sw, sh = wdautil.screen_size()
        print(f"Screen: {sw}x{sh}")
    except Exception as e:
        print(f"WDA connection optional: {e}")
        print("Will use manual coordinate entry.\n")

    print("Save a screenshot to measure coordinates.")
    ans = input("Save screenshot? (y/n): ")
    if ans.lower() == "y":
        try:
            img_b64 = wdautil.screenshot()
            if img_b64:
                img_data = base64.b64decode(img_b64)
                path = os.path.join(os.path.dirname(__file__), "calibration_screenshot.png")
                with open(path, "wb") as f:
                    f.write(img_data)
                print(f"Screenshot saved to {path}")
        except Exception as e:
            print(f"Screenshot unavailable: {e}")
            print("Enter coordinates manually instead.")

    print("\n--- Enter Coordinates (WDA logical points) ---")
    print("1) Card source — center of the face-up card")
    print("2) Columns 0-3 — drop target center for each column")
    print("3) Stay buttons 0-3 — each column's stay button")
    print()

    layout = {}
    cx = int(input("Card source X: ").strip())
    cy = int(input("Card source Y: ").strip())
    layout["card_source"] = [cx, cy]

    cols = []
    for i in range(4):
        cx = int(input(f"Column {i} X: ").strip())
        cy = int(input(f"Column {i} Y: ").strip())
        cols.append([cx, cy])
    layout["columns"] = cols

    stays = []
    for i in range(4):
        sx = int(input(f"Stay button {i} X: ").strip())
        sy = int(input(f"Stay button {i} Y: ").strip())
        stays.append([sx, sy])
    layout["stay_buttons"] = stays

    import json
    with open(LAYOUT_FILE, "w") as f:
        json.dump(layout, f, indent=2)
    print(f"\nLayout saved to {LAYOUT_FILE}")

    print("\n--- Test Mode ---")
    src = layout["card_source"]
    ans = input(f"Test drag from ({src[0]},{src[1]}) to Column 0? (y/n): ")
    if ans.lower() == "y":
        col = layout["columns"][0]
        print(f"  Dragging in 2s...")
        time.sleep(2)
        wdautil.drag(src[0], src[1], col[0], col[1])
        print("  Done")

    for i in range(4):
        ans = input(f"Test Stay button {i} at {layout['stay_buttons'][i]}? (y/n): ")
        if ans.lower() == "y":
            print(f"  Tapping in 2s...")
            time.sleep(2)
            wdautil.tap(*layout['stay_buttons'][i])
            print("  Done")

    print("\nCalibration complete!")


if __name__ == "__main__":
    main()

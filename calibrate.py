import os
import time
import base64
import wdautil

LAYOUT_FILE = os.path.join(os.path.dirname(__file__), "iphone14_layout.json")


def main():
    print("=== Triul Blackjack Calibration Tool ===")
    print("Connecting to WDA...")
    try:
        wdautil.start_session()
        sw, sh = wdautil.screen_size()
        print(f"Screen: {sw}x{sh}")
    except Exception as e:
        print(f"Failed to connect to WDA: {e}")
        return

    print("\nSave a screenshot to measure coordinates.")
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
                print("Open it in Preview to find pixel coordinates.")
            else:
                print("Screenshot failed")
        except Exception as e:
            print(f"Screenshot failed: {e}")

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
        import json
        json.dump(layout, f, indent=2)
    print(f"\nLayout saved to {LAYOUT_FILE}")

    print("\n--- Test Mode ---")
    src = layout["card_source"]
    ans = input(f"Test drag from card source ({src[0]},{src[1]}) to Column 0? (y/n): ")
    if ans.lower() == "y":
        col = layout["columns"][0]
        print(f"  Dragging ({src[0]},{src[1]}) -> ({col[0]},{col[1]}) in 2s...")
        time.sleep(2)
        wdautil.drag(src[0], src[1], col[0], col[1])
        print("  Done")

    ans = input(f"Test Stay button tap at ({sx},{sy})? (y/n): ")
    if ans.lower() == "y":
        print(f"  Tapping in 2s...")
        time.sleep(2)
        wdautil.tap(sx, sy)
        print("  Done")

    print("\nCalibration complete!")


if __name__ == "__main__":
    main()

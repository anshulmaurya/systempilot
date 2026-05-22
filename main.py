from mss import MSS
from PIL import Image

from config import SCREENSHOT_DIR, MATCH_CROP_DIR, TARGET_TEXT
from utils import clear_folder, notify_click
from mouse import quartz_click
from ocr import run_vision_ocr
from text_matcher import find_text_matches, save_text_match_crops, ask_user_to_choose_match
from icon_finder import save_icons_only_image, ask_user_for_pixel_click
from debug import save_click_debug_image, save_ocr_debug_image


def main():
    clear_folder(MATCH_CROP_DIR)

    all_text_matches = []

    with MSS() as sct:
        monitors_data = []

        for monitor_index, monitor in enumerate(sct.monitors[1:], start=1):
            print(f"\nChecking monitor {monitor_index}: {monitor}")

            screenshot = sct.grab(monitor)
            img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)

            # Retina/HiDPI: mss returns physical pixels; Quartz uses logical points.
            scale_x = img.width / monitor["width"]
            scale_y = img.height / monitor["height"]

            print(f"Monitor scale: {scale_x:.2f}x, {scale_y:.2f}y")

            raw_path = SCREENSHOT_DIR / f"monitor_{monitor_index}.png"
            img.save(raw_path)
            print(f"Saved screenshot: {raw_path}")

            ocr_items = run_vision_ocr(img)
            print(f"Detected {len(ocr_items)} OCR text items")

            save_ocr_debug_image(img, monitor_index, ocr_items)

            matches = find_text_matches(ocr_items, TARGET_TEXT)

            monitors_data.append({
                "monitor_index": monitor_index,
                "monitor": monitor,
                "img": img,
                "ocr_items": ocr_items,
                "matches": matches,
                "scale_x": scale_x,
                "scale_y": scale_y,
            })

            if matches:
                saved_matches = save_text_match_crops(img, monitor_index, matches)

                for saved in saved_matches:
                    saved.update({
                        "monitor": monitor,
                        "monitor_index": monitor_index,
                        "img": img,
                        "scale_x": scale_x,
                        "scale_y": scale_y,
                    })

                all_text_matches.extend(saved_matches)

    # ----------------------------
    # CASE 1: TEXT FOUND
    # ----------------------------

    if all_text_matches:
        chosen = (
            all_text_matches[0]
            if len(all_text_matches) == 1
            else ask_user_to_choose_match(all_text_matches)
        )

        match = chosen["match"]
        monitor = chosen["monitor"]
        monitor_index = chosen["monitor_index"]
        img = chosen["img"]
        scale_x = chosen["scale_x"]
        scale_y = chosen["scale_y"]

        local_x = match["center_x"]
        local_y = match["center_y"]
        absolute_x = monitor["left"] + local_x / scale_x
        absolute_y = monitor["top"] + local_y / scale_y

        print(f"\nText match: '{match['text']}'")
        print(f"Click local (px): {local_x:.1f}, {local_y:.1f}")
        print(f"Click global (pt): {absolute_x:.1f}, {absolute_y:.1f}")

        save_click_debug_image(img, monitor_index, local_x, local_y, label=f"clicked: {match['text']}")
        notify_click(match["text"], absolute_x, absolute_y)
        quartz_click(absolute_x, absolute_y)
        return

    # ----------------------------
    # CASE 2: NO MATCHING TEXT FOUND
    # ----------------------------

    print("\nNo matching text found on any monitor.")
    print("Generating icons-only images...")

    icons_data = []
    for data in monitors_data:
        icons_path = save_icons_only_image(
            data["img"],
            data["monitor_index"],
            data["ocr_items"],
        )
        icons_data.append({**data, "icons_only_path": icons_path})

    # If multiple monitors, ask which one to click on
    if len(icons_data) == 1:
        chosen_data = icons_data[0]
    else:
        print("\nMultiple monitors detected. Choose which one to click on:")
        for i, d in enumerate(icons_data, start=1):
            print(f"{i}. Monitor {d['monitor_index']}: {d['icons_only_path']}")
        while True:
            choice = input("\nEnter monitor number: ").strip()
            if choice.isdigit() and 1 <= int(choice) <= len(icons_data):
                chosen_data = icons_data[int(choice) - 1]
                break
            print("Invalid choice. Try again.")

    pixel_x, pixel_y = ask_user_for_pixel_click(
        chosen_data["icons_only_path"],
        chosen_data["img"].width,
        chosen_data["img"].height,
    )

    monitor = chosen_data["monitor"]
    img = chosen_data["img"]
    monitor_index = chosen_data["monitor_index"]
    scale_x = chosen_data["scale_x"]
    scale_y = chosen_data["scale_y"]

    absolute_x = monitor["left"] + pixel_x / scale_x
    absolute_y = monitor["top"] + pixel_y / scale_y

    print(f"\nIcon click at pixel: {pixel_x:.1f}, {pixel_y:.1f}")
    print(f"Global click (pt): {absolute_x:.1f}, {absolute_y:.1f}")

    save_click_debug_image(img, monitor_index, pixel_x, pixel_y, label="icon click")
    notify_click("icon target", absolute_x, absolute_y)
    quartz_click(absolute_x, absolute_y)


if __name__ == "__main__":
    main()

from config import (
    ICON_CROP_DIR,
    GRID_ROWS,
    GRID_COLS,
    MIN_ICON_CROP_WIDTH,
    MIN_ICON_CROP_HEIGHT,
)
from utils import parse_relative_xy


def rects_intersect(a, b):
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    return not (ax2 <= bx1 or ax1 >= bx2 or ay2 <= by1 or ay1 >= by2)


def save_no_text_grid_candidates(img, monitor_index, ocr_items):
    """
    Split the screen into a grid and save regions that do not overlap
    any OCR text as potential icon/visual-choice candidates.
    """
    img_width, img_height = img.size

    text_rects = [
        (item["x"], item["y"], item["x"] + item["w"], item["y"] + item["h"])
        for item in ocr_items
    ]

    cell_w = img_width / GRID_COLS
    cell_h = img_height / GRID_ROWS

    saved = []
    candidate_index = 1

    for row in range(GRID_ROWS):
        for col in range(GRID_COLS):
            left = int(col * cell_w)
            top = int(row * cell_h)
            right = int((col + 1) * cell_w)
            bottom = int((row + 1) * cell_h)

            w = right - left
            h = bottom - top

            if w < MIN_ICON_CROP_WIDTH or h < MIN_ICON_CROP_HEIGHT:
                continue

            cell_rect = (left, top, right, bottom)

            if any(rects_intersect(cell_rect, tr) for tr in text_rects):
                continue

            crop = img.crop((left, top, right, bottom))
            crop_path = ICON_CROP_DIR / f"monitor_{monitor_index}_candidate_{candidate_index}.png"
            crop.save(crop_path)

            saved.append({
                "path": crop_path,
                "monitor_index": monitor_index,
                "crop_left": left,
                "crop_top": top,
                "crop_right": right,
                "crop_bottom": bottom,
                "crop_width": w,
                "crop_height": h,
            })

            candidate_index += 1

    return saved


def ask_user_to_choose_icon_candidate(saved_candidates):
    print("\nNo matching text found.")
    print("Saved non-text candidate regions.")
    print("Open these images and choose the most relevant one:\n")

    for i, item in enumerate(saved_candidates, start=1):
        print(
            f"{i}. {item['path']} "
            f"| size={item['crop_width']}x{item['crop_height']}"
        )

    while True:
        choice = input("\nEnter candidate number: ").strip()

        if choice.isdigit():
            index = int(choice)
            if 1 <= index <= len(saved_candidates):
                return saved_candidates[index - 1]

        print("Invalid choice. Try again.")


def ask_user_for_relative_click(candidate):
    print("\nNow enter the click coordinate inside the chosen crop.")
    print("Use relative crop coordinates.")
    print("Example: 120, 45 means x=120 px from left, y=45 px from top.")
    print(f"Crop size: {candidate['crop_width']} x {candidate['crop_height']}")

    while True:
        value = input("\nEnter relative x,y: ").strip()

        try:
            rel_x, rel_y = parse_relative_xy(value)

            if 0 <= rel_x <= candidate["crop_width"] and 0 <= rel_y <= candidate["crop_height"]:
                return rel_x, rel_y

            print("Coordinates are outside the crop. Try again.")

        except ValueError as e:
            print(e)

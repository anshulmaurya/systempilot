from PIL import ImageDraw

from config import MATCH_CROP_DIR, TEXT_CROP_PADDING
from utils import safe_crop_box


def find_text_matches(ocr_items, target_text):
    return [
        item for item in ocr_items
        if target_text.lower() in item["text"].lower()
    ]


def save_text_match_crops(img, monitor_index, matches):
    img_width, img_height = img.size
    saved = []

    for index, match in enumerate(matches, start=1):
        left, top, right, bottom = safe_crop_box(
            match["x"],
            match["y"],
            match["w"],
            match["h"],
            img_width,
            img_height,
            padding=TEXT_CROP_PADDING,
        )

        crop = img.crop((left, top, right, bottom))
        draw = ImageDraw.Draw(crop)

        # Draw box around actual text relative to crop
        rel_x = match["x"] - left
        rel_y = match["y"] - top
        rel_w = match["w"]
        rel_h = match["h"]

        draw.rectangle(
            [rel_x, rel_y, rel_x + rel_w, rel_y + rel_h],
            outline="red",
            width=4,
        )

        crop_path = MATCH_CROP_DIR / f"monitor_{monitor_index}_match_{index}.png"
        crop.save(crop_path)

        saved.append({
            "path": crop_path,
            "match": match,
            "crop_left": left,
            "crop_top": top,
            "crop_right": right,
            "crop_bottom": bottom,
        })

    return saved


def ask_user_to_choose_match(saved_matches):
    print("\nMultiple text matches found.")
    print("Open these images and choose which one to click:\n")

    for i, item in enumerate(saved_matches, start=1):
        print(f"{i}. {item['path']} | text={item['match']['text']}")

    while True:
        choice = input("\nEnter match number to click: ").strip()

        if choice.isdigit():
            index = int(choice)
            if 1 <= index <= len(saved_matches):
                return saved_matches[index - 1]

        print("Invalid choice. Try again.")

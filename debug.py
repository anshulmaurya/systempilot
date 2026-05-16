from PIL import ImageDraw

from config import SCREENSHOT_DIR
from utils import draw_cross


def save_click_debug_image(img, monitor_index, local_x, local_y, label="click"):
    debug_img = img.copy()
    draw = ImageDraw.Draw(debug_img)

    draw_cross(draw, local_x, local_y, color="blue", size=24, width=5)
    draw.text((local_x + 12, local_y + 12), label, fill="blue")

    debug_path = SCREENSHOT_DIR / f"clicked_monitor_{monitor_index}.png"
    debug_img.save(debug_path)

    print(f"Saved click debug image: {debug_path}")
    return debug_path


def save_ocr_debug_image(img, monitor_index, ocr_items):
    debug_img = img.copy()
    draw = ImageDraw.Draw(debug_img)

    for item in ocr_items:
        x, y, w, h = item["x"], item["y"], item["w"], item["h"]

        draw.rectangle([x, y, x + w, y + h], outline="red", width=3)
        draw.text((x, max(0, y - 14)), item["text"], fill="red")

    debug_path = SCREENSHOT_DIR / f"ocr_debug_monitor_{monitor_index}.png"
    debug_img.save(debug_path)

    print(f"Saved OCR debug image: {debug_path}")
    return debug_path

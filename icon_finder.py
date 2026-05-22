from PIL import ImageDraw

from config import SCREENSHOT_DIR
from utils import parse_relative_xy


def save_icons_only_image(img, monitor_index, ocr_items):
    """
    Produces a copy of the screenshot with every OCR text bounding box
    painted over in solid gray, leaving only non-text content (icons,
    images, UI elements) visible.
    """
    masked = img.copy()
    draw = ImageDraw.Draw(masked)

    for item in ocr_items:
        x, y, w, h = item["x"], item["y"], item["w"], item["h"]
        draw.rectangle([x, y, x + w, y + h], fill=(180, 180, 180))

    out_path = SCREENSHOT_DIR / f"icons_only_monitor_{monitor_index}.png"
    masked.save(out_path)
    print(f"Saved icons-only image: {out_path}")
    return out_path


def ask_user_for_pixel_click(icon_image_path, img_width, img_height):
    """
    Shows the path to the icons-only image and prompts the user to enter
    the pixel coordinate of the icon they want to click.
    """
    print(f"\nOpen this image and find the icon you want to click:")
    print(f"  {icon_image_path}")
    print(f"Image size: {img_width} x {img_height} px")
    print("Enter the pixel x,y coordinate of the icon.")

    while True:
        value = input("\nEnter x,y (pixels): ").strip()
        try:
            px, py = parse_relative_xy(value)
            if 0 <= px <= img_width and 0 <= py <= img_height:
                return px, py
            print(f"Coordinates must be within 0-{img_width}, 0-{img_height}. Try again.")
        except ValueError as e:
            print(e)

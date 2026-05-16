import os
import re
from io import BytesIO
from pathlib import Path

from Foundation import NSData


def clear_folder(folder: Path):
    folder.mkdir(exist_ok=True)
    for file in folder.glob("*"):
        if file.is_file():
            file.unlink()


def notify_click(text, x, y):
    safe_text = str(text).replace('"', "'")
    os.system(
        f'''osascript -e 'display notification "Clicking {safe_text} at {int(x)}, {int(y)}" with title "OCR Click"' '''
    )


def image_to_nsdata(img):
    buffer = BytesIO()
    img.save(buffer, format="PNG")
    image_data = buffer.getvalue()
    return NSData.dataWithBytes_length_(image_data, len(image_data))


def draw_cross(draw, x, y, color="blue", size=18, width=5):
    draw.line([x - size, y, x + size, y], fill=color, width=width)
    draw.line([x, y - size, x, y + size], fill=color, width=width)


def safe_crop_box(x, y, w, h, img_width, img_height, padding=0):
    left = max(0, int(x - padding))
    top = max(0, int(y - padding))
    right = min(img_width, int(x + w + padding))
    bottom = min(img_height, int(y + h + padding))
    return left, top, right, bottom


def parse_relative_xy(value):
    """
    Accepts:
      100,200
      100 200
      x=100 y=200
    """
    nums = re.findall(r"-?\d+(?:\.\d+)?", value)
    if len(nums) < 2:
        raise ValueError("Please enter two numbers, like: 120, 45")
    return float(nums[0]), float(nums[1])

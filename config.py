from pathlib import Path

# ----------------------------
# CONFIG
# ----------------------------

TARGET_TEXT = "xxx"

MOVE_DURATION = 1.0
CLICK_PAUSE = 0.4

SCREENSHOT_DIR = Path("screenshots")
MATCH_CROP_DIR = SCREENSHOT_DIR / "text_matches"
ICON_CROP_DIR = SCREENSHOT_DIR / "icon_candidates"

SCREENSHOT_DIR.mkdir(exist_ok=True)
MATCH_CROP_DIR.mkdir(exist_ok=True)
ICON_CROP_DIR.mkdir(exist_ok=True)

# Icon/no-text candidate settings
N = 4
GRID_ROWS = 3
GRID_COLS = 3
MIN_ICON_CROP_WIDTH = 80 * N
MIN_ICON_CROP_HEIGHT = 80 * N

# Padding around text crops
TEXT_CROP_PADDING = 20 * N

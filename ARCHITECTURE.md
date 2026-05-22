# Architecture — cua-mcp

## Purpose

**cua-mcp** is a macOS desktop automation tool that:
1. Takes a screenshot of every connected monitor.
2. Runs Apple Vision OCR to find all visible text.
3. Searches for a configured target string in the detected text.
4. Either clicks the matching text automatically, or — when no text match is found — lets the user visually pick an icon/region and click it manually.

---

## Module Map

```
cua-mcp/
├── config.py        — constants & directory setup
├── utils.py         — shared low-level helpers
├── mouse.py         — Quartz mouse movement & click
├── ocr.py           — Apple Vision OCR
├── text_matcher.py  — text search, crop saving, user selection
├── icon_finder.py   — grid-based icon candidate logic
├── debug.py         — annotated debug image output
└── main.py          — entry point & orchestration
```

---

## Execution Flow

```
main()
  │
  ├─ 1. SETUP
  │     clear_folder(MATCH_CROP_DIR)       # wipe previous text match crops
  │     clear_folder(ICON_CROP_DIR)        # wipe previous icon crops
  │
  ├─ 2. PER-MONITOR LOOP  (mss → all physical monitors)
  │     │
  │     ├─ capture screenshot              (mss.grab)
  │     ├─ convert to PIL Image            (Image.frombytes)
  │     ├─ compute Retina scale            (img.width / monitor["width"])
  │     ├─ save raw screenshot             (screenshots/monitor_N.png)
  │     ├─ run OCR                         (ocr.run_vision_ocr)
  │     ├─ save OCR debug overlay          (debug.save_ocr_debug_image)
  │     └─ search for TARGET_TEXT          (text_matcher.find_text_matches)
  │           → accumulate matches + monitor metadata
  │
  ├─ 3a. CASE: TEXT FOUND
  │     │
  │     ├─ 1 match  → auto-select
  │     ├─ N matches → save padded crops + ask user to choose (stdin)
  │     │
  │     ├─ convert pixel coords → logical points
  │     │     absolute_x = monitor["left"] + center_x / scale_x
  │     │     absolute_y = monitor["top"]  + center_y / scale_y
  │     │
  │     ├─ save click debug overlay        (debug.save_click_debug_image)
  │     ├─ send macOS notification         (utils.notify_click via osascript)
  │     └─ perform click                   (mouse.quartz_click)
  │
  └─ 3b. CASE: NO TEXT MATCH
        │
        ├─ split each monitor into a 3×3 grid
        ├─ discard any grid cell that overlaps OCR text
        ├─ save remaining cells as icon candidates
        │
        ├─ ask user to choose a candidate  (stdin)
        ├─ ask user for relative x,y within that crop (stdin)
        │
        ├─ convert crop-relative → monitor-local → global logical points
        ├─ save click debug overlay
        ├─ send macOS notification
        └─ perform click
```

---

## Module Details

### `config.py`
Pure constants. Imported by every other module that needs paths or tuning values.

| Constant | Value | Purpose |
|---|---|---|
| `TARGET_TEXT` | `"xbxbxbx"` | Text to search for on screen |
| `MOVE_DURATION` | `1.0 s` | Total time to animate mouse movement |
| `CLICK_PAUSE` | `0.4 s` | Pause after arriving before clicking |
| `N` | `4` | Resolution scale multiplier for crop sizes |
| `GRID_ROWS / GRID_COLS` | `3 / 3` | Grid divisions for icon candidate search |
| `MIN_ICON_CROP_WIDTH/HEIGHT` | `320 / 320 px` | Minimum cell size to be a valid candidate |
| `TEXT_CROP_PADDING` | `80 px` | Extra pixels around text bounding boxes |
| `SCREENSHOT_DIR` | `screenshots/` | Root output folder |
| `MATCH_CROP_DIR` | `screenshots/text_matches/` | Text match crops |
| `ICON_CROP_DIR` | `screenshots/icon_candidates/` | Icon candidate crops |

---

### `utils.py`
Shared helpers with no business logic.

| Function | Description |
|---|---|
| `clear_folder(folder)` | Deletes all files in a folder (creates it first if missing) |
| `notify_click(text, x, y)` | Sends a macOS banner notification via `osascript` |
| `image_to_nsdata(img)` | Converts a PIL Image → `NSData` (required by Vision framework) |
| `draw_cross(draw, x, y, ...)` | Draws a ± crosshair on a PIL `ImageDraw` canvas |
| `safe_crop_box(x, y, w, h, ...)` | Clamps a bounding box + padding to image boundaries |
| `parse_relative_xy(value)` | Parses freeform text like `"120, 45"` or `"x=120 y=45"` into `(float, float)` |

---

### `mouse.py`
macOS-native mouse control via the `Quartz` Core Graphics framework. Does **not** use any accessibility APIs — it synthesises raw HID events.

| Function | Description |
|---|---|
| `quartz_move(x, y)` | Posts a single `kCGEventMouseMoved` event at logical point `(x, y)` |
| `quartz_click(x, y)` | Animates the cursor from its current position to `(x, y)` in 40 steps, performs a brief wiggle, then fires `MouseDown` + `MouseUp` |

**Coordinate space:** logical points (not physical pixels). The caller is responsible for converting pixel coords from screenshots using the per-monitor Retina scale factor.

---

### `ocr.py`
Wraps Apple's `Vision.VNRecognizeTextRequest`.

**`run_vision_ocr(img) → list[dict]`**

1. Converts the PIL image to `NSData`.
2. Creates a `VNRecognizeTextRequest` at `Accurate` level with language correction enabled.
3. Runs it synchronously via `VNImageRequestHandler`.
4. Iterates over `VNRecognizedTextObservation` results.
5. Converts Vision's normalized bottom-left bounding boxes to pixel-space top-left coordinates.

Each returned dict contains: `text`, `x`, `y`, `w`, `h`, `center_x`, `center_y`.

**Coordinate conversion:**
```
box_x =  bbox.origin.x                       * img_width
box_y = (1 - bbox.origin.y - bbox.height)    * img_height   # flip Y axis
```

---

### `text_matcher.py`
Handles the "text found" path.

| Function | Description |
|---|---|
| `find_text_matches(ocr_items, target_text)` | Case-insensitive substring search over all OCR items |
| `save_text_match_crops(img, monitor_index, matches)` | Crops each match from the screenshot with padding, draws a red bounding box, saves to `MATCH_CROP_DIR` |
| `ask_user_to_choose_match(saved_matches)` | Prints paths + text to stdout, reads a number from stdin, returns the chosen match dict |

---

### `icon_finder.py`
Handles the "no text found" path.

| Function | Description |
|---|---|
| `rects_intersect(a, b)` | AABB intersection test between two `(x1,y1,x2,y2)` rectangles |
| `save_no_text_grid_candidates(img, monitor_index, ocr_items)` | Splits image into a `GRID_ROWS × GRID_COLS` grid, discards cells that overlap any OCR bounding box, saves the rest as candidate crops |
| `ask_user_to_choose_icon_candidate(saved_candidates)` | Stdin selection from saved candidate list |
| `ask_user_for_relative_click(candidate)` | Prompts user for an `x,y` coordinate relative to the chosen crop, validates it is inside the crop bounds |

---

### `debug.py`
Writes annotated images for visual inspection. Never affects program flow.

| Function | Output file | Content |
|---|---|---|
| `save_ocr_debug_image(img, monitor_index, ocr_items)` | `screenshots/ocr_debug_monitor_N.png` | Red rectangles + labels over every OCR-detected text region |
| `save_click_debug_image(img, monitor_index, x, y, label)` | `screenshots/clicked_monitor_N.png` | Blue crosshair + label at the click point |

---

## Coordinate System & Retina Scaling

macOS has two coordinate spaces in play:

| Space | Unit | Used by |
|---|---|---|
| Physical pixels | px | `mss` screenshots, PIL images, Vision OCR results |
| Logical points | pt | `monitor["left/top/width/height"]`, Quartz mouse events |

On Retina displays the scale factor is typically `2.0`. The per-monitor ratio is computed as:
```python
scale_x = img.width  / monitor["width"]   # e.g. 2.0
scale_y = img.height / monitor["height"]  # e.g. 2.0
```

Global click position:
```python
absolute_x = monitor["left"] + pixel_x / scale_x
absolute_y = monitor["top"]  + pixel_y / scale_y
```

---

## Output File Structure

```
screenshots/
├── monitor_1.png                        # raw capture
├── ocr_debug_monitor_1.png              # all OCR boxes overlaid
├── clicked_monitor_1.png                # crosshair at chosen click point
├── text_matches/
│   ├── monitor_1_match_1.png            # padded crop with red box around text
│   └── monitor_1_match_2.png
└── icon_candidates/
    ├── monitor_1_candidate_1.png        # grid cell with no OCR text
    └── monitor_1_candidate_2.png
```

---

## External Dependencies

| Package | Framework/Library | Role |
|---|---|---|
| `mss` | Python | Cross-platform screen capture |
| `Pillow` | Python | Image manipulation, drawing, saving |
| `pyobjc-framework-Vision` | macOS | Apple Vision OCR (`VNRecognizeTextRequest`) |
| `pyobjc-framework-Quartz` | macOS | Low-level mouse event synthesis |
| `pyobjc-framework-Cocoa` | macOS | `Foundation.NSData` for Vision image input |

---

## Known Limitations / Design Notes

- **`TARGET_TEXT` is hardcoded** in `config.py` — it must be changed manually before each run.
- **Interactive fallback uses `stdin`** — the tool pauses and waits for keyboard input when multiple matches are found or when no text matches are found. There is no GUI.
- **mss capturing wallpaper instead of app windows** — on macOS, `mss` uses the `CGWindowListCreateImage` API which may capture the desktop/wallpaper instead of on-screen app windows if Screen Recording permission is not granted. Grant permission in *System Settings → Privacy & Security → Screen Recording*.
- **Single-pass, no loop** — the tool runs once, clicks once, and exits. It is not a continuous agent.
- **Grid-based icon search is coarse** — the 3×3 grid means icon candidates are large screen regions, not individual icons. A human must eyeball the saved crops and provide the precise relative coordinate.

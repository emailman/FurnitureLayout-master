# CLAUDE.md — Furniture Layout Project

## Project Overview

Desktop GUI application (Python + tkinter) for arranging furniture on a floor plan image.
Users load an image, set a pixel-to-inch scale, then place and move labeled furniture rectangles.

## Running the App

```bash
# Activate the venv first (PyCharm does this automatically)
.venv/Scripts/activate    # Windows
python main.py
```

## Installing Dependencies

```bash
pip install -r requirements.txt   # Only dependency: Pillow
```

## Architecture

| File | Responsibility |
|------|---------------|
| `main.py` | 5-line entry point — creates `tk.Tk`, instantiates `Application` |
| `app.py` | `Application` class: assembles toolbar, canvas, status bar, menu; wires all callbacks |
| `canvas_view.py` | `FloorPlanCanvas(tk.Canvas)`: image display, furniture rendering, drag/drop, rotation, selection |
| `furniture.py` | `FurnitureItem` dataclass + `corners(scale)` / `flat_corners(scale)` rotation geometry |
| `dialogs.py` | `ScaleDialog`, `AddFurnitureDialog`, `EditFurnitureDialog` (all `tk.Toplevel`) |
| `layout_manager.py` | `save_layout()` / `load_layout()` — JSON serialization |
| `print_layout.py` | `render_layout_image()` / `print_layout()` — render the floor plan + furniture to a single printable page and send it to the default printer |

## Key Design Decisions

**Scale**: stored as `float` pixels-per-inch on `FloorPlanCanvas.scale`. All furniture pixel
sizes are computed on the fly: `item.width_in * scale`. Changing scale triggers a full redraw.

**Furniture rendering**: each item is drawn as two canvas items sharing the same UUID tag —
a `create_polygon` (the rectangle, possibly rotated) and a `create_text` (label at center).
Using a shared tag means `canvas.delete(item.id)` removes both at once.

**Rotation geometry**: `FurnitureItem` stores the center point `(x, y)` and `angle_deg`.
`corners(scale)` applies a standard 2D rotation matrix around the center. Updating a
rotated item calls `canvas.coords(polygon_id, *new_flat_corners)` in-place — no
delete/recreate, so z-order is preserved.

**Drag**: delta-from-start approach (`new_pos = start_center + (current_mouse - start_mouse)`)
prevents floating-point drift. Center is clamped to image bounds.

**Printing**: `print_layout.render_layout_image()` re-renders the floor plan and furniture
with Pillow (not a canvas screenshot) onto a fixed US Letter page (150 DPI, 0.5" margins),
computing a single `orig_px_to_page_px` factor so the floor image and furniture overlay
stay in sync. The page is saved to a temp PNG and handed to the OS via
`os.startfile(path, "print")` — Windows-only, no extra dependencies beyond Pillow.

**Hit detection**: `canvas.find_overlapping(cx±4, cy±4)` returns canvas item IDs; their tags
are checked against `FurnitureItem.id` values (UUIDs). Iterating in reverse gives the topmost item.

## Adding New Features

- **New dialog**: subclass `_FurnitureDialog` in `dialogs.py` and override `_set_result()`
- **New toolbar button**: add `ttk.Button` in `app.py._build_toolbar()`, wire to a canvas method
- **Export to image**: use `PIL.ImageGrab` or render canvas items onto a Pillow image

## Layout JSON Format

```json
{
  "version": 1,
  "image_path": "floorplan.png",
  "scale_px_per_in": 4.167,
  "furniture": [
    {
      "id": "<uuid>",
      "name": "Sofa",
      "width_in": 72.0,
      "height_in": 34.0,
      "x": 320.5,
      "y": 410.0,
      "angle_deg": 90.0,
      "color": "#A8D8EA"
    }
  ]
}
```

`image_path` is stored relative to the JSON file for portability.

## Dependency Notes

- **Pillow**: only external dependency; needed because `tkinter.PhotoImage` only supports GIF/PPM.
  Pillow handles JPG, PNG, TIFF, WebP, etc. via `PIL.ImageTk.PhotoImage`.
- **tkinter**: ships with Python on all platforms; no install needed.
- Python 3.14+ required (uses `str | None` union type syntax).

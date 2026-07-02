import json
import os

from furniture import FurnitureItem


def save_layout(path: str, image_path: str, scale: float,
                items: list[FurnitureItem]) -> None:
    """Serialize the current layout to a JSON file."""
    layout_dir = os.path.dirname(os.path.abspath(path))
    try:
        rel_image = os.path.relpath(image_path, layout_dir) if image_path else ""
    except ValueError:
        # relpath can fail when paths are on different Windows drives
        rel_image = image_path

    data = {
        "version": 1,
        "image_path": rel_image,
        "scale_px_per_in": scale,
        "furniture": [
            {
                "id":         item.id,
                "name":       item.name,
                "width_in":   item.width_in,
                "height_in":  item.height_in,
                "x":          item.x,
                "y":          item.y,
                "angle_deg":  item.angle_deg,
                "color":      item.color,
            }
            for item in items
        ],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_layout(path: str) -> tuple[str, float, list[FurnitureItem]]:
    """Deserialize a layout JSON file.

    Returns:
        (absolute_image_path, scale_px_per_in, furniture_items)
    """
    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    layout_dir = os.path.dirname(os.path.abspath(path))
    rel_image = data.get("image_path", "")
    abs_image = os.path.normpath(os.path.join(layout_dir, rel_image))\
        if rel_image else ""

    scale = float(data.get("scale_px_per_in", 1.0))

    items = [
        FurnitureItem(
            id=d["id"],
            name=d["name"],
            width_in=float(d["width_in"]),
            height_in=float(d["height_in"]),
            x=float(d["x"]),
            y=float(d["y"]),
            angle_deg=float(d["angle_deg"]),
            color=d.get("color", "#A8D8EA"),
        )
        for d in data.get("furniture", [])
    ]

    return abs_image, scale, items

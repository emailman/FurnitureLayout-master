import os
import sys
import tempfile

from PIL import Image, ImageDraw, ImageFont

from furniture import FurnitureItem

PAGE_SIZE_IN = (8.5, 11.0)   # US Letter, portrait
MARGIN_IN = 0.5
DPI = 150


def render_layout_image(image_path: str, scale: float,
                        items: list[FurnitureItem]) -> Image.Image:
    """Render the floor plan and all furniture onto a single Letter-size
    page, scaled uniformly to fit within the printable margins."""
    floor_img = Image.open(image_path).convert("RGB")
    img_w_in = floor_img.width / scale
    img_h_in = floor_img.height / scale

    printable_w_in = PAGE_SIZE_IN[0] - 2 * MARGIN_IN
    printable_h_in = PAGE_SIZE_IN[1] - 2 * MARGIN_IN
    fit_ratio = min(printable_w_in / img_w_in, printable_h_in / img_h_in)
    # Converts a coordinate in floor-plan image pixels to a coordinate in
    # rendered-page pixels (both the resize and the furniture overlay must
    # use this same factor so furniture lines up with the floor plan).
    orig_px_to_page_px = fit_ratio * DPI / scale

    resized_w = max(1, round(floor_img.width * orig_px_to_page_px))
    resized_h = max(1, round(floor_img.height * orig_px_to_page_px))
    floor_resized = floor_img.resize((resized_w, resized_h), Image.LANCZOS)

    page = Image.new("RGB",
                     (round(PAGE_SIZE_IN[0] * DPI), round(PAGE_SIZE_IN[1] * DPI)),
                     "white")
    offset_x = round((page.width - resized_w) / 2)
    offset_y = round((page.height - resized_h) / 2)
    page.paste(floor_resized, (offset_x, offset_y))

    draw = ImageDraw.Draw(page)
    try:
        font = ImageFont.truetype("arial.ttf", 11)
    except OSError:
        font = ImageFont.load_default()

    for item in items:
        page_corners = [
            (offset_x + x * orig_px_to_page_px, offset_y + y * orig_px_to_page_px)
            for x, y in item.corners(scale)
        ]
        draw.polygon(page_corners, fill=item.color, outline="#333333", width=1)

        label = f"{item.name}\n{item.width_in:.0f}\" x {item.height_in:.0f}\""
        cx = offset_x + item.x * orig_px_to_page_px
        cy = offset_y + item.y * orig_px_to_page_px
        draw.multiline_text((cx, cy), label, fill="#000000", font=font,
                            anchor="mm", align="center")

    return page


def print_layout(image_path: str, scale: float, items: list[FurnitureItem]) -> str:
    """Render the layout to a single printable page and send it to the
    default printer. Returns the path of the rendered PNG."""
    page = render_layout_image(image_path, scale, items)

    fd, path = tempfile.mkstemp(suffix=".png", prefix="furniture_layout_")
    os.close(fd)
    page.save(path)

    if sys.platform == "win32":
        os.startfile(path, "print")
    else:
        raise OSError("Printing is only supported on Windows in this build.")

    return path

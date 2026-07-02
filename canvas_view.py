import tkinter as tk
from tkinter import messagebox

from PIL import Image, ImageTk

from furniture import FurnitureItem


class FloorPlanCanvas(tk.Canvas):
    def __init__(self, parent, status_callback=None, **kwargs):
        super().__init__(parent, bg="#d0d0d0", cursor="crosshair", **kwargs)

        self.status_callback = status_callback or (lambda s: None)

        self.image_path: str | None = None
        self.image_size: tuple[int, int] | None = None   # (width_px, height_px)
        self._photo_image = None                          # keep reference to prevent GC

        self.scale: float | None = None                  # pixels per inch
        self.furniture_items: list[FurnitureItem] = []
        self._selected: FurnitureItem | None = None

        # Drag state
        self._drag_item: FurnitureItem | None = None
        self._drag_start_mouse: tuple[float, float] = (0.0, 0.0)
        self._drag_start_center: tuple[float, float] = (0.0, 0.0)

        self._build_context_menu()
        self._bind_events()

    # ── Context menu ───────────────────────────────────────────────
    def _build_context_menu(self):
        self._ctx = tk.Menu(self, tearoff=0)
        self._ctx.add_command(label="Edit",
                              command=self._edit_selected)
        self._ctx.add_command(label="Rotate 90°",
                              command=self.rotate_selected)
        self._ctx.add_separator()
        self._ctx.add_command(label="Bring to Front",
                              command=self._bring_to_front)
        self._ctx.add_command(label="Send to Back",
                              command=self._send_to_back)
        self._ctx.add_separator()
        self._ctx.add_command(label="Delete",
                              command=self.delete_selected)

    # ── Event bindings ─────────────────────────────────────────────
    def _bind_events(self):
        self.bind("<ButtonPress-1>",   self._on_press)
        self.bind("<B1-Motion>",       self._on_drag)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.bind("<Double-Button-1>", self._on_double_click)
        self.bind("<Button-3>",        self._on_right_click)
        self.bind("<MouseWheel>",      self._on_scroll)
        self.bind("<Shift-MouseWheel>", self._on_rotate_scroll)

    # ── Public API ─────────────────────────────────────────────────
    def load_image(self, path: str):
        """Load and display a floor plan image, clearing all existing furniture."""
        img = Image.open(path)
        self.image_path = path
        self.image_size = img.size
        self._photo_image = ImageTk.PhotoImage(img)

        self.delete("all")
        self.furniture_items.clear()
        self._selected = None

        self.create_image(0, 0, anchor=tk.NW, image=self._photo_image,
                          tags=("floor_image",))
        self.configure(scrollregion=(0, 0, img.width, img.height))

    def set_scale(self, scale: float):
        """Set pixels-per-inch scale and redraw all furniture at the new scale."""
        self.scale = scale
        for item in self.furniture_items:
            self._redraw_item(item)

    def add_furniture(self, item: FurnitureItem):
        """Add a new furniture item, placed at the center
         of the visible canvas area."""
        cx = self.canvasx(self.winfo_width() / 2)
        cy = self.canvasy(self.winfo_height() / 2)
        item.x = cx
        item.y = cy
        self.furniture_items.append(item)
        self._draw_item(item)
        self._select(item)

    def rotate_selected(self):
        """Rotate the selected furniture item 90° clockwise."""
        if self._selected:
            self._selected.angle_deg = (self._selected.angle_deg + 90) % 360
            self._redraw_item(self._selected)

    def delete_selected(self):
        """Delete the selected furniture item after confirmation."""
        if not self._selected:
            return
        if messagebox.askyesno("Delete Furniture", f"Delete '{self._selected.name}'?"):
            self.delete(self._selected.id)   # removes both polygon and text (same tag)
            self.furniture_items.remove(self._selected)
            self._selected = None
            self._post_status()

    def load_layout(self, image_path: str, scale: float, items: list[FurnitureItem]):
        """Load a saved layout: image, scale, and all furniture items."""
        if image_path:
            self.load_image(image_path)
        self.scale = scale
        self.furniture_items = items
        for item in items:
            self._draw_item(item)

    # ── Rendering ──────────────────────────────────────────────────
    def _draw_item(self, item: FurnitureItem):
        scale = self.scale or 1.0
        pts = item.flat_corners(scale)
        label = f"{item.name}\n{item.width_in:.0f}\" × {item.height_in:.0f}\""

        self.create_polygon(
            *pts,
            fill=item.color,
            outline="#333333",
            width=1,
            tags=(item.id, "furniture"),
        )
        self.create_text(
            item.x, item.y,
            text=label,
            justify="center",
            font=("Arial", 8),
            tags=(item.id, "furniture"),
        )

    def _redraw_item(self, item: FurnitureItem):
        """Update polygon coords and text position in-place (no delete/recreate)."""
        scale = self.scale or 1.0
        pts = item.flat_corners(scale)
        label = f"{item.name}\n{item.width_in:.0f}\" × {item.height_in:.0f}\""

        for cid in self.find_withtag(item.id):
            kind = self.type(cid)
            if kind == "polygon":
                self.coords(cid, *pts)
            elif kind == "text":
                self.coords(cid, item.x, item.y)
                self.itemconfig(cid, text=label)

    # ── Selection ──────────────────────────────────────────────────
    def _select(self, item: FurnitureItem | None):
        if self._selected:
            for cid in self.find_withtag(self._selected.id):
                if self.type(cid) == "polygon":
                    self.itemconfig(cid, outline="#333333", width=1)

        self._selected = item

        if item:
            for cid in self.find_withtag(item.id):
                if self.type(cid) == "polygon":
                    self.itemconfig(cid, outline="#FF6600", width=2)
            msg = f"Selected: {item.name}  ({item.width_in:.1f}\" × {item.height_in:.1f}\")"
            if self.scale:
                msg += f"  |  Scale: {self.scale:.3f} px/in"
            self.status_callback(msg)
        else:
            self._post_status()

    def _post_status(self):
        if self.scale:
            self.status_callback(f"Scale: {self.scale:.3f} px/in")
        else:
            self.status_callback("Set scale to place furniture.")

    # ── Hit detection ──────────────────────────────────────────────
    def _find_furniture_at(self, cx: float, cy: float) -> FurnitureItem | None:
        """Return the topmost furniture item under (cx, cy) in canvas coordinates."""
        candidates = self.find_overlapping(cx - 4, cy - 4, cx + 4, cy + 4)
        for cid in reversed(candidates):
            for tag in self.gettags(cid):
                item = self._item_by_id(tag)
                if item is not None:
                    return item
        return None

    def _item_by_id(self, fid: str) -> FurnitureItem | None:
        for item in self.furniture_items:
            if item.id == fid:
                return item
        return None

    # ── Mouse events ───────────────────────────────────────────────
    def _on_press(self, event):
        cx, cy = self.canvasx(event.x), self.canvasy(event.y)
        hit = self._find_furniture_at(cx, cy)
        if hit:
            self._select(hit)
            self._drag_item = hit
            self._drag_start_mouse = (cx, cy)
            self._drag_start_center = (hit.x, hit.y)
        else:
            self._select(None)
            self._drag_item = None

    def _on_drag(self, event):
        if not self._drag_item:
            return
        cx, cy = self.canvasx(event.x), self.canvasy(event.y)
        dx = cx - self._drag_start_mouse[0]
        dy = cy - self._drag_start_mouse[1]
        new_x = self._drag_start_center[0] + dx
        new_y = self._drag_start_center[1] + dy

        # Clamp to image bounds
        if self.image_size:
            new_x = max(0.0, min(new_x, float(self.image_size[0])))
            new_y = max(0.0, min(new_y, float(self.image_size[1])))

        self._drag_item.x = new_x
        self._drag_item.y = new_y
        self._redraw_item(self._drag_item)

    def _on_release(self, event):
        self._drag_item = None

    def _on_double_click(self, event):
        cx, cy = self.canvasx(event.x), self.canvasy(event.y)
        hit = self._find_furniture_at(cx, cy)
        if hit:
            self._edit_furniture(hit)

    def _on_right_click(self, event):
        cx, cy = self.canvasx(event.x), self.canvasy(event.y)
        hit = self._find_furniture_at(cx, cy)
        if hit:
            self._select(hit)
            self._ctx.tk_popup(event.x_root, event.y_root)

    def _on_scroll(self, event):
        if event.delta > 0:
            self.yview_scroll(-1, "units")
        else:
            self.yview_scroll(1, "units")

    def _on_rotate_scroll(self, event):
        """Shift+scroll wheel: free rotation in 5° increments."""
        if self._selected:
            delta = -5 if event.delta > 0 else 5
            self._selected.angle_deg = (self._selected.angle_deg + delta) % 360
            self._redraw_item(self._selected)

    # ── Context menu actions ───────────────────────────────────────
    def _edit_selected(self):
        if self._selected:
            self._edit_furniture(self._selected)

    def _edit_furniture(self, item: FurnitureItem):
        from dialogs import EditFurnitureDialog
        dlg = EditFurnitureDialog(self.winfo_toplevel(), item)
        if dlg.result is not None:
            item.name = dlg.result.name
            item.width_in = dlg.result.width_in
            item.height_in = dlg.result.height_in
            self._redraw_item(item)
            # Refresh selection highlight status text
            if self._selected is item:
                self._select(item)

    def _bring_to_front(self):
        if self._selected:
            self.tag_raise(self._selected.id)
            self.tag_lower("floor_image")

    def _send_to_back(self):
        if self._selected:
            # Lower to just above the floor image (i.e., behind other furniture)
            self.tag_lower(self._selected.id)
            self.tag_raise(self._selected.id, "floor_image")

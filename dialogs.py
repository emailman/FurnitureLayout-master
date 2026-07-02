import tkinter as tk
from tkinter import ttk, messagebox
import uuid

from furniture import FurnitureItem, COLORS


# ── Unit helpers ───────────────────────────────────────────────────
def _parse_ft_in(ft_str: str, in_str: str) -> float:
    """Parse separate feet and inches text fields → total decimal inches."""
    try:
        ft = float(ft_str.strip()) if ft_str.strip() else 0.0
    except ValueError:
        ft = 0.0
    try:
        inches = float(in_str.strip()) if in_str.strip() else 0.0
    except ValueError:
        inches = 0.0
    return ft * 12.0 + inches


def _inches_to_ft_in(total_in: float) -> tuple[int, float]:
    """Split decimal inches → (whole feet, remaining inches)."""
    ft = int(total_in // 12)
    rem = total_in % 12
    return ft, rem


# ── Scale dialog ───────────────────────────────────────────────────
class ScaleDialog(tk.Toplevel):
    """Ask the user for the real-world width of the floor plan
     to compute px/in scale."""

    def __init__(self, parent, image_size: tuple[int, int]):
        super().__init__(parent)
        self.title("Set Floor Plan Scale")
        self.resizable(False, False)
        self.grab_set()
        self.transient(parent)

        self.image_size = image_size
        self.result: float | None = None

        self._build()
        self.wait_window()

    def _build(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill="both", expand=True)

        ttk.Label(
            frame,
            text=f"Image size: {self.image_size[0]} × {self.image_size[1]} pixels",
            foreground="gray",
        ).grid(row=0, column=0, columnspan=5, sticky="w", pady=(0, 10))

        (ttk.Label(frame, text="Floor plan width:").
         grid(row=1, column=0, sticky="e", padx=(0, 4)))
        self._wft = ttk.Entry(frame, width=5)
        self._wft.grid(row=1, column=1)
        ttk.Label(frame, text="ft").grid(row=1, column=2, padx=(2, 8))
        self._win = ttk.Entry(frame, width=6)
        self._win.grid(row=1, column=3)
        ttk.Label(frame, text="in").grid(row=1, column=4, padx=(2, 0))

        self._feedback = ttk.Label(frame, text="", foreground="gray")
        self._feedback.grid(row=2, column=0, columnspan=5, sticky="w", pady=(10, 0))

        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=5, pady=(14, 0))
        ttk.Button(btn_frame, text="OK",     command=self._ok).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side="left", padx=4)

        self._wft.bind("<KeyRelease>", self._update_feedback)
        self._win.bind("<KeyRelease>", self._update_feedback)
        self.bind("<Return>", lambda e: self._ok())
        self.bind("<Escape>", lambda e: self.destroy())
        self._wft.focus()

    def _update_feedback(self, _event=None):
        total_in = _parse_ft_in(self._wft.get(), self._win.get())
        if total_in > 0:
            scale = self.image_size[0] / total_in
            h_in = self.image_size[1] / scale
            h_ft, h_rem = _inches_to_ft_in(h_in)
            self._feedback.config(
                text=f"Scale: {scale:.3f} px/in  →  height ≈ {h_ft}' {h_rem:.1f}\""
            )
        else:
            self._feedback.config(text="")

    def _ok(self):
        total_in = _parse_ft_in(self._wft.get(), self._win.get())
        if total_in <= 0:
            messagebox.showwarning("Invalid Input",
                                   "Please enter a valid floor plan width.",
                                   parent=self)
            return
        self.result = self.image_size[0] / total_in
        self.destroy()


# ── Shared furniture dialog base ───────────────────────────────────
class _FurnitureDialog(tk.Toplevel):
    """Base class for Add/Edit furniture dialogs."""

    def __init__(self, parent, title: str,
                 name: str = "",
                 width_ft: int = 0, width_rem_in: float = 0.0,
                 height_ft: int = 0, height_rem_in: float = 0.0):
        super().__init__(parent)
        self.title(title)
        self.resizable(False, False)
        self.grab_set()
        self.transient(parent)
        self.result: FurnitureItem | None = None

        self._init_name     = name
        self._init_wft      = str(width_ft)     if width_ft > 0     else ""
        self._init_win      = f"{width_rem_in:.2g}"  if width_rem_in > 0 else ""
        self._init_hft      = str(height_ft)    if height_ft > 0    else ""
        self._init_hin      = f"{height_rem_in:.2g}" if height_rem_in > 0 else ""

        self._build()
        self.wait_window()

    def _build(self):
        frame = ttk.Frame(self, padding=16)
        frame.pack(fill="both", expand=True)

        # Name row
        ttk.Label(frame, text="Name:").grid(row=0, column=0, sticky="e", pady=4, padx=(0, 4))
        self._name_entry = ttk.Entry(frame, width=22)
        self._name_entry.insert(0, self._init_name)
        self._name_entry.grid(row=0, column=1, columnspan=4, sticky="w")

        # Width row
        ttk.Label(frame, text="Width:").grid(row=1, column=0, sticky="e", pady=4, padx=(0, 4))
        self._wft = ttk.Entry(frame, width=5)
        self._wft.insert(0, self._init_wft)
        self._wft.grid(row=1, column=1)
        ttk.Label(frame, text="ft").grid(row=1, column=2, padx=(2, 8))
        self._win = ttk.Entry(frame, width=6)
        self._win.insert(0, self._init_win)
        self._win.grid(row=1, column=3)
        ttk.Label(frame, text="in").grid(row=1, column=4, padx=(2, 0))

        # Depth row
        ttk.Label(frame, text="Depth:").grid(row=2, column=0, sticky="e", pady=4, padx=(0, 4))
        self._hft = ttk.Entry(frame, width=5)
        self._hft.insert(0, self._init_hft)
        self._hft.grid(row=2, column=1)
        ttk.Label(frame, text="ft").grid(row=2, column=2, padx=(2, 8))
        self._hin = ttk.Entry(frame, width=6)
        self._hin.insert(0, self._init_hin)
        self._hin.grid(row=2, column=3)
        ttk.Label(frame, text="in").grid(row=2, column=4, padx=(2, 0))

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=3, column=0, columnspan=5, pady=(14, 0))
        ttk.Button(btn_frame, text="OK",     command=self._ok).pack(side="left", padx=4)
        ttk.Button(btn_frame, text="Cancel", command=self.destroy).pack(side="left", padx=4)

        self.bind("<Return>", lambda e: self._ok())
        self.bind("<Escape>", lambda e: self.destroy())
        self._name_entry.focus()

    def _ok(self):
        name = self._name_entry.get().strip()
        if not name:
            messagebox.showwarning("Invalid", "Please enter a furniture name.", parent=self)
            return
        w = _parse_ft_in(self._wft.get(), self._win.get())
        h = _parse_ft_in(self._hft.get(), self._hin.get())
        if w <= 0 or h <= 0:
            messagebox.showwarning(
                "Invalid Dimensions",
                "Width and height must both be greater than 0.",
                parent=self,
            )
            return
        self._set_result(name, w, h)
        self.destroy()

    def _set_result(self, name: str, width_in: float, height_in: float):
        raise NotImplementedError


# ── Add dialog ─────────────────────────────────────────────────────
class AddFurnitureDialog(_FurnitureDialog):
    _color_index: int = 0

    def __init__(self, parent):
        super().__init__(parent, title="Add Furniture")

    def _set_result(self, name: str, width_in: float, height_in: float):
        color = COLORS[AddFurnitureDialog._color_index % len(COLORS)]
        AddFurnitureDialog._color_index += 1
        self.result = FurnitureItem(
            name=name,
            width_in=width_in,
            height_in=height_in,
            color=color,
            id=str(uuid.uuid4()),
        )


# ── Edit dialog ────────────────────────────────────────────────────
class EditFurnitureDialog(_FurnitureDialog):
    def __init__(self, parent, item: FurnitureItem):
        self._item = item
        ft_w, rem_w = _inches_to_ft_in(item.width_in)
        ft_h, rem_h = _inches_to_ft_in(item.height_in)
        super().__init__(
            parent,
            title="Edit Furniture",
            name=item.name,
            width_ft=ft_w,   width_rem_in=rem_w,
            height_ft=ft_h,  height_rem_in=rem_h,
        )

    def _set_result(self, name: str, width_in: float, height_in: float):
        self.result = FurnitureItem(
            name=name,
            width_in=width_in,
            height_in=height_in,
            x=self._item.x,
            y=self._item.y,
            angle_deg=self._item.angle_deg,
            color=self._item.color,
            id=self._item.id,
        )

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from canvas_view import FloorPlanCanvas
from dialogs import ScaleDialog, AddFurnitureDialog
import layout_manager
import print_layout


class Application:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Furniture Layout")
        self.root.geometry("1200x800")
        self._save_path: str | None = None

        self._build_menu()
        self._build_toolbar()
        self._build_canvas()
        self._build_statusbar()
        self._bind_keys()

    # ── Menu ───────────────────────────────────────────────────────
    def _build_menu(self):
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open Layout…", command=self._open_layout,
                              accelerator="Ctrl+O")
        file_menu.add_command(label="Save Layout", command=self._save_layout,
                              accelerator="Ctrl+S")
        file_menu.add_command(label="Save Layout As…", command=self._save_layout_as)
        file_menu.add_separator()
        file_menu.add_command(label="Print Layout…", command=self._print_layout,
                              accelerator="Ctrl+P")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menubar)

    # ── Toolbar ────────────────────────────────────────────────────
    def _build_toolbar(self):
        tb = ttk.Frame(self.root, relief="raised")
        tb.pack(side="top", fill="x", padx=2, pady=2)

        ttk.Button(tb, text="Load Image",
                   command=self._load_image).pack(side="left", padx=2, pady=2)
        ttk.Button(tb, text="Set Scale",
                   command=self._set_scale).pack(side="left", padx=2, pady=2)
        ttk.Separator(tb, orient="vertical").pack(side="left", fill="y", padx=6, pady=2)
        ttk.Button(tb, text="Add Furniture",
                   command=self._add_furniture).pack(side="left", padx=2, pady=2)
        ttk.Button(tb, text="Rotate 90°",
                   command=self._rotate).pack(side="left", padx=2, pady=2)
        ttk.Button(tb, text="Delete",
                   command=self._delete).pack(side="left", padx=2, pady=2)

    # ── Canvas area ────────────────────────────────────────────────
    def _build_canvas(self):
        frame = ttk.Frame(self.root)
        frame.pack(side="top", fill="both", expand=True)

        self.canvas = FloorPlanCanvas(frame,
                                      status_callback=self._update_status)

        h_scroll = ttk.Scrollbar(frame, orient="horizontal",
                                 command=self.canvas.xview)
        v_scroll = ttk.Scrollbar(frame, orient="vertical",
                                 command=self.canvas.yview)
        self.canvas.configure(xscrollcommand=h_scroll.set,
                              yscrollcommand=v_scroll.set)

        h_scroll.pack(side="bottom", fill="x")
        v_scroll.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

    # ── Status bar ─────────────────────────────────────────────────
    def _build_statusbar(self):
        self._status_var = (
            tk.StringVar(value="Load a floor plan image to begin."))
        ttk.Label(
            self.root, textvariable=self._status_var,
            relief="sunken", anchor="w", padding=(6, 2)
        ).pack(side="bottom", fill="x")

    def _update_status(self, text: str):
        self._status_var.set(text)

    # ── Key bindings ───────────────────────────────────────────────
    def _bind_keys(self):
        self.root.bind("<Control-s>", lambda e: self._save_layout())
        self.root.bind("<Control-o>", lambda e: self._open_layout())
        self.root.bind("<Control-p>", lambda e: self._print_layout())
        self.root.bind("r", lambda e: self._rotate())
        self.root.bind("R", lambda e: self._rotate())
        self.root.bind("<Delete>", lambda e: self._delete())

    # ── Toolbar callbacks ──────────────────────────────────────────
    def _load_image(self):
        path = filedialog.askopenfilename(
            title="Select Floor Plan Image",
            filetypes=[
                ("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp *.tiff *.webp"),
                ("All Files", "*.*"),
            ],
        )
        if not path:
            return
        self.canvas.load_image(path)
        self._update_status(f"Loaded: {path}  |  Click 'Set Scale' to calibrate dimensions.")

    def _set_scale(self):
        if not self.canvas.image_size:
            messagebox.showwarning("No Image",
                                   "Please load a floor plan image first.")
            return
        dlg = ScaleDialog(self.root, self.canvas.image_size)
        if dlg.result is not None:
            self.canvas.set_scale(dlg.result)
            self._update_status(
                f"Scale: {dlg.result:.3f} px/in  |  Click 'Add Furniture' to place items."
            )

    def _add_furniture(self):
        if not self.canvas.scale:
            messagebox.showwarning("No Scale",
                                   "Please set the floor plan scale first.")
            return
        dlg = AddFurnitureDialog(self.root)
        if dlg.result is not None:
            self.canvas.add_furniture(dlg.result)

    def _rotate(self):
        self.canvas.rotate_selected()

    def _delete(self):
        self.canvas.delete_selected()

    # ── Save / Load ────────────────────────────────────────────────
    def _save_layout(self):
        if not self._save_path:
            self._save_layout_as()
            return
        self._do_save(self._save_path)

    def _save_layout_as(self):
        path = filedialog.asksaveasfilename(
            title="Save Layout",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
        )
        if path:
            self._save_path = path
            self._do_save(path)

    def _do_save(self, path: str):
        layout_manager.save_layout(
            path,
            self.canvas.image_path or "",
            self.canvas.scale or 0.0,
            self.canvas.furniture_items,
        )
        self.root.title(f"Furniture Layout — {path}")
        self._update_status(f"Saved: {path}")

    def _open_layout(self):
        path = filedialog.askopenfilename(
            title="Open Layout",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
        )
        if not path:
            return
        try:
            image_path, scale, items = layout_manager.load_layout(path)
            self.canvas.load_layout(image_path, scale, items)
            self._save_path = path
            self.root.title(f"Furniture Layout — {path}")
            self._update_status(f"Opened: {path}")
        except Exception as exc:
            messagebox.showerror("Error", f"Failed to load layout:\n{exc}")

    # ── Print ──────────────────────────────────────────────────────
    def _print_layout(self):
        if not self.canvas.image_path or not self.canvas.scale:
            messagebox.showwarning(
                "Nothing to Print",
                "Please load a floor plan image and set the scale first.")
            return
        try:
            path = print_layout.print_layout(
                self.canvas.image_path, self.canvas.scale,
                self.canvas.furniture_items)
            self._update_status(f"Sent layout to printer ({path})")
        except Exception as exc:
            messagebox.showerror("Print Failed", f"Could not print layout:\n{exc}")

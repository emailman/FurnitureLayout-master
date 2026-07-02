import math
import uuid
from dataclasses import dataclass, field


COLORS = [
    "#A8D8EA", "#AA96DA", "#FCBAD3", "#FFFFD2",
    "#B5EAD7", "#FFD700", "#C8A2C8", "#98D8C8",
    "#F7DC6F", "#A9CCE3", "#A3E4D7", "#F9E79F",
]


@dataclass
class FurnitureItem:
    name: str
    width_in: float
    height_in: float
    x: float = 0.0
    y: float = 0.0
    angle_deg: float = 0.0
    color: str = "#A8D8EA"
    id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def corners(self, scale: float) -> list[tuple[float, float]]:
        """Return 4 canvas-pixel corners after rotation, centered on (x, y)."""
        w = self.width_in * scale / 2
        h = self.height_in * scale / 2
        rad = math.radians(self.angle_deg)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        local = [(-w, -h), (w, -h), (w, h), (-w, h)]
        return [
            (self.x + lx * cos_a - ly * sin_a,
             self.y + lx * sin_a + ly * cos_a)
            for lx, ly in local
        ]

    def flat_corners(self, scale: float) -> list[float]:
        """Return corners as a flat list [x0, y0, x1, y1, ...]
         for tkinter create_polygon."""
        pts = self.corners(scale)
        return [coord for pt in pts for coord in pt]

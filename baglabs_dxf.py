#!/usr/bin/env python3
"""Writes the Baglabs RoundCorners patches UPPER and LOWER to a DXF file.

The geometry and the mark positions come from the same model as the Inkscape
extension (extensions/baglabs_roundcorners/baglabs_roundcorners.py), so both
outputs always agree. The DXF is written directly (ASCII, release 12), no
extra Python package is needed. All values are in cm, 1 drawing unit = 1 cm,
the Y axis points up.

Layers:
  OUTLINE  solid outer line
  SEWING   dashed sewing line, 1 cm inside
  MARKS    marks between outer line and sewing line (double line = thick)
  TEXT     mark numbers and patch names

The script imports the Inkscape extension module, which needs the ``inkex``
module that ships with Inkscape (set PYTHONPATH to Inkscape's extensions
folder if it is not found automatically).
"""

from __future__ import annotations

import argparse
import datetime
import math
import os
import sys
from types import SimpleNamespace

BASE = os.path.dirname(os.path.abspath(__file__))
SEAM = 1.0  # sewing border in cm
GAP = 5.0  # distance between the two patches in cm
TEXT_H = 0.8  # height of the mark numbers in cm
MARK_WIDTH = 0.12  # distance of the two lines forming a thick mark, in cm

for _p in (
    os.path.join(BASE, "extensions", "baglabs_roundcorners"),
    "/usr/share/inkscape/extensions",
    "/Applications/Inkscape.app/Contents/Resources/share/inkscape/extensions",
):
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.append(_p)

try:
    from baglabs_roundcorners import BaglabsRoundCorners
except ImportError as exc:  # pragma: no cover
    sys.exit(
        f"Cannot import the extension ({exc}). The 'inkex' module of Inkscape is "
        "required: set PYTHONPATH to Inkscape's extensions folder, e.g.\n"
        "  PYTHONPATH=/usr/share/inkscape/extensions python3 baglabs_dxf.py"
    )


class Dxf:
    """Minimal ASCII DXF (R12) writer for LINE, ARC and TEXT entities."""

    LAYERS = (  # name, ACI color, linetype
        ("OUTLINE", 7, "CONTINUOUS"),
        ("SEWING", 7, "DASHED"),
        ("MARKS", 7, "CONTINUOUS"),
        ("TEXT", 7, "CONTINUOUS"),
    )

    def __init__(self):
        self.entities = []

    def _add(self, *pairs):
        self.entities.extend(pairs)

    def line(self, layer, x1, y1, x2, y2):
        self._add((0, "LINE"), (8, layer), (10, x1), (20, y1), (30, 0.0),
                  (11, x2), (21, y2), (31, 0.0))

    def arc(self, layer, cx, cy, r, start, end):
        """Counter-clockwise arc, angles in degrees."""
        self._add((0, "ARC"), (8, layer), (10, cx), (20, cy), (30, 0.0),
                  (40, r), (50, float(start)), (51, float(end)))

    def text(self, layer, x, y, height, text):
        """Text centered horizontally and vertically on (x, y)."""
        self._add((0, "TEXT"), (8, layer), (10, x), (20, y), (30, 0.0),
                  (40, height), (1, text), (72, 1), (11, x), (21, y),
                  (31, 0.0), (73, 2))

    def rounded_rect(self, layer, x0, y0, w, h, r):
        r = max(0.0, min(r, w / 2, h / 2))
        x1, y1 = x0 + w, y0 + h
        self.line(layer, x0 + r, y0, x1 - r, y0)
        self.line(layer, x1, y0 + r, x1, y1 - r)
        self.line(layer, x1 - r, y1, x0 + r, y1)
        self.line(layer, x0, y1 - r, x0, y0 + r)
        if r > 0:
            self.arc(layer, x1 - r, y0 + r, r, 270, 360)
            self.arc(layer, x1 - r, y1 - r, r, 0, 90)
            self.arc(layer, x0 + r, y1 - r, r, 90, 180)
            self.arc(layer, x0 + r, y0 + r, r, 180, 270)

    def mark(self, x1, y1, x2, y2):
        """A mark; DXF R12 has no line width, so it is drawn as a double line
        (MARK_WIDTH apart) to look thick."""
        dx, dy = x2 - x1, y2 - y1
        n = math.hypot(dx, dy) or 1.0
        ox, oy = -dy / n * MARK_WIDTH / 2, dx / n * MARK_WIDTH / 2
        self.line("MARKS", x1 + ox, y1 + oy, x2 + ox, y2 + oy)
        self.line("MARKS", x1 - ox, y1 - oy, x2 - ox, y2 - oy)


    def write(self, path):
        out = []

        def put(code, value):
            out.append(f"{code:>3}")
            out.append(f"{value:.6f}" if isinstance(value, float) else str(value))

        put(0, "SECTION"); put(2, "HEADER")
        put(9, "$ACADVER"); put(1, "AC1009")
        put(9, "$INSUNITS"); put(70, 5)  # 5 = centimeters
        put(0, "ENDSEC")

        put(0, "SECTION"); put(2, "TABLES")
        put(0, "TABLE"); put(2, "LTYPE"); put(70, 2)
        put(0, "LTYPE"); put(2, "CONTINUOUS"); put(70, 0)
        put(3, "Solid line"); put(72, 65); put(73, 0); put(40, 0.0)
        put(0, "LTYPE"); put(2, "DASHED"); put(70, 0)
        put(3, "Dashed __ __ __"); put(72, 65); put(73, 2); put(40, 0.5)
        put(49, 0.3); put(49, -0.2)
        put(0, "ENDTAB")
        put(0, "TABLE"); put(2, "LAYER"); put(70, len(self.LAYERS))
        for name, color, ltype in self.LAYERS:
            put(0, "LAYER"); put(2, name); put(70, 0); put(62, color); put(6, ltype)
        put(0, "ENDTAB")
        put(0, "TABLE"); put(2, "STYLE"); put(70, 1)
        put(0, "STYLE"); put(2, "STANDARD"); put(70, 0); put(40, 0.0)
        put(41, 1.0); put(50, 0.0); put(71, 0); put(42, 1.0)
        put(3, "txt"); put(4, "")
        put(0, "ENDTAB")
        put(0, "ENDSEC")

        put(0, "SECTION"); put(2, "ENTITIES")
        for code, value in self.entities:
            put(code, value)
        put(0, "ENDSEC")
        put(0, "EOF")
        with open(path, "w", encoding="ascii", errors="replace", newline="\n") as f:
            f.write("\n".join(out) + "\n")


def draw_patch(dxf, spec, ox, oy):
    """Draws one patch with its lower left corner at (ox, oy), Y pointing up.

    The model measures Y from the top edge, so Y values are flipped.
    """
    w, h, r = spec["w"], spec["h"], spec["r"]
    dxf.rounded_rect("OUTLINE", ox, oy, w, h, r + SEAM)
    dxf.rounded_rect("SEWING", ox + SEAM, oy + SEAM, w - 2 * SEAM, h - 2 * SEAM, r)

    # radial marks in the middle (45 degrees) of every corner arc; the
    # corners are given in the order top left, top right, bottom left, bottom right
    R = r + SEAM
    k = math.sqrt(0.5)
    corners = [
        (ox + R, oy + h - R, -1, 1),
        (ox + w - R, oy + h - R, 1, 1),
        (ox + R, oy + R, -1, -1),
        (ox + w - R, oy + R, 1, -1),
    ]
    for (cx, cy, sx, sy), label in zip(corners, spec["corners"]):
        dxf.mark(cx + sx * k * R, cy + sy * k * R,
                 cx + sx * k * (R - SEAM), cy + sy * k * (R - SEAM))
        rl = max(R - SEAM - 1.0, 0.5)
        dxf.text("TEXT", cx + sx * k * rl, cy + sy * k * rl, TEXT_H, label)

    off = SEAM + TEXT_H  # label center distance from the outer line (inner side)

    # X marks: label "a,b" -> a at the top edge, b at the bottom edge
    for x, label in spec["x_marks"]:
        first, _, second = label.partition(",")
        dxf.mark(ox + x, oy + h, ox + x, oy + h - SEAM)
        dxf.mark(ox + x, oy, ox + x, oy + SEAM)
        if first:
            dxf.text("TEXT", ox + x, oy + h - off, TEXT_H, first)
        if second:
            dxf.text("TEXT", ox + x, oy + off, TEXT_H, second)

    # Y marks (measured from the top): label "a,b" -> a at left, b at right edge
    for y, label in spec["y_marks"]:
        first, _, second = label.partition(",")
        yy = oy + h - y
        dxf.mark(ox, yy, ox + SEAM, yy)
        dxf.mark(ox + w, yy, ox + w - SEAM, yy)
        if first:
            dxf.text("TEXT", ox + off, yy, TEXT_H, first)
        if second:
            dxf.text("TEXT", ox + w - off, yy, TEXT_H, second)

    # patch name and date in the middle
    cx, cy = ox + w / 2, oy + h / 2
    dxf.text("TEXT", cx, cy + 0.8, 1.5, spec["name"])
    dxf.text("TEXT", cx, cy - 0.8, 0.6, datetime.date.today().isoformat())


def build(options, path):
    ext = BaglabsRoundCorners.__new__(BaglabsRoundCorners)  # model() needs only options
    ext.options = options
    specs = ext.model()
    for spec in specs.values():
        if spec["w"] <= 2 * (spec["r"] + SEAM) or spec["h"] <= 2 * (spec["r"] + SEAM):
            sys.exit(
                f"Patch {spec['name']} is too small for the given radius/values "
                f"({spec['w']:.1f} x {spec['h']:.1f} cm). Please check the inputs."
            )
    dxf = Dxf()
    draw_patch(dxf, specs["upper"], 0.0, 0.0)
    draw_patch(dxf, specs["lower"], specs["upper"]["w"] + GAP, 0.0)
    dxf.write(path)
    return specs


def main():
    ap = argparse.ArgumentParser(
        description="Write the Baglabs RoundCorners patches UPPER and LOWER to a DXF "
        "file. All values in cm; defaults are the values of the XLSX file."
    )
    ap.add_argument("--length", type=float, default=50.0, help="Länge L")
    ap.add_argument("--width", type=float, default=30.0, help="Breite Br")
    ap.add_argument("--height", type=float, default=30.0, help="Höhe Ho (t)")
    ap.add_argument("--segment_height", type=float, default=20.0, help="Segmenthöhe Hs")
    ap.add_argument("--radius_top", type=float, default=11.0, help="Rt")
    ap.add_argument("--radius_bottom", type=float, default=5.0, help="Rb")
    ap.add_argument("--output", default=os.path.join(BASE, "baglabs_patches.dxf"),
                    help="output DXF file (default: baglabs_patches.dxf in the project base)")
    args = ap.parse_args()
    options = SimpleNamespace(**{k: v for k, v in vars(args).items() if k != "output"})
    specs = build(options, args.output)
    print(f"Wrote {args.output}: UPPER {specs['upper']['w']:.1f} x {specs['upper']['h']:.1f} cm, "
          f"LOWER {specs['lower']['w']:.1f} x {specs['lower']['h']:.1f} cm")


if __name__ == "__main__":
    main()


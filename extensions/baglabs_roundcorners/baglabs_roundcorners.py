#!/usr/bin/env python3
"""Baglabs RoundCorners Inkscape extension.

Plots the two sewing patches UPPER and LOWER of a bag with rounded corners
(see dev/Baglab_roundedCorners_WIP.xlsx). All inputs and the drawn geometry
are in centimeters.
"""

from __future__ import annotations

import datetime
import math

import inkex

SEAM = 1.0  # sewing border in cm
EPS = 1e-6


class BaglabsRoundCorners(inkex.EffectExtension):
    """Draws the UPPER and LOWER patches including sewing line and marks."""

    def add_arguments(self, pars):
        pars.add_argument("--tab", type=str, default="main")
        pars.add_argument("--length", type=float, default=50.0, help="Länge L in cm")
        pars.add_argument("--width", type=float, default=30.0, help="Breite Br in cm")
        pars.add_argument("--height", type=float, default=30.0, help="Höhe Ho (t) in cm")
        pars.add_argument(
            "--segment_height", type=float, default=20.0, help="Segmenthöhe Hs in cm"
        )
        pars.add_argument("--radius_top", type=float, default=11.0, help="Rt in cm")
        pars.add_argument("--radius_bottom", type=float, default=5.0, help="Rb in cm")

    # ------------------------------------------------------------------
    # Model (formulas from the XLSX sheet "Double U")
    # ------------------------------------------------------------------
    def model(self):
        L = self.options.length
        Br = self.options.width
        t = self.options.height
        Hs = self.options.segment_height
        Rt = self.options.radius_top
        Rb = self.options.radius_bottom
        k = 1 - math.pi / 4
        dt = math.pi / 4 * Rt  # D11
        db = math.pi / 4 * Rb  # E11

        # Outer dimensions (first table)
        upper_x = 2 + L + 2 * t - 2 * Hs - Rt * (4 - math.pi)
        upper_y = 2 + Br
        lower_x = 2 + L
        lower_y = 2 + 2 * t + Br - Rb * (4 - math.pi)

        # UPPER X marks (column C rows 22..30). They are given along the
        # whole strip; the patch starts Hs into the strip, so shift by -Hs.
        c24 = 1 + t - Rt * k
        c26 = c24 + L / 2 - Rt * k
        c28 = c26 + L / 2 - Rt * k
        c31 = c28 + t - Rt * k
        # Numbered marks (clock positions): where the straight L section
        # starts / is centered / ends.
        numbered = [(c24 + dt - Hs, "11,7"), (c26 - Hs, "12,6"), (c28 - dt - Hs, "1,5")]
        # Unnamed marks: (a) exactly where the outer corner arcs (radius Rb + 1)
        # meet the straight top/bottom edges, i.e. 1 + Rb from each border;
        # (b) the yellow table cells C24 and C28 (arc mid-points of the bag
        # corner, shifted by -Hs) which lie inside the patch.
        arc_end = 1 + Rb
        extra = [c24 - Hs, c26 - Hs, c28 - Hs]
        marks = [(arc_end, ""), (upper_x - arc_end, "")] + numbered
        # the numbered marks Pt 11/7 and 1/5 get marks at Pt - dt and
        # Pt + dt with dt = PI/4 * Rt; 12/6 has no neighbour marks
        for pos, _ in (numbered[0], numbered[2]):
            extra += [pos - dt, pos + dt]
        for x in extra:
            if EPS < x < upper_x - EPS and all(abs(x - m[0]) > EPS for m in marks):
                marks.append((x, ""))
        upper_x_marks = sorted(marks, key=lambda m: m[0])

        # UPPER Y marks (column C rows 38..40)
        upper_y_marks = [(1 + Rb, ""), (1 + Br / 2, "9,3"), (1 + Br - Rb, "")]

        # LOWER Y marks (column D rows 22..30)
        d24 = 1 + t - Rb * k
        d26 = d24 + Br / 2 - Rb * k
        d28 = d26 + Br / 2 - Rb * k
        d31 = d28 + t - Rb * k
        lower = [1 + Rt, d24 - db, d24, d24 + db, d26, d28 - db, d28, d28 + db, d31 - Rt]
        names = {d24: "10,2", d26: "9,3", d28: "8,4"}
        lower_y_marks = [(d, names.get(d, "")) for d in lower]

        # LOWER X marks (column D rows 38..40)
        lower_x_marks = [(1 + Rt, ""), (1 + L / 2, "12,6"), (1 + L - Rt, "")]

        return {
            "upper": dict(
                name="UPPER", w=upper_x, h=upper_y, r=Rb, rname="Rb",
                corners=("10", "2", "8", "4"),  # TL, TR, BL, BR
                x_marks=upper_x_marks, y_marks=upper_y_marks,
            ),
            "lower": dict(
                name="LOWER", w=lower_x, h=lower_y, r=Rt, rname="Rt",
                corners=("11", "1", "7", "5"),  # TL, TR, BL, BR
                x_marks=lower_x_marks, y_marks=lower_y_marks,
            ),
        }

    # ------------------------------------------------------------------
    # Drawing helpers (model lengths in cm, converted with self.cm)
    # ------------------------------------------------------------------
    def rounded_rect_d(self, x0, y0, w, h, r):
        s = self.cm
        r = max(0.0, min(r, w / 2, h / 2))
        x1, y1 = x0 + w, y0 + h

        def p(x, y):
            return f"{x * s:.4f} {y * s:.4f}"

        def corner(x, y):
            if r > 0:
                return f"A {r * s:.4f} {r * s:.4f} 0 0 1 {p(x, y)} "
            return f"L {p(x, y)} "

        return (
            f"M {p(x0 + r, y0)} L {p(x1 - r, y0)} " + corner(x1, y0 + r)
            + f"L {p(x1, y1 - r)} " + corner(x1 - r, y1)
            + f"L {p(x0 + r, y1)} " + corner(x0, y1 - r)
            + f"L {p(x0, y0 + r)} " + corner(x0 + r, y0) + "Z"
        )

    def add_path(self, parent, d, width_cm, dashed=False, name=None):
        el = inkex.PathElement()
        el.set("d", d)
        style = {
            "fill": "none",
            "stroke": "#000000",
            "stroke-width": f"{width_cm * self.cm:.4f}",
        }
        if dashed:
            style["stroke-dasharray"] = f"{0.3 * self.cm:.4f},{0.2 * self.cm:.4f}"
        el.style = style
        if name:
            el.set("inkscape:label", name)
        parent.add(el)

    def add_line(self, parent, x1, y1, x2, y2):
        s = self.cm
        d = f"M {x1 * s:.4f} {y1 * s:.4f} L {x2 * s:.4f} {y2 * s:.4f}"
        self.add_path(parent, d, 0.12, name="mark")

    def add_text(self, parent, x, y, text):
        fs = 0.8  # cm
        el = inkex.TextElement()
        el.set("x", f"{x * self.cm:.4f}")
        el.set("y", f"{(y + fs * 0.35) * self.cm:.4f}")  # vertically centered
        el.style = {
            "font-size": f"{fs * self.cm:.4f}px",
            "text-anchor": "middle",
            "fill": "#000000",
            "font-family": "sans-serif",
        }
        el.text = text
        parent.add(el)

    def draw_patch(self, parent, spec, ox, oy):
        w, h, r = spec["w"], spec["h"], spec["r"]
        group = inkex.Group()
        group.set("inkscape:label", spec["name"])
        parent.add(group)

        # outer line: the radius gets the additional sewing centimeter
        self.add_path(group, self.rounded_rect_d(ox, oy, w, h, r + SEAM), 0.03, name="outline")
        # dashed sewing line, 1 cm inside
        self.add_path(
            group,
            self.rounded_rect_d(ox + SEAM, oy + SEAM, w - 2 * SEAM, h - 2 * SEAM, r),
            0.03, dashed=True, name="sewing",
        )

        # corner marks: radial mark at the middle (45 degrees) of every arc
        R = r + SEAM
        k = math.sqrt(0.5)
        centers = [
            (ox + R, oy + R, -1, -1),
            (ox + w - R, oy + R, 1, -1),
            (ox + R, oy + h - R, -1, 1),
            (ox + w - R, oy + h - R, 1, 1),
        ]
        for (cx, cy, sx, sy), label in zip(centers, spec["corners"]):
            self.add_line(
                group, cx + sx * k * R, cy + sy * k * R,
                cx + sx * k * (R - SEAM), cy + sy * k * (R - SEAM),
            )
            rl = max(R - SEAM - 1.0, 0.5)
            self.add_text(group, cx + sx * k * rl, cy + sy * k * rl, label)

        off = SEAM + 0.8  # label center distance from the outer line (inner side)

        # X marks: label "a,b" -> a at top edge, b at bottom edge
        for x, label in spec["x_marks"]:
            first, _, second = label.partition(",")
            self.add_line(group, ox + x, oy, ox + x, oy + SEAM)
            self.add_line(group, ox + x, oy + h, ox + x, oy + h - SEAM)
            if first:
                self.add_text(group, ox + x, oy + off, first)
            if second:
                self.add_text(group, ox + x, oy + h - off, second)

        # Y marks: label "a,b" -> a at left edge, b at right edge
        for y, label in spec["y_marks"]:
            first, _, second = label.partition(",")
            self.add_line(group, ox, oy + y, ox + SEAM, oy + y)
            self.add_line(group, ox + w, oy + y, ox + w - SEAM, oy + y)
            if first:
                self.add_text(group, ox + off, oy + y, first)
            if second:
                self.add_text(group, ox + w - off, oy + y, second)

    # ------------------------------------------------------------------
    # Dimensioning
    # ------------------------------------------------------------------
    DIM_COLOR = "#0000ff"

    def dim_line(self, parent, x1, y1, x2, y2):
        s = self.cm
        el = inkex.PathElement()
        el.set("d", f"M {x1 * s:.4f} {y1 * s:.4f} L {x2 * s:.4f} {y2 * s:.4f}")
        el.style = {
            "fill": "none",
            "stroke": self.DIM_COLOR,
            "stroke-width": f"{0.02 * s:.4f}",
        }
        el.set("inkscape:label", "dimension")
        parent.add(el)

    def dim_text(self, parent, x, y, text, rotate=False, fs=0.55):
        s = self.cm
        el = inkex.TextElement()
        el.set("x", f"{x * s:.4f}")
        el.set("y", f"{y * s:.4f}")
        if rotate:
            el.set("transform", f"rotate(-90 {x * s:.4f} {y * s:.4f})")
        el.style = {
            "font-size": f"{fs * s:.4f}px",
            "text-anchor": "middle",
            "fill": self.DIM_COLOR,
            "font-family": "sans-serif",
        }
        el.text = text
        parent.add(el)

    @staticmethod
    def fmt(v):
        return f"{v:.1f}".replace(".0", "") if abs(v - round(v)) < 0.05 else f"{v:.1f}"

    def dim_chain(self, parent, positions, fixed, horizontal, ox, oy):
        """Dimension chain through `positions` (cm along the axis) at `fixed`."""
        pts = sorted(set(round(p, 4) for p in positions))
        tick = 0.3
        if horizontal:
            self.dim_line(parent, ox + pts[0], oy + fixed, ox + pts[-1], oy + fixed)
        else:
            self.dim_line(parent, ox + fixed, oy + pts[0], ox + fixed, oy + pts[-1])
        for p in pts:
            if horizontal:
                self.dim_line(parent, ox + p, oy + fixed - tick, ox + p, oy + fixed + tick)
            else:
                self.dim_line(parent, ox + fixed - tick, oy + p, ox + fixed + tick, oy + p)
        for a, b in zip(pts, pts[1:]):
            seg = b - a
            if seg < 1.0:
                continue
            mid = (a + b) / 2
            if horizontal:
                self.dim_text(parent, ox + mid, oy + fixed - 0.25, self.fmt(seg))
            else:
                self.dim_text(parent, ox + fixed - 0.25, oy + mid, self.fmt(seg), rotate=True)

    def dim_radius(self, parent, cx, cy, r, sx, sy, text):
        """Radius leader from the arc centre to the arc, steep (20 deg from the
        vertical) so it does not collide with the 45 deg corner mark."""
        a = math.radians(20)
        dx, dy = sx * math.sin(a), sy * math.cos(a)
        self.dim_line(parent, cx, cy, cx + dx * r, cy + dy * r)
        self.dim_line(parent, cx - 0.2, cy, cx + 0.2, cy)
        self.dim_line(parent, cx, cy - 0.2, cx, cy + 0.2)
        self.dim_text(parent, cx + dx * r * 0.5 + sx * 0.9, cy + dy * r * 0.5, text)

    def draw_dimensions(self, parent, spec, ox, oy):
        w, h, r = spec["w"], spec["h"], spec["r"]
        group = inkex.Group()
        group.set("inkscape:label", spec["name"] + " dimensions")
        parent.add(group)
        # overall (outer) measures only
        self.dim_chain(group, [0.0, w], h - 6.5, True, ox, oy)
        self.dim_chain(group, [0.0, h], w - 6.5, False, ox, oy)
        # outer radius (r + 1 cm sewing border) at all four rounded corners
        R = r + SEAM
        for cx, cy, sx, sy in (
            (ox + R, oy + R, -1, -1),
            (ox + w - R, oy + R, 1, -1),
            (ox + R, oy + h - R, -1, 1),
            (ox + w - R, oy + h - R, 1, 1),
        ):
            self.dim_radius(group, cx, cy, R, sx, sy, f"{spec['rname']} {self.fmt(R)}")

    def draw_info_box(self, parent, spec, ox, oy):
        """Box with patch name, date and a table of all input parameters."""
        o = self.options
        rows = [
            ("Länge (L)", o.length), ("Breite (Br)", o.width),
            ("Höhe (Ho)", o.height), ("Segmenthöhe (Hs)", o.segment_height),
            ("Radius Top (Rt)", o.radius_top), ("Radius Bottom (Rb)", o.radius_bottom),
        ]
        bw, row_h = 10.0, 0.75
        bh = 0.4 + 1.3 + 0.8 + len(rows) * row_h + 0.4
        bx = ox + spec["w"] / 2 - bw / 2
        by = oy + spec["h"] / 2 - bh / 2
        s = self.cm
        group = inkex.Group()
        group.set("inkscape:label", spec["name"] + " info")
        parent.add(group)
        d = (f"M {bx * s:.4f} {by * s:.4f} h {bw * s:.4f} v {bh * s:.4f} "
             f"h {-bw * s:.4f} Z")
        self.add_path(group, d, 0.05, name="info box")

        def txt(x, y, text, size, anchor="middle", bold=False):
            el = inkex.TextElement()
            el.set("x", f"{x * s:.4f}")
            el.set("y", f"{y * s:.4f}")
            el.style = {
                "font-size": f"{size * s:.4f}px", "text-anchor": anchor,
                "fill": "#000000", "font-family": "sans-serif",
                "font-weight": "bold" if bold else "normal",
            }
            el.text = text
            group.add(el)

        y = by + 0.4 + 1.0
        txt(bx + bw / 2, y, spec["name"], 1.2, bold=True)
        y += 0.8
        txt(bx + bw / 2, y, datetime.date.today().isoformat(), 0.55)
        y += 0.3
        line = f"M {(bx + 0.4) * s:.4f} {y * s:.4f} h {(bw - 0.8) * s:.4f}"
        self.add_path(group, line, 0.02, name="info separator")
        y += 0.6
        for name, value in rows:
            txt(bx + 0.5, y, name, 0.5, anchor="start")
            txt(bx + bw - 0.5, y, f"{value:g} cm", 0.5, anchor="end")
            y += row_h

    def draw_mark_tables(self, parent, spec, ox, oy):
        """Tables of the mark positions like in the XLS (NAME / cm, START..END).

        UPPER: X then Y; LOWER: Y then X (same order as in the sheet). The first
        table is left of the info box, the second one right of it.
        """
        s = self.cm
        if spec["name"] == "UPPER":
            tables = [("UPPER X", spec["x_marks"], spec["w"]),
                      ("UPPER Y", spec["y_marks"], spec["h"])]
        else:
            tables = [("LOWER Y", spec["y_marks"], spec["h"]),
                      ("LOWER X", spec["x_marks"], spec["w"])]
        tw, row_h, info_w = 7.0, 0.65, 10.0
        group = inkex.Group()
        group.set("inkscape:label", spec["name"] + " mark tables")
        parent.add(group)

        def txt(x, y, text, size, anchor="start", bold=False):
            el = inkex.TextElement()
            el.set("x", f"{x * s:.4f}")
            el.set("y", f"{y * s:.4f}")
            el.style = {
                "font-size": f"{size * s:.4f}px", "text-anchor": anchor,
                "fill": "#000000", "font-family": "sans-serif",
                "font-weight": "bold" if bold else "normal",
            }
            el.text = text
            group.add(el)

        for i, (title, marks, end) in enumerate(tables):
            rows = [("START", 0.0)]
            rows += [(name.replace(",", "/"), pos) for pos, name in marks]
            rows.append(("END", end))
            th = (len(rows) + 2) * row_h
            cx = ox + spec["w"] / 2
            tx = cx - info_w / 2 - 1.0 - tw if i == 0 else cx + info_w / 2 + 1.0
            ty = oy + spec["h"] / 2 - th / 2
            d = (f"M {tx * s:.4f} {ty * s:.4f} h {tw * s:.4f} v {th * s:.4f} "
                 f"h {-tw * s:.4f} Z")
            self.add_path(group, d, 0.05, name=title + " table")
            txt(tx + tw / 2, ty + row_h * 0.75, title, 0.55, anchor="middle", bold=True)
            y = ty + row_h
            for k in (1, 2):  # separators below title and column header
                line = f"M {tx * s:.4f} {(ty + k * row_h) * s:.4f} h {tw * s:.4f}"
                self.add_path(group, line, 0.02, name="table separator")
            txt(tx + 0.3, ty + row_h * 1.75, "NAME", 0.45, bold=True)
            txt(tx + tw - 0.3, ty + row_h * 1.75, "cm", 0.45, anchor="end", bold=True)
            y = ty + row_h * 2.75
            for name, pos in rows:
                txt(tx + 0.3, y, name, 0.45)
                txt(tx + tw - 0.3, y, f"{pos:.2f}", 0.45, anchor="end")
                y += row_h

    def effect(self):
        self.cm = self.svg.unittouu("1cm")
        layer = self.svg.get_current_layer()
        specs = self.model()
        for spec in specs.values():
            if spec["w"] <= 2 * (spec["r"] + SEAM) or spec["h"] <= 2 * (spec["r"] + SEAM):
                raise inkex.AbortExtension(
                    f"Patch {spec['name']} is too small for the given radius/values "
                    f"({spec['w']:.1f} x {spec['h']:.1f} cm). Please check the inputs."
                )
        margin = 3.0
        gap = 5.0
        lower_ox = margin + specs["upper"]["w"] + gap
        self.draw_patch(layer, specs["upper"], margin, margin)
        self.draw_info_box(layer, specs["upper"], margin, margin)
        self.draw_mark_tables(layer, specs["upper"], margin, margin)
        self.draw_dimensions(layer, specs["upper"], margin, margin)
        self.draw_patch(layer, specs["lower"], lower_ox, margin)
        self.draw_info_box(layer, specs["lower"], lower_ox, margin)
        self.draw_mark_tables(layer, specs["lower"], lower_ox, margin)
        self.draw_dimensions(layer, specs["lower"], lower_ox, margin)

        # The patches are far larger than a default page: fit the page to them.
        total_w = lower_ox + specs["lower"]["w"] + margin
        total_h = margin * 2 + max(specs["upper"]["h"], specs["lower"]["h"])
        root = self.svg
        root.set("width", f"{total_w:.3f}cm")
        root.set("height", f"{total_h:.3f}cm")
        root.set("viewBox", f"0 0 {total_w * self.cm:.4f} {total_h * self.cm:.4f}")

        # confirmation (shown by Inkscape as a message box) so it is visible that it ran
        inkex.errormsg(
            f"Baglabs RoundCorners: plotted UPPER ({specs['upper']['w']:.1f} x "
            f"{specs['upper']['h']:.1f} cm) and LOWER ({specs['lower']['w']:.1f} x "
            f"{specs['lower']['h']:.1f} cm). Press 5 to fit the page into the window."
        )


if __name__ == "__main__":
    BaglabsRoundCorners().run()

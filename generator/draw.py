"""Drawing operation layer + PyMuPDF painter.

Renderers emit ops; the painter executes them on a PDF page. Keeping the op
layer separate lets the redesigned templates swap renderers freely while the
painter, link wiring, and validation stay identical.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

import pymupdf

# ---------------------------------------------------------------------------
# Ops
# ---------------------------------------------------------------------------

@dataclass
class TextOp:
    x: float
    y: float            # BASELINE of the text
    text: str
    size: float
    color: str
    font: str = "main"  # key into Fonts registry
    rotate: int = 0     # 0 / 90 (counterclockwise, around baseline origin)


@dataclass
class LineOp:
    x0: float
    y0: float
    x1: float
    y1: float
    color: str
    width: float = 0.4


@dataclass
class RectOp:
    x0: float
    y0: float
    x1: float
    y1: float
    fill: Optional[str] = None
    stroke: Optional[str] = None
    width: float = 0.4


@dataclass
class CircleOp:
    x: float
    y: float
    r: float
    fill: Optional[str] = None
    stroke: Optional[str] = None
    width: float = 0.4


@dataclass
class DotGridOp:
    x: float                 # left edge of grid
    y: float                 # top edge of grid
    dx: float
    dy: float
    r: float
    color: str
    cols: int
    rows: int


@dataclass
class LinkOp:
    x0: float
    y0: float
    x1: float
    y1: float
    target: str              # named destination (PageMap target)
    note: str = ""           # debugging label


# ---------------------------------------------------------------------------
# Font registry
# ---------------------------------------------------------------------------

class Fonts:
    """Maps design font keys to pymupdf font buffers.

    Ships with CM-like STIX (via matplotlib) or extracted embedded fonts.
    Populated at build time by build.py.
    """

    def __init__(self):
        self._buffers: dict[str, bytes] = {}
        self._fonts: dict[str, pymupdf.Font] = {}

    def register_file(self, key: str, path):
        with open(path, "rb") as f:
            self.register_buffer(key, f.read())

    def register_buffer(self, key: str, buf: bytes):
        self._buffers[key] = buf
        self._fonts[key] = pymupdf.Font(fontbuffer=buf)

    def alias(self, key: str, target: str):
        self._buffers[key] = self._buffers[target]
        self._fonts[key] = self._fonts[target]

    def has(self, key: str) -> bool:
        return key in self._buffers

    def buffer(self, key: str) -> bytes:
        if key not in self._buffers:
            raise KeyError(f"font {key!r} not registered; have {list(self._buffers)}")
        return self._buffers[key]

    def get(self, key: str) -> pymupdf.Font:
        return self._fonts[key]

    def text_width(self, text: str, key: str, size: float) -> float:
        return self.get(key).text_length(text, size)


# ---------------------------------------------------------------------------
# Painter
# ---------------------------------------------------------------------------

def _hex_to_rgb01(color: str):
    c = color.lstrip("#")
    if len(c) == 3:
        c = "".join(ch * 2 for ch in c)
    return tuple(int(c[i:i + 2], 16) / 255 for i in (0, 2, 4))


class DotAssets:
    """Creates one XObject page per distinct dot-grid size and stamps it,
    so a 1102-dot grid is stored once per document instead of once per page."""

    def __init__(self, dx: float = 14.173, r: float = 0.5):
        self.doc = pymupdf.open()
        self.dx, self.r = dx, r
        self._pages: dict = {}   # (cols, rows, color) -> page number

    def page_for(self, cols: int, rows: int, color: str = "#C7CFA3"):
        key = (cols, rows, color)
        if key in self._pages:
            return self._pages[key]
        import math
        def h01(color: str):
            c = color.lstrip("#")
            return tuple(int(c[i:i + 2], 16) / 255 for i in (0, 2, 4))
        p = self.doc.new_page(width=cols * self.dx + 2 * self.r,
                              height=rows * self.dx + 2 * self.r)
        sh = p.new_shape()
        for rr in range(rows):
            for cc in range(cols):
                sh.draw_circle((cc * self.dx + self.r, rr * self.dx + self.r), self.r)
        sh.finish(fill=h01(color), color=None)
        sh.commit()
        self._pages[key] = len(self.doc) - 1
        return self._pages[key]

    def stamp(self, page: pymupdf.Page, op: DotGridOp):
        pno = self.page_for(op.cols, op.rows, op.color)
        page.show_pdf_page(
            pymupdf.Rect(op.x, op.y,
                         op.x + op.cols * op.dx + 2 * op.r,
                         op.y + op.rows * op.dy + 2 * op.r),
            self.doc, pno)


class Painter:
    def __init__(self, page: pymupdf.Page, fonts: Fonts, dot_assets: DotAssets = None):
        self.page = page
        self.fonts = fonts
        self.dot_assets = dot_assets
        self.links: list[LinkOp] = []
        self.deferred_dots: list[tuple] = []   # (page, op) stamped later
        self.defer_dots = False
        self._registered: set = set()

    def execute(self, ops):
        for op in ops:
            if isinstance(op, TextOp):
                self._text(op)
            elif isinstance(op, LineOp):
                shape = self.page.new_shape()
                shape.draw_line((op.x0, op.y0), (op.x1, op.y1))
                shape.finish(color=_hex_to_rgb01(op.color), width=op.width)
                shape.commit()
            elif isinstance(op, RectOp):
                shape = self.page.new_shape()
                shape.draw_rect((op.x0, op.y0, op.x1, op.y1))
                shape.finish(color=_hex_to_rgb01(op.stroke) if op.stroke else None,
                             fill=_hex_to_rgb01(op.fill) if op.fill else None,
                             width=op.width)
                shape.commit()
            elif isinstance(op, CircleOp):
                shape = self.page.new_shape()
                shape.draw_circle((op.x, op.y), op.r)
                shape.finish(color=_hex_to_rgb01(op.stroke) if op.stroke else None,
                             fill=_hex_to_rgb01(op.fill) if op.fill else None,
                             width=op.width)
                shape.commit()
            elif isinstance(op, DotGridOp):
                if self.defer_dots:
                    self.deferred_dots.append((self.page.number, op))
                elif self.dot_assets is not None:
                    self.dot_assets.stamp(self.page, op)
                else:
                    shape = self.page.new_shape()
                    fill = _hex_to_rgb01(op.color)
                    for r in range(op.rows):
                        for c in range(op.cols):
                            shape.draw_circle((op.x + c * op.dx, op.y + r * op.dy), op.r)
                    shape.finish(color=None, fill=fill)
                    shape.commit()
            elif isinstance(op, LinkOp):
                self.links.append(op)
            else:
                raise ValueError(f"unknown op {op!r}")

    # -- text --------------------------------------------------------------
    def _text(self, op: TextOp):
        fname = f"F{abs(hash(op.font)) % 100000}"  # stable per-font key
        fbuf = self.fonts.buffer(op.font)
        if op.font not in self._registered:
            self.page.insert_font(fontname=fname, fontbuffer=fbuf)
            self._registered.add(op.font)
        color = _hex_to_rgb01(op.color)
        rotate = op.rotate if op.rotate in (0, 90, 180, 270) else 0
        self.page.insert_text((op.x, op.y), op.text, fontname=fname,
                              fontsize=op.size, color=color, rotate=rotate)

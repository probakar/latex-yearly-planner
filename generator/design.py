"""Design tokens for the planner rendering layer.

The tokens describe the *current* (baseline olive) design of the reference
planner. When the redesigned template pages are analyzed, a new Design
instance replaces these values (and/or per-page-kind renderers change), while
the calendar engine, page map, and link graph stay untouched.

All linear units are points (1 cm = 28.3465 pt). Page size: 15.6 x 20.9 cm.
"""

from dataclasses import dataclass, field

CM = 28.3465


def cm(v: float) -> float:
    return v * CM


@dataclass
class Design:
    year: int = 2027

    # page geometry (rm2.base.yaml) -----------------------------------------
    page_w: float = cm(15.6)          # 442.20 pt
    page_h: float = cm(20.9)          # 592.44 pt
    margin_top: float = cm(0.3)
    margin_bottom: float = cm(0.6)
    margin_left: float = cm(1.4)      # wide left margin hosts the rotated nav
    margin_right: float = cm(0.3)
    marginpar_width: float = cm(1.0)  # rotated side-nav zone
    marginpar_sep: float = cm(0.45)

    # colors ------------------------------------------------------------------
    # baseline olive palette (reference planner)
    primary: str = "#33401F"   # deepolive  - headings, main text, thick rules
    gray: str = "#7D8F52"      # mediumolive - normal rules, secondary text
    lightgray: str = "#C7CFA3" # softolive  - dots, light rules
    white: str = "#FFFFFF"

    # fonts --------------------------------------------------------------------
    # LaTeX default: Computer Modern (cmr); sizes derived from 9pt extarticle.
    font_regular: str = "cmm"       # key into Fonts registry (baseline: CM-like)
    font_bold: str = "cmm-bold"
    font_sans: str = "cmss"
    base_size: float = 9.0

    # rules ---------------------------------------------------------------------
    rule_thin: float = 0.4           # pt
    rule_thick: float = 0.8          # pt

    # dotted paper ----------------------------------------------------------------
    dot_spacing: float = cm(0.5)     # 5mm grid
    dot_radius: float = 0.35         # pt (circle*{0.1} approx)
    dot_color: str = lightgray

    # writing-line rhythm ------------------------------------------------------------
    line_height: float = cm(0.5)     # \myLenLineHeightButLine = 5mm - .4pt

    # header / breadcrumb ------------------------------------------------------------
    header_resize: float = cm(0.6)   # \myLenHeaderResizeBox = 6mm

    # side navigation bars (rotated 90deg, in left margin) ------------------------------
    side_months_width: float = cm(15.25)   # vertical extent of month bar
    side_quarters_width: float = cm(4.0)   # vertical extent of quarter bar
    side_cell_height: float = None         # measured from reference

    # month grid -------------------------------------------------------------------------
    monthly_cell_height: float = 55.0      # pt, large month grid rows

    # notes index ------------------------------------------------------------------------
    notes_index_cell_height: float = cm(1.45)
    notes_index_pages: int = 3
    notes_per_index_page: int = 38

    # daily schedule ----------------------------------------------------------------------
    daily_bottom_hour: int = 6
    daily_top_hour: int = 23
    daily_todos: int = 8
    daily_notes_rows: int = 26
    daily_grateful: int = 4
    daily_best: int = 4
    daily_log: int = 26
    weekly_lines: int = 11
    quarterly_lines: int = 38

    extra: dict = field(default_factory=dict)

"""Geometry constants measured from the reference planner PDF (points).

Source: ref/reference_planner_2027.pdf span + drawing extraction.
Page: 442.20 x 592.44 pt.
"""

from design import cm

PAGE_W = 442.20
PAGE_H = 592.44

# text frame
TEXT_X0 = 39.7
TEXT_X1 = 433.7
TEXT_W = TEXT_X1 - TEXT_X0  # 394.0
TEXT_Y1 = 575.4             # nominal bottom (unused; side bar exceeds it)

# colors (hex)
PRIMARY = "#33401F"
GRAY = "#7D8F52"
LIGHT = "#C7CFA3"
WHITE = "#FFFFFF"

RULE = 0.4
RULE_THICK = 0.8
BODY = 8.97                 # body text size (LM 9pt rendered)
SMALL = 7.97                # LM 8pt (schedule hours)
DOT_DX = 14.173             # 5mm dot pitch
DOT_R = 0.5                 # lcircle glyph ≈ 1pt dot

# ---- header ---------------------------------------------------------------
# two tab-row patterns:
#   A: day/reflect/day_notes/quarter/month/week  -> rule ~36.7, tabs cell 11.2..27.6
#   B: year/notes_index/note                     -> rule ~37.7, tabs cell 15.1..31.5
HEAD_RULE_Y = {"A": 36.7, "B": 37.7}
TAB_SIZE = 8.97
TAB_CELL_H = 16.4
TAB_PAD = 6.0               # cell text padding each side
TAB_CELL_W = {"Calendar": 48.3, "Notes": 34.8, "Week": 48.9}  # measured fills

# heading (resizebox ~6mm cap height)
HEAD_SIZES = {  # per kind, rendered pt
    "year": 25.16,
    "quarter": 24.13,
    "month": 24.13,
    "week": 24.51,
    "day": 25.55, "reflect": 25.55, "day_notes": 25.55,
    "notes_index": 24.51,
    "note": 24.13,
}
HEAD_BASELINE = 24.9        # approx common baseline for heading text
HEAD_GAP = 7.0              # gap between heading parts (⟨ Week 1 ⟩)

# day heading two-row block
DAY_HEAD_ROW2_BASE = 26.4   # "January" baseline
DAY_HEAD_VLINE_X = 59.0     # separator between number and weekday/month

# ---- side navigation (rotated 90°, left margin) ----------------------------
SIDE_X0 = -0.7              # bar left edge (bleeds off-page, as reference)
SIDE_X1 = 26.7              # bar right edge
SIDE_TEXT_CENTER_X = 12.0   # center of rotated label
SIDE_Q_TOP = 37.1           # Q1 cell top
SIDE_Q_CELL = 28.35         # quarter cell height
SIDE_GAP = 8.9              # gap between bars
SIDE_M_TOP = 159.4          # January cell top
SIDE_M_CELL = 36.04         # month cell height
SIDE_TEXT = 8.97

# ---- annual page ------------------------------------------------------------
ANN_COL_X = [39.7, 175.0, 310.3]   # 3 month columns
ANN_COL_W = 123.4
ANN_NAME_BASE = 52.4               # month name baseline row 1
ANN_HDR_BASE = 68.9                # W M T ... baseline
ANN_ROW_H = 16.35                  # calendar row height
ANN_ROW0_BASE = 88.6               # first data-row baseline
ANN_LINE1 = 58.5                   # underline below name
ANN_LINE2 = 75.3                   # underline below header
ANN_Q_ROW1_BASE = 52.4             # first month name baseline

# ---- quarter page ------------------------------------------------------------
QTR_MINI_X = 39.7
QTR_MINI_W = 130.4                 # measured grid width
QTR_DOTS_X = 177.7
QTR_DOTS_COLS = 19
QTR_DOTS_ROWS = 38

# ---- month page ---------------------------------------------------------------
MON_HDR_BASE = 48.7                # weekday names baseline
MON_THICK2 = 52.6                  # thick line under header
MON_WEEKCOL_W = 14.2               # week label column
MON_VTHICK_X = 53.9                # thick separator after week col
MON_CELL_H = 56.7                  # row height (55pt cell + rules)
MON_DAY_SIZE = 8.97
MON_ROW1_TOP = 53.0

# ---- week page ------------------------------------------------------------------
WK_COL_X = [39.7, 172.5, 305.4]
WK_COL_W = [127.9, 127.9, 128.3]
WK_HDR_BASE = 49.4                 # "4, Monday" baseline
WK_UNDERLINE_Y = [54.8, 236.6, 418.5]
WK_DOTS_TOP = 62.0
WK_DOTS_COLS = 29
WK_DOTS_ROWS = 11

# ---- day page ---------------------------------------------------------------------
DAY_SCHED_BASE = 50.4              # "Schedule" baseline
DAY_SCHED_UL = 55.8                # thick underline
DAY_HOUR_W = 10.4                  # hour label column ("06".."23")
DAY_ROW_H = 14.17
DAY_TODO_X = 172.5
DAY_TODO_W = 260.8
DAY_TODO1_BASE = 65.0              # first checkbox baseline
DAY_TODOS = 8
DAY_NOTES_HDR_BASE = 188.5         # measured ~; recomputed from todo block
DAY_NOTES_UL = 197.0
DAY_NOTES_DOTS_X = 177.7
DAY_NOTES_DOTS_COLS = 19
DAY_NOTES_DOTS_ROWS = 26

# ---- reflect page -------------------------------------------------------------------
RFL_TITLE1_BASE = 47.4
RFL_UL1 = 52.7
RFL_TITLE2_BASE = 124.5
RFL_UL2 = 129.8
RFL_TITLE3_BASE = 201.6
RFL_UL3 = 206.9
RFL_DOTS_X = 39.7
RFL_DOTS_COLS = 29
RFL_ROWS_1 = 4
RFL_ROWS_2 = 4
RFL_ROWS_3 = 26

# ---- day-notes (More) page ------------------------------------------------------------
DN_DOTS_X = 39.7
DN_DOTS_TOP = 41.4
DN_DOTS_COLS = 29
DN_DOTS_ROWS = 38

# ---- notes index ----------------------------------------------------------------------
NI_NUM_X = 45.7
NI_NUM_BASE0 = 50.2                # "01" baseline
NI_VLINE_X = 61.1
NI_ROW_H = 14.17
NI_ROW_LINE0 = 55.3
NI_DOTS_X = 39.7
NI_DOTS_TOP = 41.4
NI_DOTS_COLS = 29
NI_DOTS_ROWS = 38

# ---- note page -------------------------------------------------------------------------
NOTE_DOTS_X = 39.7
NOTE_DOTS_TOP = 41.4
NOTE_DOTS_COLS = 29
NOTE_DOTS_ROWS = 38

# ---- title -----------------------------------------------------------------------------
TITLE_SIZE = 134.18
TITLE_X1 = 426.0                   # right-aligned (STIX advance vs bbox)
TITLE_BASELINE = 608.8   # STIX metrics; ref cap-top 467.2

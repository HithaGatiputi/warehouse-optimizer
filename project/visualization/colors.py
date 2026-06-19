"""
Color palette and theming for the warehouse visualization.

Professional dark theme designed for an operations monitoring dashboard.
All colors are defined as RGB tuples. RGBA variants (with alpha) are
used for translucent overlays like the BFS path highlight.
"""

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  BASE THEME
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BG_PRIMARY = (25, 28, 36)            # Main background
BG_SECONDARY = (35, 39, 48)         # Sidebar / panels
BG_TERTIARY = (45, 50, 62)          # Card backgrounds
BG_CONTROL = (30, 34, 42)           # Control bar

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  GRID CELL COLORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CELL_AISLE_COLOR = (60, 66, 80)          # Walkable aisles
CELL_SHELF_COLOR = (42, 46, 56)          # Storage racks (not walkable)
CELL_SHELF_BORDER = (52, 56, 68)         # Shelf border for 3D effect
CELL_PACKING_COLOR = (39, 174, 96)       # Packing station — green
CELL_DISPATCH_COLOR = (41, 128, 185)     # Dispatch area — blue
GRID_LINE_COLOR = (50, 56, 68)           # Subtle grid lines

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  SKU / ITEM COLORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ITEM_DEFAULT = (80, 90, 110)             # Standard item on shelf
ITEM_IN_ORDER = (241, 196, 15)           # Highlighted — in current order
ITEM_CLASS_A = (231, 76, 60)             # High demand — red
ITEM_CLASS_B = (241, 196, 15)            # Medium demand — amber
ITEM_CLASS_C = (46, 204, 113)            # Low demand — green

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PATH & ROUTE COLORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PATH_COLOR = (66, 133, 244)              # BFS path overlay — blue
ROUTE_LINE_COLOR = (241, 196, 15)        # Optimized route line — yellow
ROUTE_LINE_NN = (231, 76, 60)            # NN route line — red (comparison)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  PICKER COLORS (up to 5 simultaneous pickers)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PICKER_COLORS = [
    (155, 89, 182),     # Purple
    (230, 126, 34),     # Orange
    (26, 188, 156),     # Teal
    (52, 152, 219),     # Blue
    (241, 196, 15),     # Yellow
    (231, 76, 60),      # Red
    (46, 204, 113),     # Green
    (255, 105, 180),    # Hot Pink
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  TEXT HIERARCHY
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TEXT_PRIMARY = (220, 225, 235)           # Main text
TEXT_SECONDARY = (140, 150, 170)         # Muted / labels
TEXT_ACCENT = (66, 133, 244)             # Accent — blue
TEXT_HEADER = (255, 255, 255)            # Section headers

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  UI ELEMENTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
BUTTON_NORMAL = (55, 62, 78)
BUTTON_HOVER = (70, 78, 95)
BUTTON_ACTIVE = (66, 133, 244)
BUTTON_TEXT = (220, 225, 235)

SLIDER_TRACK = (55, 62, 78)
SLIDER_FILL = (66, 133, 244)
SLIDER_HANDLE = (100, 110, 130)

DIVIDER = (55, 60, 72)

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  STATUS INDICATORS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STATUS_SUCCESS = (46, 204, 113)          # Green
STATUS_WARNING = (241, 196, 15)          # Yellow
STATUS_DANGER = (231, 76, 60)            # Red
STATUS_INFO = (66, 133, 244)             # Blue

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
#  HEATMAP GRADIENT (cold → hot)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
HEATMAP_GRADIENT = [
    (66, 133, 244),     # Cool blue
    (46, 204, 113),     # Green
    (241, 196, 15),     # Yellow
    (230, 126, 34),     # Orange
    (231, 76, 60),      # Hot red
]

"""
Warehouse layout management module.

Generates and manages the warehouse grid structure including
shelves, walkable aisles, packing station, and dispatch area.

Layout Design:
    - Vertical aisles every 3rd column (columns 0, 3, 6, 9, ...)
    - Horizontal cross-aisles at top, middle, and bottom rows
    - Pairs of shelf columns fill space between aisles
    - Packing station at bottom-left corner
    - Dispatch area at bottom-right corner

This ensures every shelf cell has at least one adjacent aisle cell,
which is required for BFS pathfinding — pickers stand in an aisle
to pick from an adjacent shelf.

Complexity: O(R × C) for grid generation.
"""

import numpy as np
from typing import Optional

from project.config import (
    GRID_ROWS, GRID_COLS,
    CELL_AISLE, CELL_SHELF, CELL_PACKING, CELL_DISPATCH,
)


class WarehouseLayout:
    """
    Represents the physical layout of a warehouse / dark-store.

    Each cell in the 2D grid has a type:
        0 (AISLE)    — walkable floor space for pickers
        1 (SHELF)    — storage rack, not traversable
        2 (PACKING)  — packing station where orders are assembled
        3 (DISPATCH) — dispatch area where orders leave the warehouse

    The grid is configurable via rows/cols parameters, defaulting
    to the values in config.py (20 × 25).
    """

    def __init__(self, rows: int = GRID_ROWS, cols: int = GRID_COLS) -> None:
        self.rows: int = rows
        self.cols: int = cols
        self.grid: np.ndarray = np.zeros((rows, cols), dtype=int)
        self.packing_station: tuple[int, int] = (rows - 1, 0)
        self.dispatch_area: tuple[int, int] = (rows - 1, cols - 1)

        self._generate_layout()

        # Cache frequently queried cell lists
        self._shelf_cells: list[tuple[int, int]] = []
        self._aisle_cells: list[tuple[int, int]] = []
        self._rebuild_cache()

    # ── Layout Generation ──────────────────────────────────────

    def _generate_layout(self) -> None:
        """
        Generate the warehouse grid.

        Column pattern (for a 25-col grid):
            Col 0:  aisle       Col 12: aisle
            Col 1:  shelf       Col 13: shelf
            Col 2:  shelf       Col 14: shelf
            Col 3:  aisle       Col 15: aisle
            ...                 ...
            Col 24: aisle

        Row pattern:
            Row 0:         top cross-aisle
            Rows 1–9:      shelf rows (in shelf columns)
            Row 10:         middle cross-aisle
            Rows 11–18:    shelf rows (in shelf columns)
            Row 19:         bottom cross-aisle
        """
        # Aisle columns: every 3rd starting from 0, plus last column
        aisle_cols: set[int] = set(range(0, self.cols, 3))
        aisle_cols.add(self.cols - 1)

        # Cross-aisle rows: top, middle, bottom
        mid_row = self.rows // 2
        cross_aisle_rows: set[int] = {0, mid_row, self.rows - 1}

        for r in range(self.rows):
            for c in range(self.cols):
                if r in cross_aisle_rows or c in aisle_cols:
                    self.grid[r, c] = CELL_AISLE
                else:
                    self.grid[r, c] = CELL_SHELF

        # Special cells
        self.grid[self.packing_station] = CELL_PACKING
        self.grid[self.dispatch_area] = CELL_DISPATCH

    def _rebuild_cache(self) -> None:
        """Cache shelf and aisle positions for O(1) lookup."""
        self._shelf_cells = []
        self._aisle_cells = []
        for r in range(self.rows):
            for c in range(self.cols):
                cell = int(self.grid[r, c])
                if cell == CELL_SHELF:
                    self._shelf_cells.append((r, c))
                elif cell in (CELL_AISLE, CELL_PACKING, CELL_DISPATCH):
                    self._aisle_cells.append((r, c))

    # ── Public API ─────────────────────────────────────────────

    def get_shelf_cells(self) -> list[tuple[int, int]]:
        """Return all shelf cell coordinates (available for storage)."""
        return self._shelf_cells.copy()

    def get_aisle_cells(self) -> list[tuple[int, int]]:
        """Return all walkable cells (aisles + packing + dispatch)."""
        return self._aisle_cells.copy()

    def is_walkable(self, r: int, c: int) -> bool:
        """Check if a cell is traversable by a picker."""
        if 0 <= r < self.rows and 0 <= c < self.cols:
            return int(self.grid[r, c]) != CELL_SHELF
        return False

    def get_cell_type(self, r: int, c: int) -> int:
        """Return the cell type at given coordinates, or -1 if out of bounds."""
        if 0 <= r < self.rows and 0 <= c < self.cols:
            return int(self.grid[r, c])
        return -1

    def get_neighbors(self, r: int, c: int) -> list[tuple[int, int]]:
        """
        Return walkable 4-connected neighbors of a cell.

        Directions: up, down, left, right.
        Only returns cells that are within bounds and traversable.
        """
        neighbors: list[tuple[int, int]] = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if self.is_walkable(nr, nc):
                neighbors.append((nr, nc))
        return neighbors

    def get_adjacent_aisle(
        self, shelf_pos: tuple[int, int],
    ) -> Optional[tuple[int, int]]:
        """
        Find the nearest walkable aisle cell adjacent to a shelf position.

        A picker cannot stand on a shelf; they must stand on an adjacent
        aisle cell to pick an item. This method finds that cell.

        Priority order: left, right, up, down — because vertical aisles
        are to the left/right of every shelf pair in our layout.

        Returns:
            Adjacent aisle cell coordinates, or None if none exists
            (should never happen in a well-formed layout).
        """
        r, c = shelf_pos
        for dr, dc in [(0, -1), (0, 1), (-1, 0), (1, 0)]:
            nr, nc = r + dr, c + dc
            if self.is_walkable(nr, nc):
                return (nr, nc)
        return None

    def shelf_count(self) -> int:
        """Total number of shelf cells available for item storage."""
        return len(self._shelf_cells)

    def __repr__(self) -> str:
        return (
            f"WarehouseLayout(rows={self.rows}, cols={self.cols}, "
            f"shelves={self.shelf_count()}, aisles={len(self._aisle_cells)})"
        )

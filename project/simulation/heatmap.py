"""
Tracks warehouse traffic density for heatmap analytics.
"""
import numpy as np
from project.warehouse.layout import WarehouseLayout
from project.simulation.picker import Picker, PickerState

class HeatmapManager:
    def __init__(self, layout: WarehouseLayout):
        self.rows = layout.rows
        self.cols = layout.cols
        self.visit_counts = np.zeros((self.rows, self.cols), dtype=int)
        
    def update(self, pickers: list[Picker]):
        """Increments visit counts for cells currently occupied by active pickers."""
        for p in pickers:
            if p.state != PickerState.IDLE:
                r, c = p.grid_pos
                if 0 <= r < self.rows and 0 <= c < self.cols:
                    self.visit_counts[r, c] += 1
                    
    def reset(self):
        self.visit_counts.fill(0)
        
    def get_normalized_heatmap(self) -> np.ndarray:
        max_val = np.max(self.visit_counts)
        if max_val == 0:
            return self.visit_counts.astype(float)
        return self.visit_counts / max_val

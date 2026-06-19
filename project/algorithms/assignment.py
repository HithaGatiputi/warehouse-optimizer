"""
Picker assignment strategies.
"""
from project.simulation.picker import Picker, PickerState
from project.algorithms.pathfinding import bfs_shortest_path
from project.warehouse.layout import WarehouseLayout

def assign_nearest_available_picker(pickers: list[Picker], layout: WarehouseLayout, target_cell: tuple[int, int]) -> Picker | None:
    """Finds the idle picker with the shortest BFS path to the first item of the order."""
    idle_pickers = [p for p in pickers if p.state == PickerState.IDLE]
    if not idle_pickers:
        return None
        
    best_picker = None
    min_dist = float('inf')
    
    for picker in idle_pickers:
        # Distance from picker's current position to the target cell
        _, dist = bfs_shortest_path(layout, picker.grid_pos, target_cell)
        if dist < min_dist:
            min_dist = dist
            best_picker = picker
            
    # Fallback to any idle picker if unreachable or tied (unlikely in grid)
    if not best_picker and idle_pickers:
        best_picker = idle_pickers[0]
        
    return best_picker

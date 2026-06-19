"""
Picker entity representing warehouse staff moving through the aisles.
"""
from enum import Enum
import math
from project.config import PICKER_BASE_SPEED
from project.simulation.orders import Order

class PickerState(Enum):
    IDLE = 1
    PICKING = 2
    RETURNING = 3

class Picker:
    def __init__(self, picker_id: int, start_pos: tuple[int, int], color: tuple[int, int, int]):
        self.id = picker_id
        self.pixel_x = float(start_pos[1])
        self.pixel_y = float(start_pos[0])
        self.grid_pos = start_pos
        self.color = color
        self.state = PickerState.IDLE
        
        self.active_order: Order | None = None
        self.full_path_cells: list[tuple[int, int]] = []
        self.trail: list[tuple[float, float]] = []
        self.path_index = 0
        
        self.distance_traveled = 0.0
        self.orders_completed = 0
        self.active_time = 0.0
        self.total_time = 0.0
        self.speed = PICKER_BASE_SPEED

    def assign_route(self, order: Order, full_path_cells: list[tuple[int, int]]):
        self.active_order = order
        order.picker_id = self.id
        self.full_path_cells = full_path_cells
        self.path_index = 0
        
        if full_path_cells:
            self.state = PickerState.PICKING

    def update(self, dt: float, tile_size: int, padding: int, offset_x: int = 0, offset_y: int = 0) -> Order | None:
        """Advances the picker along its path. Returns completed order if finished."""
        self.total_time += 1.0
        
        if self.state == PickerState.IDLE or not self.full_path_cells or self.path_index >= len(self.full_path_cells):
            return None

        self.active_time += 1.0
        
        target_cell = self.full_path_cells[self.path_index]
        target_x = target_cell[1] * tile_size + offset_x + tile_size // 2
        target_y = target_cell[0] * tile_size + offset_y + tile_size // 2

        dx = target_x - self.pixel_x
        dy = target_y - self.pixel_y
        dist = math.hypot(dx, dy)

        if dist > self.speed:
            self.pixel_x += (dx / dist) * self.speed
            self.pixel_y += (dy / dist) * self.speed
            self.distance_traveled += self.speed
            self.trail.append((self.pixel_x, self.pixel_y))
        else:
            self.pixel_x = target_x
            self.pixel_y = target_y
            self.distance_traveled += dist
            self.grid_pos = target_cell
            self.path_index += 1
            self.trail.append((self.pixel_x, self.pixel_y))

            if self.path_index >= len(self.full_path_cells):
                # Finished route
                completed_order = self.active_order
                self.state = PickerState.IDLE
                self.orders_completed += 1
                self.active_order = None
                self.full_path_cells = []
                self.trail.clear()
                return completed_order
                
        if len(self.trail) > 50:
            self.trail.pop(0)
                
        return None

    def get_utilization(self) -> float:
        if self.total_time == 0: return 0.0
        return self.active_time / self.total_time

"""
Models picker congestion in the warehouse.
"""
from project.simulation.picker import Picker, PickerState
from project.config import CONGESTION_RADIUS, CONGESTION_SPEED_PENALTY
import math

class CongestionManager:
    def __init__(self):
        self.total_delay_time = 0.0
        self.congestion_events = 0
        
    def update(self, pickers: list[Picker], dt: float):
        """Checks distance between active pickers and applies speed penalties."""
        active_pickers = [p for p in pickers if p.state != PickerState.IDLE]
        
        # Reset speeds first
        for p in active_pickers:
            p.speed = p.speed / CONGESTION_SPEED_PENALTY if getattr(p, '_is_congested', False) else p.speed
            p._is_congested = False
            
        for i in range(len(active_pickers)):
            p1 = active_pickers[i]
            for j in range(i + 1, len(active_pickers)):
                p2 = active_pickers[j]
                
                # Check grid distance
                dr = p1.grid_pos[0] - p2.grid_pos[0]
                dc = p1.grid_pos[1] - p2.grid_pos[1]
                dist = math.hypot(dr, dc)
                
                if dist <= CONGESTION_RADIUS:
                    if not getattr(p1, '_is_congested', False):
                        p1.speed *= CONGESTION_SPEED_PENALTY
                        p1._is_congested = True
                    if not getattr(p2, '_is_congested', False):
                        p2.speed *= CONGESTION_SPEED_PENALTY
                        p2._is_congested = True
                        
                    self.congestion_events += 1
                    self.total_delay_time += (1.0 - CONGESTION_SPEED_PENALTY) * 2

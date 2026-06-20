"""
Lightweight UI state manager for custom carts and mouse hovers.
"""
from dataclasses import dataclass, field
from typing import Optional
from project.warehouse.inventory import SKUInfo
import pygame

@dataclass
class UIState:
    custom_cart: list[SKUInfo] = field(default_factory=list)
    mouse_pos: tuple[int, int] = (0, 0)
    hovered_cell: Optional[tuple[int, int]] = None
    catalog_scroll_y: int = 0
    
    # Store rendering rects so main.py can check collisions on click
    catalog_rects: dict[str, pygame.Rect] = field(default_factory=dict)
    submit_rect: Optional[pygame.Rect] = None
    clear_rect: Optional[pygame.Rect] = None

    # Re-slot animation states
    reslot_timer: int = 0
    reslot_message: str = ""
    reslot_moved_skus: set[str] = field(default_factory=set)
    # optional UI widgets for manual mode
    sliders: list = field(default_factory=list)
    
    def add_to_cart(self, sku: SKUInfo):
        if len(self.custom_cart) < 15:
            self.custom_cart.append(sku)
            
    def clear_cart(self):
        self.custom_cart.clear()

"""
Advanced Pygame renderer for Dark Store UI with interactive elements.
"""
import pygame
import pygame.gfxdraw
import numpy as np
import math
from project.warehouse.layout import WarehouseLayout
from project.warehouse.inventory import InventoryManager, SKUInfo
from project.simulation.picker import Picker, PickerState
from project.simulation.congestion import CongestionManager
from project.simulation.heatmap import HeatmapManager
from project.simulation.orders import OrderManager
from project.algorithms.forecasting import DemandForecaster
from project.algorithms.slotting import SlottingEngine
from project.visualization.ui_state import UIState
from project.config import (
    SCREEN_WIDTH, SCREEN_HEIGHT, TILE_SIZE, PADDING, SIDEBAR_WIDTH, LEFT_PANEL_WIDTH,
    CELL_AISLE, CELL_SHELF, CELL_PACKING, CELL_DISPATCH
)
from project.visualization.colors import (
    BG_PRIMARY, BG_SECONDARY, CELL_AISLE_COLOR, CELL_SHELF_COLOR, CELL_SHELF_BORDER,
    CELL_PACKING_COLOR, CELL_DISPATCH_COLOR, GRID_LINE_COLOR,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_HEADER, ITEM_IN_ORDER,
    ITEM_CLASS_A, ITEM_CLASS_B, ITEM_CLASS_C, HEATMAP_GRADIENT,
    DIVIDER, ITEM_DEFAULT
)

def draw_dashed_line(surface, color, start_pos, end_pos, width=1, dash_length=4):
    x1, y1 = start_pos
    x2, y2 = end_pos
    dl = dash_length
    if y1 == y2:
        for x in range(int(x1), int(x2), dl * 2):
            pygame.draw.line(surface, color, (x, y1), (min(x + dl, x2), y1), width)

def draw_tag_icon(surface, color, ix, iy):
    pygame.draw.polygon(surface, color, [
        (ix - 5, iy - 1), (ix - 1, iy - 5), (ix + 5, iy - 5), (ix + 5, iy + 3), (ix - 5, iy + 3)
    ], 1)
    pygame.draw.circle(surface, color, (ix + 2, iy - 2), 1)

def draw_gauge_icon(surface, color, ix, iy):
    pygame.draw.arc(surface, color, (ix - 6, iy - 4, 12, 12), 0, math.pi, 1)
    pygame.draw.line(surface, color, (ix - 6, iy + 2), (ix + 6, iy + 2), 1)
    pygame.draw.line(surface, color, (ix, iy + 2), (ix + 2, iy - 2), 1)

def draw_box_icon(surface, color, ix, iy):
    pygame.draw.polygon(surface, color, [
        (ix, iy - 6), (ix + 5, iy - 3), (ix + 5, iy + 3), (ix, iy + 6), (ix - 5, iy + 3), (ix - 5, iy - 3)
    ], 1)
    pygame.draw.line(surface, color, (ix, iy - 6), (ix, iy + 6), 1)
    pygame.draw.line(surface, color, (ix, iy), (ix + 5, iy - 3), 1)
    pygame.draw.line(surface, color, (ix, iy), (ix - 5, iy - 3), 1)

def draw_common_logo(surface, cx, cy, color, bg_color):
    # A beautiful 3D Box (cube) representing inventory products
    pygame.draw.polygon(surface, color, [
        (cx, cy - 10), (cx + 9, cy - 5), (cx + 9, cy + 5), (cx, cy + 10), (cx - 9, cy + 5), (cx - 9, cy - 5)
    ], 2)
    pygame.draw.line(surface, color, (cx, cy - 10), (cx, cy + 10), 2)
    pygame.draw.line(surface, color, (cx, cy), (cx + 9, cy - 5), 2)
    pygame.draw.line(surface, color, (cx, cy), (cx - 9, cy - 5), 2)

class Renderer:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("Quick-Commerce Dark Store Operations Platform")
        self.base_tile_size = TILE_SIZE
        self.base_left_panel_width = LEFT_PANEL_WIDTH
        self.base_sidebar_width = SIDEBAR_WIDTH
        self.base_padding = PADDING
        self.scale = 1.0
        self.ui_scale = 1.0
        self.tile_size = TILE_SIZE
        self.left_panel_width = LEFT_PANEL_WIDTH
        self.sidebar_width = SIDEBAR_WIDTH
        self.padding = PADDING
        self.grid_offset_x = PADDING + LEFT_PANEL_WIDTH + PADDING
        self.grid_offset_y = PADDING
        self.line_height = 20
        self._rebuild_fonts()
        self.show_heatmap = True
        
    def _rebuild_fonts(self):
        tiny_size = max(9, int(11 * self.ui_scale))
        small_size = max(10, int(12 * self.ui_scale))
        normal_size = max(12, int(14 * self.ui_scale))
        large_size = max(14, int(18 * self.ui_scale))
        
        import os
        font_dir = os.path.join("project", "assets", "fonts")
        
        try:
            self.font_heading = pygame.font.Font(os.path.join(font_dir, "Inter-SemiBold.ttf"), large_size)
            self.font_subheading = pygame.font.Font(os.path.join(font_dir, "Inter-SemiBold.ttf"), normal_size)
            self.font_label = pygame.font.Font(os.path.join(font_dir, "Inter-Medium.ttf"), normal_size)
            self.font_bold = pygame.font.Font(os.path.join(font_dir, "Inter-Bold.ttf"), normal_size)
            self.font_regular = pygame.font.Font(os.path.join(font_dir, "Inter-Regular.ttf"), normal_size)
            self.font_tiny = pygame.font.Font(os.path.join(font_dir, "Inter-Regular.ttf"), tiny_size)
            self.font_small = pygame.font.Font(os.path.join(font_dir, "Inter-Regular.ttf"), small_size)
        except Exception as e:
            print(f"Error loading custom Inter fonts: {e}. Falling back to Arial.")
            self.font_heading = pygame.font.SysFont("Arial", large_size, bold=True)
            self.font_subheading = pygame.font.SysFont("Arial", normal_size, bold=True)
            self.font_label = pygame.font.SysFont("Arial", normal_size, bold=False)
            self.font_bold = pygame.font.SysFont("Arial", normal_size, bold=True)
            self.font_regular = pygame.font.SysFont("Arial", normal_size)
            self.font_tiny = pygame.font.SysFont("Arial", tiny_size)
            self.font_small = pygame.font.SysFont("Arial", small_size)

        # Fallbacks for legacy/base code references:
        self.font = self.font_regular
        self.font_large = self.font_heading
        self.line_height = max(18, int(18 * self.ui_scale))

    def _update_layout(self, layout: WarehouseLayout, win_w: int, win_h: int):
        min_tile = 16
        min_side = 180
        min_sidebar = 240
        target_grid_width = layout.cols * self.base_tile_size
        target_grid_height = layout.rows * self.base_tile_size
        available_width = win_w - (self.base_padding * 4 + self.base_left_panel_width + self.base_sidebar_width)
        available_height = win_h - self.base_padding * 2

        if available_width <= 0 or available_height <= 0:
            self.scale = 0.5
        else:
            self.scale = min(2.5, available_width / target_grid_width, available_height / target_grid_height)
            self.scale = max(0.45, self.scale)

        self.ui_scale = min(1.0, self.scale)
        self.tile_size = max(min_tile, int(self.base_tile_size * self.scale))
        self.left_panel_width = max(min_side, int(self.base_left_panel_width * self.ui_scale))
        self.sidebar_width = max(min_sidebar, int(self.base_sidebar_width * self.ui_scale))
        self.padding = max(8, int(self.base_padding * self.ui_scale))
        self.grid_offset_x = self.padding + self.left_panel_width + self.padding
        self.grid_offset_y = self.padding
        self._rebuild_fonts()

    def _get_heatmap_color(self, value: float) -> tuple:
        if value <= 0: return None
        idx = int(value * (len(HEATMAP_GRADIENT) - 1))
        idx = min(len(HEATMAP_GRADIENT) - 1, max(0, idx))
        return HEATMAP_GRADIENT[idx]

    def _draw_panel(self, rect: pygame.Rect, title: str):
        pygame.draw.rect(self.screen, BG_SECONDARY, rect, border_radius=8)
        title_surf = self.font_large.render(title, True, TEXT_HEADER)
        self.screen.blit(title_surf, (rect.x + 15, rect.y + 15))
        pygame.draw.line(self.screen, DIVIDER, (rect.x + 15, rect.y + 40), (rect.right - 15, rect.y + 40), 1)
        return rect.x + 15, rect.y + 50

    def _draw_card(self, rect: pygame.Rect, title: str, has_icon=False):
        pygame.draw.rect(self.screen, BG_SECONDARY, rect, border_radius=8)
        pygame.draw.rect(self.screen, DIVIDER, rect, width=1, border_radius=8)
        
        tx = rect.x + 15
        if has_icon and title:
            ix = rect.x + 15
            iy = rect.y + 12
            # Draw line graph trend icon
            points = [(ix, iy + 10), (ix + 4, iy + 7), (ix + 8, iy + 11), (ix + 14, iy + 2)]
            pygame.draw.lines(self.screen, (108, 92, 231), False, points, 2)
            for px, py in points:
                pygame.draw.circle(self.screen, (108, 92, 231), (px, py), 2)
            tx += 20
            
        if title:
            title_surf = self.font_subheading.render(title, True, TEXT_HEADER)
            self.screen.blit(title_surf, (tx, rect.y + 10))
        return rect.x + 15, rect.y + 35
        
    def render(self, layout: WarehouseLayout, inventory: InventoryManager, pickers: list[Picker], 
               metrics: dict, order_manager: OrderManager, congestion: CongestionManager, 
               heatmap: HeatmapManager, forecaster: DemandForecaster, slotting: SlottingEngine, 
               demo_mode: bool, ui_state: UIState):
        self.screen.fill(BG_PRIMARY)
        
        win_w, win_h = self.screen.get_size()
        self._update_layout(layout, win_w, win_h)
        
        grid_offset_x = self.grid_offset_x
        grid_offset_y = self.grid_offset_y
        
        # 1. Draw Grid
        heatmap_data = heatmap.get_normalized_heatmap()
        
        for r in range(layout.rows):
            for c in range(layout.cols):
                rect = pygame.Rect(c * self.tile_size + grid_offset_x, r * self.tile_size + grid_offset_y, self.tile_size, self.tile_size)
                cell_type = layout.get_cell_type(r, c)
                
                if cell_type == CELL_SHELF:
                    shelf_rect = rect.inflate(-4, -4)
                    pygame.draw.rect(self.screen, CELL_SHELF_COLOR, shelf_rect)
                    pygame.draw.rect(self.screen, CELL_SHELF_BORDER, shelf_rect, 1)
                elif cell_type == CELL_PACKING:
                    pygame.draw.rect(self.screen, CELL_PACKING_COLOR, rect)
                elif cell_type == CELL_DISPATCH:
                    pygame.draw.rect(self.screen, CELL_DISPATCH_COLOR, rect)
                else:
                    pygame.draw.rect(self.screen, CELL_AISLE_COLOR, rect)
                    pygame.draw.rect(self.screen, GRID_LINE_COLOR, rect, 1)
                    
                    if self.show_heatmap:
                        h_color = self._get_heatmap_color(heatmap_data[r, c])
                        if h_color:
                            s = pygame.Surface((self.tile_size, self.tile_size))
                            s.set_alpha(100) # softer blend
                            s.fill(h_color)
                            self.screen.blit(s, (rect.x, rect.y))

        # 2. Draw Inventory on Grid
        hovered_sku_info = None
        for sku in inventory.get_all_skus():
            if sku.location:
                r, c = sku.location
                rect = pygame.Rect(c * self.tile_size + grid_offset_x + 3, r * self.tile_size + grid_offset_y + 3, self.tile_size - 6, self.tile_size - 6)
                
                if sku.abc_class == "A": color = ITEM_CLASS_A
                elif sku.abc_class == "B": color = ITEM_CLASS_B
                else: color = ITEM_CLASS_C
                
                if ui_state.reslot_timer > 0 and sku.sku_id in ui_state.reslot_moved_skus:
                    if (ui_state.reslot_timer // 10) % 2 == 0:
                        color = (255, 255, 255)
                        rect.inflate_ip(4, 4)
                        
                pygame.draw.rect(self.screen, color, rect, border_radius=3)
                
                name = sku.product_name[:3]
                name_surf = self.font_tiny.render(name, True, (255, 255, 255))
                name_rect = name_surf.get_rect(center=rect.center)
                self.screen.blit(name_surf, name_rect)
                
                if ui_state.hovered_cell == (r, c):
                    hovered_sku_info = sku

        # 3. Draw Active Pickers
        for picker in pickers:
            if picker.state == PickerState.PICKING and picker.active_order:
                for item in picker.active_order.items:
                    if item.location:
                        r, c = item.location
                        rect = pygame.Rect(c * self.tile_size + grid_offset_x, r * self.tile_size + grid_offset_y, self.tile_size, self.tile_size)
                        pygame.draw.rect(self.screen, ITEM_IN_ORDER, rect, 2, border_radius=2)
                    
                if len(picker.full_path_cells) > 1:
                    remaining_path = picker.full_path_cells[picker.path_index:]
                    points = [(c * self.tile_size + grid_offset_x + self.tile_size // 2, r * self.tile_size + grid_offset_y + self.tile_size // 2) for r, c in remaining_path]
                    if points:
                        points.insert(0, (int(picker.pixel_x), int(picker.pixel_y)))
                    if len(points) > 1:
                        pygame.draw.lines(self.screen, picker.color, False, points, max(2, int(4 * self.scale)))

            # Draw fading trails
            if len(picker.trail) > 1:
                for i, (tgx, tgy) in enumerate(picker.trail):
                    if i % 3 == 0:
                        tx = tgx * self.tile_size + grid_offset_x + self.tile_size // 2
                        ty = tgy * self.tile_size + grid_offset_y + self.tile_size // 2
                        rad = max(1, int(6 * (i / len(picker.trail))))
                        pygame.draw.circle(self.screen, picker.color, (int(tx), int(ty)), rad)

            px = int(picker.pixel_x)
            py = int(picker.pixel_y)
            
            pygame.draw.circle(self.screen, picker.color, (px, py), 10)
            p_id_surf = self.font_tiny.render(str(picker.id), True, (255, 255, 255))
            p_id_rect = p_id_surf.get_rect(center=(px, py))
            self.screen.blit(p_id_surf, p_id_rect)

        # 4. LEFT PANEL: Product Catalog & Custom Cart Builder
        if not demo_mode:
            left_rect = pygame.Rect(self.padding, self.padding, self.left_panel_width, self.screen.get_height() - self.padding * 2)
            lx, ly = self._draw_panel(left_rect, "Cart Builder & Catalog")
            
            btn_height = max(28, int(26 * self.ui_scale))
            total_height = left_rect.bottom - btn_height - 20 - ly
            list_height = (total_height - (2 * self.line_height + 30)) // 2

            # Catalog list
            catalog_surf = self.font_subheading.render("Available Products:", True, TEXT_HEADER)
            self.screen.blit(catalog_surf, (lx, ly))
            ly += self.line_height + 5
            
            # Setup a clipping rect for scrollable area
            clip_rect = pygame.Rect(lx, ly, self.left_panel_width - 20, list_height)
            self.screen.set_clip(clip_rect)
            
            ui_state.catalog_rects.clear()
            scroll_offset = ui_state.catalog_scroll_y
            
            # Get unique catalog items for display to not clutter with duplicates
            seen_names = set()
            unique_skus = []
            for s in inventory.get_all_skus():
                if s.product_name not in seen_names:
                    unique_skus.append(s)
                    seen_names.add(s.product_name)
            
            for sku in unique_skus:
                item_rect = pygame.Rect(lx, ly - scroll_offset, self.left_panel_width - 30, max(18, int(18 * self.ui_scale)))
                
                if item_rect.bottom > clip_rect.top and item_rect.top < clip_rect.bottom:
                    pygame.draw.rect(self.screen, BG_PRIMARY, item_rect, border_radius=4)
                    cat_color = ITEM_CLASS_A if sku.abc_class == "A" else ITEM_CLASS_B if sku.abc_class == "B" else ITEM_CLASS_C
                    pygame.draw.circle(self.screen, cat_color, (lx + 10, item_rect.centery), 4)
                    
                    text = f"{sku.product_name[:12]} | {sku.category[:8]} | v:{int(sku.velocity)}"
                    surf = self.font_small.render(text, True, TEXT_PRIMARY)
                    self.screen.blit(surf, (lx + 20, item_rect.y + 3))
                    
                ui_state.catalog_rects[sku.sku_id] = item_rect
                ly += 24
                
            self.screen.set_clip(None)
            ly = clip_rect.bottom + 10
            
            # Custom Cart
            pygame.draw.line(self.screen, DIVIDER, (lx, ly), (left_rect.right - 15, ly), 1)
            ly += 10
            cart_surf = self.font_subheading.render(f"Current Cart ({len(ui_state.custom_cart)} items):", True, TEXT_HEADER)
            self.screen.blit(cart_surf, (lx, ly))
            ly += self.line_height + 5
            
            cart_clip_rect = pygame.Rect(lx, ly, self.left_panel_width - 20, list_height)
            self.screen.set_clip(cart_clip_rect)
            
            cy = ly
            for item in ui_state.custom_cart:
                surf = self.font_small.render(f"- {item.product_name}", True, TEXT_SECONDARY)
                self.screen.blit(surf, (lx + 10, cy))
                cy += max(16, int(16 * self.ui_scale))
                
            self.screen.set_clip(None)
                
            # Buttons
            btn_height = max(28, int(26 * self.ui_scale))
            btn_width = max(100, int(100 * self.ui_scale))
            submit_rect = pygame.Rect(lx, left_rect.bottom - btn_height - 10, btn_width, btn_height)
            pygame.draw.rect(self.screen, ITEM_CLASS_A, submit_rect, border_radius=4)
            sub_text = self.font.render("Submit Order", True, (255, 255, 255))
            self.screen.blit(sub_text, (submit_rect.x + 10, submit_rect.y + (btn_height - self.font.get_height()) // 2))
            ui_state.submit_rect = submit_rect
            
            clear_rect = pygame.Rect(submit_rect.right + max(10, int(10 * self.ui_scale)), submit_rect.y, max(80, int(80 * self.ui_scale)), btn_height)
            pygame.draw.rect(self.screen, ITEM_DEFAULT, clear_rect, border_radius=4)
            clr_text = self.font.render("Clear", True, (255, 255, 255))
            self.screen.blit(clr_text, (clear_rect.x + (clear_rect.width - clr_text.get_width()) // 2, clear_rect.y + (btn_height - clr_text.get_height()) // 2))
            ui_state.clear_rect = clear_rect

        # 5. RIGHT PANEL: Dark Store Operations Dashboard (Card-based layout)
        import math
        grid_pixel_width = layout.cols * self.tile_size
        right_x = grid_offset_x + grid_pixel_width + self.padding
        
        # Calculate dynamic gap between cards based on available height and heights of cards
        available_height = self.screen.get_height() - self.padding * 2
        
        # Base heights
        h_sliders_base = 240 if not demo_mode else 70
        h_stats_base = 115
        h_kpis_base = 105
        
        orders_to_show = order_manager.active_orders[:2] + order_manager.pending_orders[:2]
        if not orders_to_show:
            h_orders_base = 55
        else:
            h_orders_base = 42 + len(orders_to_show[:3]) * 15
            
        h_fleet_base = 80
        h_opt_base = 65
        h_controls_base = 80
        
        sum_base = h_sliders_base + h_stats_base + h_kpis_base + h_orders_base + h_fleet_base + h_opt_base + h_controls_base
        
        # Responsive scaling factor k and card gap
        if available_height > sum_base + 60: # 60px is 6 gaps of 10px
            card_gap = 10
            k = (available_height - 60) / sum_base
            k = min(1.5, k) # Cap to avoid oversized text spacing
        else:
            k = 1.0
            card_gap = max(4, (available_height - sum_base) // 6)
            
        # Compute scaled heights
        h_sliders = int(h_sliders_base * k)
        h_stats = int(h_stats_base * k)
        h_kpis = int(h_kpis_base * k)
        h_orders = int(h_orders_base * k)
        h_fleet = int(h_fleet_base * k)
        h_opt = int(h_opt_base * k)
        h_controls = int(h_controls_base * k)
        
        ry = self.padding

        # --- Card 1: Sliders ---
        card1_rect = pygame.Rect(right_x, ry, self.sidebar_width, h_sliders)
        cx, cy = self._draw_card(card1_rect, "Operations Dashboard", has_icon=True)
        
        if not demo_mode:
            # Draw divider line above footer
            pygame.draw.line(self.screen, DIVIDER, 
                             (card1_rect.x + 15, card1_rect.bottom - int(28 * k)), 
                             (card1_rect.right - 15, card1_rect.bottom - int(28 * k)), 1)
            
            mode_y = card1_rect.bottom - int(22 * k)
            mode_text = f"Mode: {'DEMO PRESENTATION' if demo_mode else 'MANUAL'}  |  Time: {order_manager.time_of_day}"
            mode_color = (39, 174, 96) if demo_mode else TEXT_SECONDARY
            mode_surf = self.font_regular.render(mode_text, True, mode_color)
            self.screen.blit(mode_surf, (cx, mode_y))
            
            # Draw weather/sun icon based on time of day
            tod = order_manager.time_of_day.lower()
            sx = card1_rect.right - 25
            sy = mode_y + mode_surf.get_height() // 2
            if "morning" in tod or "afternoon" in tod:
                pygame.draw.circle(self.screen, (243, 156, 18), (sx, sy), 5, width=2)
                for angle in range(0, 360, 45):
                    rad = math.radians(angle)
                    pygame.draw.line(self.screen, (243, 156, 18), 
                                     (sx + 7 * math.cos(rad), sy + 7 * math.sin(rad)), 
                                     (sx + 10 * math.cos(rad), sy + 10 * math.sin(rad)), 2)
            else:
                pygame.draw.circle(self.screen, (127, 140, 141), (sx, sy), 5, width=2)
                pygame.draw.circle(self.screen, BG_SECONDARY, (sx - 2, sy - 2), 5)
        else:
            mode_y = card1_rect.y + int(35 * k)
            mode_text = "Mode: DEMO PRESENTATION"
            mode_surf = self.font_regular.render(mode_text, True, (39, 174, 96))
            self.screen.blit(mode_surf, (cx, mode_y))

        ry += h_sliders + card_gap

        # --- Card 2: Warehouse Stats ---
        card2_rect = pygame.Rect(right_x, ry, self.sidebar_width, h_stats)
        cx, cy = self._draw_card(card2_rect, "Warehouse Stats")
        
        col1_x = cx
        col2_x = right_x + self.sidebar_width // 2 + 10
        
        num_skus = len(inventory.get_all_skus())
        num_shelves = len(layout.get_shelf_cells())
        utilization = (num_skus / num_shelves * 100) if num_shelves > 0 else 0
        unique_catalog = len(set([s.product_name for s in inventory.get_all_skus()]))
        
        # Row 1, Column 1: Shelf Utilization
        lbl = self.font_label.render("Shelf Utilization", True, TEXT_SECONDARY)
        self.screen.blit(lbl, (col1_x, card2_rect.y + int(30 * k)))
        val = self.font_bold.render(f"{utilization:.1f}%", True, (41, 128, 185))
        self.screen.blit(val, (col1_x, card2_rect.y + int(46 * k)))
        
        # Row 1, Column 2: Catalog Size
        lbl = self.font_label.render("Catalog Size", True, TEXT_SECONDARY)
        self.screen.blit(lbl, (col2_x, card2_rect.y + int(30 * k)))
        val = self.font_bold.render(str(unique_catalog), True, TEXT_PRIMARY)
        self.screen.blit(val, (col2_x, card2_rect.y + int(46 * k)))
        sfx = self.font_small.render("distinct products", True, TEXT_SECONDARY)
        self.screen.blit(sfx, (col2_x, card2_rect.y + int(62 * k)))
        
        # Row 2, Column 1: Total Physical Units
        lbl = self.font_label.render("Total Physical Units", True, TEXT_SECONDARY)
        self.screen.blit(lbl, (col1_x, card2_rect.y + int(78 * k)))
        val = self.font_bold.render(str(num_skus), True, TEXT_PRIMARY)
        self.screen.blit(val, (col1_x, card2_rect.y + int(94 * k)))
        
        # Row 2, Column 2: Active Pickers
        lbl = self.font_label.render("Active Pickers", True, TEXT_SECONDARY)
        self.screen.blit(lbl, (col2_x, card2_rect.y + int(78 * k)))
        active_pickers = sum(1 for p in pickers if p.state != PickerState.IDLE)
        val = self.font_bold.render(f"{active_pickers}/{len(pickers)}", True, TEXT_PRIMARY)
        self.screen.blit(val, (col2_x, card2_rect.y + int(94 * k)))

        ry += h_stats + card_gap

        # --- Card 3: Live KPIs ---
        card3_rect = pygame.Rect(right_x, ry, self.sidebar_width, h_kpis)
        cx, cy = self._draw_card(card3_rect, "Live KPIs")
        
        om_metrics = order_manager.get_metrics()
        acc = forecaster.get_average_accuracy()
        acc_color = (39, 174, 96) if acc > 80 else (241, 196, 15) if acc > 50 else (211, 47, 47)
        
        # Row 1, Column 1: Queue Size
        lbl = self.font_label.render("Queue Size", True, TEXT_SECONDARY)
        self.screen.blit(lbl, (col1_x, card3_rect.y + int(30 * k)))
        val = self.font_bold.render(str(om_metrics['pending']), True, TEXT_PRIMARY)
        self.screen.blit(val, (col1_x, card3_rect.y + int(44 * k)))
        
        # Row 1, Column 2: Completed Orders
        lbl = self.font_label.render("Completed Orders", True, TEXT_SECONDARY)
        self.screen.blit(lbl, (col2_x, card3_rect.y + int(30 * k)))
        val = self.font_bold.render(str(om_metrics['completed']), True, TEXT_PRIMARY)
        self.screen.blit(val, (col2_x, card3_rect.y + int(44 * k)))
        
        # Row 2, Column 1: Avg Fulfillment
        lbl = self.font_label.render("Avg Fulfillment", True, TEXT_SECONDARY)
        self.screen.blit(lbl, (col1_x, card3_rect.y + int(60 * k)))
        val_surf = self.font_bold.render(f"{om_metrics['avg_fulfillment_time']:.1f}", True, TEXT_PRIMARY)
        self.screen.blit(val_surf, (col1_x, card3_rect.y + int(74 * k)))
        sfx_surf = self.font_regular.render(" ticks", True, TEXT_SECONDARY)
        self.screen.blit(sfx_surf, (col1_x + val_surf.get_width(), card3_rect.y + int(74 * k) + (val_surf.get_height() - sfx_surf.get_height()) // 2))
        
        # Row 2, Column 2: Forecast Accuracy
        lbl = self.font_label.render("Forecast Accuracy", True, TEXT_SECONDARY)
        self.screen.blit(lbl, (col2_x, card3_rect.y + int(60 * k)))
        val = self.font_bold.render(f"{acc:.1f}%", True, acc_color)
        self.screen.blit(val, (col2_x, card3_rect.y + int(74 * k)))

        ry += h_kpis + card_gap

        # --- Card 4: Order Management ---
        card4_rect = pygame.Rect(right_x, ry, self.sidebar_width, h_orders)
        cx, cy = self._draw_card(card4_rect, "Order Management")
        
        if not orders_to_show:
            empty_surf = self.font_regular.render("Queue is empty.", True, TEXT_SECONDARY)
            self.screen.blit(empty_surf, (cx, card4_rect.y + int(32 * k)))
        else:
            for idx, order in enumerate(orders_to_show[:3]):
                items_str = ", ".join([item.product_name for item in order.items[:2]])
                if len(order.items) > 2:
                    items_str += "..."
                if order.picker_id:
                    text = f"#{order.order_id} [P{order.picker_id}]: {items_str}"
                    color = (41, 128, 185)
                else:
                    text = f"#{order.order_id} [Pending]: {items_str}"
                    color = (243, 156, 18)
                order_surf = self.font_small.render(text, True, color)
                self.screen.blit(order_surf, (cx, card4_rect.y + int(32 * k) + idx * int(14 * k)))

        ry += h_orders + card_gap

        # --- Card 5: Picker Status List (No Header) ---
        card5_rect = pygame.Rect(right_x, ry, self.sidebar_width, h_fleet)
        pygame.draw.rect(self.screen, BG_SECONDARY, card5_rect, border_radius=8)
        pygame.draw.rect(self.screen, DIVIDER, card5_rect, width=1, border_radius=8)
        
        # Vertical divider line in the middle
        pygame.draw.line(self.screen, DIVIDER, 
                         (card5_rect.x + self.sidebar_width // 2, card5_rect.y + int(8 * k)), 
                         (card5_rect.x + self.sidebar_width // 2, card5_rect.bottom - int(8 * k)), 1)
        
        col_width = self.sidebar_width // 2
        for idx, picker in enumerate(pickers[:8]):
            col = idx // 4
            row = idx % 4
            px = card5_rect.x + 12 + col * col_width
            py = card5_rect.y + int(8 * k) + row * int(15 * k)
            
            # Colored circle dot (radius 4, anti-aliased)
            pygame.gfxdraw.aacircle(self.screen, px + 5, py + 7, 4, picker.color)
            pygame.gfxdraw.filled_circle(self.screen, px + 5, py + 7, 4, picker.color)
            
            status = "Idle"
            if picker.state == PickerState.PICKING: 
                status = "Picking"
            elif picker.state == PickerState.RETURNING: 
                status = "Returning"
                
            # Render "Picker X:" in picker color
            name_text = f"Picker {picker.id}: "
            name_surf = self.font_small.render(name_text, True, picker.color)
            self.screen.blit(name_surf, (px + 14, py))
            
            # Render status and utilization in gray
            status_text = f"{status} | Util: {picker.get_utilization()*100:.1f}%"
            status_surf = self.font_small.render(status_text, True, TEXT_SECONDARY)
            self.screen.blit(status_surf, (px + 14 + name_surf.get_width(), py))

        ry += h_fleet + card_gap

        # --- Card 6: Warehouse Optimization ---
        card6_rect = pygame.Rect(right_x, ry, self.sidebar_width, h_opt)
        cx, cy = self._draw_card(card6_rect, "Warehouse Optimization")
        
        strategy = metrics.get('strategy', 'Greedy')
        dist = metrics.get('avg_storage_distance', 0.0)
        
        # Column 1: Active Strategy
        strat_lbl = self.font_label.render("Active Strategy", True, TEXT_SECONDARY)
        self.screen.blit(strat_lbl, (cx, card6_rect.y + int(26 * k)))
        strat_val = self.font_bold.render(strategy, True, (108, 92, 231))
        self.screen.blit(strat_val, (cx, card6_rect.y + int(40 * k)))
        
        # Column 2: Storage Distance
        dist_lbl = self.font_label.render("Storage Distance", True, TEXT_SECONDARY)
        self.screen.blit(dist_lbl, (col2_x, card6_rect.y + int(26 * k)))
        
        dist_val_str = f"{dist:.1f}"
        dist_surf = self.font_bold.render(dist_val_str, True, TEXT_PRIMARY)
        self.screen.blit(dist_surf, (col2_x, card6_rect.y + int(40 * k)))
        
        sfx_surf = self.font_regular.render(" steps", True, TEXT_SECONDARY)
        self.screen.blit(sfx_surf, (col2_x + dist_surf.get_width(), card6_rect.y + int(40 * k) + (dist_surf.get_height() - sfx_surf.get_height()) // 2))

        ry += h_opt + card_gap

        # --- Card 7: Controls ---
        card7_rect = pygame.Rect(right_x, ry, self.sidebar_width, h_controls)
        cx, cy = self._draw_card(card7_rect, "Controls")
        
        col1_shortcuts = [
            "[D] Demo Mode",
            "[S] Change Strategy",
            "[H] Toggle Heatmap"
        ]
        col2_shortcuts = [
            "[SPACE] Random Orders",
            "[O] Re-slot",
            "[T] Cycle Time of Day"
        ]
        
        for idx, shortcut in enumerate(col1_shortcuts):
            s_surf = self.font_small.render(shortcut, True, TEXT_SECONDARY)
            self.screen.blit(s_surf, (cx, card7_rect.y + int(26 * k) + idx * 13))
            
        for idx, shortcut in enumerate(col2_shortcuts):
            s_surf = self.font_small.render(shortcut, True, TEXT_SECONDARY)
            self.screen.blit(s_surf, (col2_x, card7_rect.y + int(26 * k) + idx * 13))

        ry += h_controls + card_gap

        # 6. Tooltip Overlay (Drawn last so it's on top)
        if hovered_sku_info:
            mx, my = ui_state.mouse_pos
            tooltip_w = 240
            tooltip_h = 110
            
            tx = mx + 16
            ty = my - 20
            tail_side = "left"
            
            win_w, win_h = self.screen.get_size()
            if tx + tooltip_w > win_w - 15:
                tx = mx - 16 - tooltip_w
                tail_side = "right"
                
            if ty < 15:
                ty = 15
            elif ty + tooltip_h > win_h - 15:
                ty = win_h - 15 - tooltip_h
                
            if tail_side == "left":
                tail_points = [
                    (tx, my - 8),
                    (tx, my + 8),
                    (tx - 12, my)
                ]
                tail_border_lines = [
                    ((tx, my - 8), (tx - 12, my)),
                    ((tx - 12, my), (tx, my + 8))
                ]
            else:
                tail_points = [
                    (tx + tooltip_w, my - 8),
                    (tx + tooltip_w, my + 8),
                    (tx + tooltip_w + 12, my)
                ]
                tail_border_lines = [
                    ((tx + tooltip_w, my - 8), (tx + tooltip_w + 12, my)),
                    ((tx + tooltip_w + 12, my), (tx + tooltip_w, my + 8))
                ]
                
            bg_color = (255, 245, 242)
            border_color = (255, 229, 222)
            icon_bg_color = (255, 235, 230)
            primary_color = (224, 90, 54)  # Terracotta orange
            text_label_color = (90, 90, 90)
            
            # Draw rounded background
            rect = pygame.Rect(tx, ty, tooltip_w, tooltip_h)
            pygame.draw.rect(self.screen, bg_color, rect, border_radius=12)
            
            # Draw filled tail pointer
            pygame.draw.polygon(self.screen, bg_color, tail_points)
            
            # Draw rounded border
            pygame.draw.rect(self.screen, border_color, rect, width=1, border_radius=12)
            
            # Draw tail pointer border lines
            for p_start, p_end in tail_border_lines:
                pygame.draw.line(self.screen, border_color, p_start, p_end, 1)
                
            # Left Icon Box
            ibox_x = tx + 12
            ibox_y = ty + 12
            ibox_w = 44
            ibox_h = 44
            ibox_rect = pygame.Rect(ibox_x, ibox_y, ibox_w, ibox_h)
            pygame.draw.rect(self.screen, icon_bg_color, ibox_rect, border_radius=8)
            
            cx = ibox_x + ibox_w // 2
            cy = ibox_y + ibox_h // 2
            draw_common_logo(self.screen, cx, cy, primary_color, icon_bg_color)
            
            # Product Title
            title_surf = self.font_bold.render(hovered_sku_info.product_name, True, primary_color)
            self.screen.blit(title_surf, (tx + 68, ty + 10))
            
            # Divider Line
            div_y = ty + 32
            draw_dashed_line(self.screen, border_color, (tx + 68, div_y), (tx + tooltip_w - 12, div_y), width=1, dash_length=4)
            
            # Info Rows
            row_x = tx + 68
            row_y_start = ty + 38
            row_spacing = 20
            
            # Row 1: Category
            iy = row_y_start + 6
            draw_tag_icon(self.screen, text_label_color, row_x + 5, iy)
            lbl1 = self.font_small.render("Category: ", True, text_label_color)
            self.screen.blit(lbl1, (row_x + 16, row_y_start))
            val1 = self.font_small.render(hovered_sku_info.category, True, primary_color)
            self.screen.blit(val1, (row_x + 16 + lbl1.get_width(), row_y_start))
            
            # Row 2: Velocity
            row_y = row_y_start + row_spacing
            iy = row_y + 6
            draw_gauge_icon(self.screen, text_label_color, row_x + 5, iy)
            lbl2 = self.font_small.render("Velocity: ", True, text_label_color)
            self.screen.blit(lbl2, (row_x + 16, row_y))
            val2 = self.font_small.render(f"{int(hovered_sku_info.velocity)}", True, primary_color)
            self.screen.blit(val2, (row_x + 16 + lbl2.get_width(), row_y))
            
            # Row 3: Class
            row_y = row_y_start + row_spacing * 2
            iy = row_y + 6
            draw_box_icon(self.screen, text_label_color, row_x + 5, iy)
            lbl3 = self.font_small.render("Class: ", True, text_label_color)
            self.screen.blit(lbl3, (row_x + 16, row_y))
            val3 = self.font_small.render(hovered_sku_info.abc_class, True, primary_color)
            self.screen.blit(val3, (row_x + 16 + lbl3.get_width(), row_y))

        # Render sliders when in manual mode: draw to the right sidebar area if present
        try:
            if not demo_mode and hasattr(ui_state, 'sliders') and ui_state.sliders:
                for s in ui_state.sliders:
                    s.draw(self.screen, self.font_label)
        except Exception:
            pass

        if ui_state.reslot_timer > 0:
            banner_width = max(280, int(360 * self.scale))
            banner_height = max(40, int(48 * self.scale))
            banner_rect = pygame.Rect(self.screen.get_width() // 2 - banner_width // 2, self.padding * 2, banner_width, banner_height)
            pygame.draw.rect(self.screen, ITEM_CLASS_A, banner_rect, border_radius=10)
            pygame.draw.rect(self.screen, (255, 255, 255), banner_rect, width=2, border_radius=10)
            surf = self.font_large.render(ui_state.reslot_message, True, (255, 255, 255))
            self.screen.blit(surf, surf.get_rect(center=banner_rect.center))

        pygame.display.flip()

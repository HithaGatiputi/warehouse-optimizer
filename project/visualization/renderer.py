"""
Advanced Pygame renderer for Dark Store UI with interactive elements.
"""
import pygame
import numpy as np
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
    ITEM_CLASS_A, ITEM_CLASS_B, ITEM_CLASS_C, HEATMAP_GRADIENT
)

class Renderer:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((500,500), pygame.RESIZABLE)
        pygame.display.set_caption("Quick-Commerce Dark Store Operations Platform")
        self.base_tile_size = TILE_SIZE
        self.base_left_panel_width = LEFT_PANEL_WIDTH
        self.base_sidebar_width = SIDEBAR_WIDTH
        self.base_padding = PADDING
        self.scale = 1.0
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
        tiny_size = max(9, int(11 * self.scale))
        small_size = max(10, int(12 * self.scale))
        normal_size = max(12, int(14 * self.scale))
        large_size = max(14, int(18 * self.scale))
        self.font_tiny = pygame.font.SysFont("Arial", tiny_size)
        self.font_small = pygame.font.SysFont("Arial", small_size)
        self.font = pygame.font.SysFont("Arial", normal_size)
        self.font_large = pygame.font.SysFont("Arial", large_size, bold=True)
        self.line_height = max(18, int(18 * self.scale))

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
            self.scale = min(1.0, available_width / target_grid_width, available_height / target_grid_height)
            self.scale = max(0.45, self.scale)

        self.tile_size = max(min_tile, int(self.base_tile_size * self.scale))
        self.left_panel_width = max(min_side, int(self.base_left_panel_width * self.scale))
        self.sidebar_width = max(min_sidebar, int(self.base_sidebar_width * self.scale))
        self.padding = max(8, int(self.base_padding * self.scale))
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
        pygame.draw.line(self.screen, (60, 60, 75), (rect.x + 15, rect.y + 40), (rect.right - 15, rect.y + 40), 1)
        return rect.x + 15, rect.y + 50
        
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
            if picker.state != PickerState.IDLE and picker.active_order:
                for item in picker.active_order.items:
                    if item.location:
                        r, c = item.location
                        rect = pygame.Rect(c * self.tile_size + grid_offset_x, r * self.tile_size + grid_offset_y, self.tile_size, self.tile_size)
                        pygame.draw.rect(self.screen, ITEM_IN_ORDER, rect, 2, border_radius=2)
                    
                if len(picker.full_path_cells) > 1:
                    points = [(c * self.tile_size + grid_offset_x + self.tile_size // 2, r * self.tile_size + grid_offset_y + self.tile_size // 2) for r, c in picker.full_path_cells]
                    pygame.draw.lines(self.screen, picker.color, False, points, max(2, int(4 * self.scale)))

            # Draw fading trails
            if len(picker.trail) > 1:
                for i, (tx, ty) in enumerate(picker.trail):
                    if i % 3 == 0:
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
            
            # Catalog list
            catalog_surf = self.font.render("Available Products:", True, TEXT_HEADER)
            self.screen.blit(catalog_surf, (lx, ly))
            ly += self.line_height + 5
            
            # Setup a clipping rect for scrollable area
            clip_rect = pygame.Rect(lx, ly, self.left_panel_width - 20, int(220 * self.scale))
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
                item_rect = pygame.Rect(lx, ly - scroll_offset, self.left_panel_width - 30, max(18, int(18 * self.scale)))
                
                if item_rect.bottom > clip_rect.top and item_rect.top < clip_rect.bottom:
                    pygame.draw.rect(self.screen, (50, 50, 60), item_rect, border_radius=4)
                    cat_color = ITEM_CLASS_A if sku.abc_class == "A" else ITEM_CLASS_B if sku.abc_class == "B" else ITEM_CLASS_C
                    pygame.draw.circle(self.screen, cat_color, (lx + 10, item_rect.centery), 4)
                    
                    text = f"{sku.product_name[:12]} | {sku.category[:8]} | v:{int(sku.velocity)}"
                    surf = self.font_small.render(text, True, TEXT_PRIMARY)
                    self.screen.blit(surf, (lx + 20, item_rect.y + 3))
                    
                ui_state.catalog_rects[sku.sku_id] = item_rect
                ly += 24
                
            self.screen.set_clip(None)
            ly = clip_rect.bottom + int(15 * self.scale)
            
            # Custom Cart
            pygame.draw.line(self.screen, (60, 60, 75), (lx, ly), (left_rect.right - 15, ly), 1)
            ly += 15
            cart_surf = self.font.render(f"Current Cart ({len(ui_state.custom_cart)} items):", True, TEXT_HEADER)
            self.screen.blit(cart_surf, (lx, ly))
            ly += self.line_height + 5
            
            for item in ui_state.custom_cart[-10:]:
                surf = self.font_small.render(f"- {item.product_name}", True, TEXT_SECONDARY)
                self.screen.blit(surf, (lx + 10, ly))
                ly += max(16, int(16 * self.scale))
                
            # Buttons
            btn_height = max(28, int(26 * self.scale))
            btn_width = max(100, int(100 * self.scale))
            submit_rect = pygame.Rect(lx, left_rect.bottom - btn_height - 10, btn_width, btn_height)
            pygame.draw.rect(self.screen, (46, 204, 113), submit_rect, border_radius=4)
            sub_text = self.font.render("Submit Order", True, (0, 0, 0))
            self.screen.blit(sub_text, (submit_rect.x + 10, submit_rect.y + (btn_height - self.font.get_height()) // 2))
            ui_state.submit_rect = submit_rect
            
            clear_rect = pygame.Rect(submit_rect.right + max(10, int(10 * self.scale)), submit_rect.y, max(80, int(80 * self.scale)), btn_height)
            pygame.draw.rect(self.screen, (231, 76, 60), clear_rect, border_radius=4)
            clr_text = self.font.render("Clear", True, (255, 255, 255))
            self.screen.blit(clr_text, (clear_rect.x + (clear_rect.width - clr_text.get_width()) // 2, clear_rect.y + (btn_height - clr_text.get_height()) // 2))
            ui_state.clear_rect = clear_rect

        # 5. RIGHT PANEL: Dark Store Operations Dashboard
        grid_pixel_width = layout.cols * self.tile_size
        right_x = grid_offset_x + grid_pixel_width + self.padding
        right_rect = pygame.Rect(right_x, self.padding, self.sidebar_width, self.screen.get_height() - self.padding * 2)
        rx, ry = self._draw_panel(right_rect, "Operations Dashboard")
        
        footer_top = right_rect.bottom - max(90, int(80 * self.scale))
        def draw_text(text, color, bold=False, allow_overflow=False):
            nonlocal ry
            if ry + self.line_height > footer_top and not allow_overflow:
                return False
            f = self.font_large if bold else self.font
            surf = f.render(text, True, color)
            self.screen.blit(surf, (rx, ry))
            ry += self.line_height
            return True

        draw_text(f"Mode: {'DEMO PRESENTATION' if demo_mode else 'MANUAL'} | Time: {order_manager.time_of_day}", (46, 204, 113) if demo_mode else TEXT_SECONDARY)
        ry += max(8, int(8 * self.scale))
        
        # Warehouse Stats
        num_skus = len(inventory.get_all_skus())
        num_shelves = len(layout.get_shelf_cells())
        utilization = (num_skus / num_shelves * 100) if num_shelves > 0 else 0
        unique_catalog = len(set([s.product_name for s in inventory.get_all_skus()]))
        
        draw_text("Warehouse Stats", TEXT_HEADER, True)
        draw_text(f"Shelf Utilization: {utilization:.1f}%", TEXT_PRIMARY)
        draw_text(f"Catalog Size: {unique_catalog} distinct products", TEXT_PRIMARY)
        draw_text(f"Total Physical Units: {num_skus}", TEXT_PRIMARY)
        draw_text(f"Active Pickers: {sum(1 for p in pickers if p.state != PickerState.IDLE)}/{len(pickers)}", TEXT_PRIMARY)
        ry += 10
        
        # KPIs
        om_metrics = order_manager.get_metrics()
        draw_text("Live KPIs", TEXT_HEADER, True)
        draw_text(f"Queue Size: {om_metrics['pending']}", TEXT_PRIMARY)
        draw_text(f"Completed Orders: {om_metrics['completed']}", TEXT_PRIMARY)
        draw_text(f"Avg Fulfillment: {om_metrics['avg_fulfillment_time']:.1f} ticks", TEXT_PRIMARY)
        
        acc = forecaster.get_average_accuracy()
        acc_color = (46, 204, 113) if acc > 80 else (241, 196, 15) if acc > 50 else (231, 76, 60)
        draw_text(f"Forecast Accuracy: {acc:.1f}%", acc_color)
        ry += 10

        # Orders Queue
        draw_text("Order Management", TEXT_HEADER, True)
        for order in order_manager.active_orders[:3]:
            items_str = ", ".join([item.product_name for item in order.items[:3]])
            draw_text(f"#{order.order_id} [Picking by P{order.picker_id}]: {items_str}", (52, 152, 219)) # Blue
            
        for order in order_manager.pending_orders[:4]:
            items_str = ", ".join([item.product_name for item in order.items[:3]])
            draw_text(f"#{order.order_id} [Pending]: {items_str}", (241, 196, 15)) # Yellow
            
        if not order_manager.active_orders and not order_manager.pending_orders:
            draw_text("Queue is empty.", TEXT_SECONDARY)
        ry += 10

        # Pickers
        draw_text("Picker Fleet", TEXT_HEADER, True)
        for picker in pickers:
            status = "Idle"
            if picker.state == PickerState.PICKING: status = f"Picking #{picker.active_order.order_id}"
            elif picker.state == PickerState.RETURNING: status = "Returning"
            draw_text(f"Picker {picker.id}: {status} | Util: {picker.get_utilization()*100:.1f}%", picker.color)
        ry += 10

        # Optimization Status
        draw_text("Warehouse Opt.", TEXT_HEADER, True)
        draw_text(f"Active Strategy: {metrics.get('strategy', 'Greedy')}", TEXT_PRIMARY)
        draw_text(f"Storage Dist: {metrics.get('avg_storage_distance', 0.0):.1f} steps", TEXT_PRIMARY)
        
        # Controls footer
        ry = right_rect.bottom - max(90, int(80 * self.scale))
        draw_text("Controls", TEXT_HEADER, True, allow_overflow=True)
        draw_text("[D] Demo Mode | [SPACE] Random Orders", TEXT_SECONDARY, allow_overflow=True)
        draw_text("[S] Change Strategy | [O] Re-slot", TEXT_SECONDARY, allow_overflow=True)
        draw_text("[H] Toggle Heatmap | [T] Cycle Time of Day", TEXT_SECONDARY, allow_overflow=True)

        # 6. Tooltip Overlay (Drawn last so it's on top)
        if hovered_sku_info:
            mx, my = ui_state.mouse_pos
            tooltip_rect = pygame.Rect(mx + 15, my + 15, 160, 90)
            pygame.draw.rect(self.screen, (30, 30, 35), tooltip_rect, border_radius=6)
            pygame.draw.rect(self.screen, (80, 80, 90), tooltip_rect, width=1, border_radius=6)
            
            tx, ty = tooltip_rect.x + 10, tooltip_rect.y + 10
            surf = self.font_large.render(hovered_sku_info.product_name, True, (255, 255, 255))
            self.screen.blit(surf, (tx, ty))
            ty += 22
            surf = self.font.render(f"Category: {hovered_sku_info.category}", True, TEXT_SECONDARY)
            self.screen.blit(surf, (tx, ty))
            ty += 18
            surf = self.font.render(f"Velocity: {int(hovered_sku_info.velocity)}", True, TEXT_SECONDARY)
            self.screen.blit(surf, (tx, ty))
            ty += 18
            
            c_color = ITEM_CLASS_A if hovered_sku_info.abc_class == "A" else ITEM_CLASS_B if hovered_sku_info.abc_class == "B" else ITEM_CLASS_C
            surf = self.font.render(f"Class: {hovered_sku_info.abc_class}", True, c_color)
            self.screen.blit(surf, (tx, ty))

        if ui_state.reslot_timer > 0:
            banner_width = max(280, int(360 * self.scale))
            banner_height = max(40, int(48 * self.scale))
            banner_rect = pygame.Rect(self.screen.get_width() // 2 - banner_width // 2, self.padding * 2, banner_width, banner_height)
            pygame.draw.rect(self.screen, (46, 204, 113), banner_rect, border_radius=10)
            pygame.draw.rect(self.screen, (255, 255, 255), banner_rect, width=2, border_radius=10)
            surf = self.font_large.render(ui_state.reslot_message, True, (0, 0, 0))
            self.screen.blit(surf, surf.get_rect(center=banner_rect.center))

        pygame.display.flip()

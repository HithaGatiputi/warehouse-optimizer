import pygame
import numpy as np
import random
import sys
import time

# --- CONFIGURATION & CONSTANTS ---
GRID_ROWS = 10
GRID_COLS = 15
TILE_SIZE = 40
PADDING = 20
INFO_PANEL_HEIGHT = 100

SCREEN_WIDTH = GRID_COLS * TILE_SIZE + (PADDING * 2)
SCREEN_HEIGHT = GRID_ROWS * TILE_SIZE + (PADDING * 2) + INFO_PANEL_HEIGHT

# Colors (RGB)
COLOR_BACKGROUND = (245, 247, 250)
COLOR_AISLE = (255, 255, 255)
COLOR_WALL = (200, 207, 214)
COLOR_PACKING = (46, 204, 113)      # Green
COLOR_ITEM_NORMAL = (52, 152, 219)   # Blue
COLOR_ITEM_HOT = (231, 76, 60)       # Red (High demand)
COLOR_PICKER = (155, 89, 182)       # Purple
COLOR_PATH = (241, 196, 15)         # Yellow line
COLOR_TEXT = (44, 62, 80)

# Layout: 0 = Aisle, 1 = Shelf/Rack, 2 = Packing Station
WAREHOUSE_MAP = np.zeros((GRID_ROWS, GRID_COLS), dtype=int)
# Design standard warehouse aisles (alternating columns of shelves)
for c in range(1, GRID_COLS - 1):
    if c % 3 != 0:
        for r in range(1, GRID_ROWS - 1):
            WAREHOUSE_MAP[r, c] = 1

# Place packing station at bottom-left corner
PACKING_STATION = (GRID_ROWS - 1, 0)
WAREHOUSE_MAP[PACKING_STATION] = 2

# --- DATA STRUCTURES & DATA GENERATION ---
# Initialize 40 distinct items/SKUs
SKUs = [f"SKU_{i:02d}" for i in range(40)]
sku_to_coords = {}
coords_to_sku = {}

# Assign SKUs to shelf spaces initially
shelf_cells = [(r, c) for r in range(GRID_ROWS) for c in range(GRID_COLS) if WAREHOUSE_MAP[r, c] == 1]
random.shuffle(shelf_cells)

for idx, sku in enumerate(SKUs):
    if idx < len(shelf_cells):
        cell = shelf_cells[idx]
        sku_to_coords[sku] = cell
        coords_to_sku[cell] = sku

# Initialize Item Velocities (Demand Frequency)
sku_velocities = {sku: random.randint(5, 20) for sku in SKUs}

# --- TIER 1: GREEDY SLOTTING ENGINE ---
def run_greedy_reslotting():
    """
    Greedy Strategy: Sorts SKUs by Velocity / Distance to Packing Station.
    Re-assigns high-valued SKUs to shelf spots physically closest to the Packing Station.
    """
    global sku_to_coords, coords_to_sku
    
    def manhattan_dist(p1, p2):
        return abs(p1[0] - p2[0]) + abs(p1[1] - p2[1])
    
    # Calculate scores: Higher velocity and shorter distance yields higher priority score
    sku_scores = {}
    for sku in SKUs:
        # Temporary baseline distance if unassigned
        curr_loc = sku_to_coords.get(sku, shelf_cells[0])
        dist = manhattan_dist(curr_loc, PACKING_STATION) or 1
        sku_scores[sku] = sku_velocities[sku] / dist
        
    # Sort items by priority score descending
    sorted_skus = sorted(SKUs, key=lambda x: sku_scores[x], reverse=True)
    
    # Sort available shelf positions by proximity to packing station ascending
    sorted_shelves = sorted(shelf_cells, key=lambda cell: manhattan_dist(cell, PACKING_STATION))
    
    # Remap allocations
    sku_to_coords.clear()
    coords_to_sku.clear()
    for idx, sku in enumerate(sorted_skus):
        if idx < len(sorted_shelves):
            cell = sorted_shelves[idx]
            sku_to_coords[sku] = cell
            coords_to_sku[cell] = sku

# Run initial slotting optimization
run_greedy_reslotting()

# --- TIER 2: BITMASK DP ROUTE OPTIMIZER ---
def compute_distance_matrix(targets):
    """Computes basic Manhattan distances between all target nodes for the router."""
    n = len(targets)
    dist_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(n):
            dist_matrix[i, j] = abs(targets[i][0] - targets[j][0]) + abs(targets[i][1] - targets[j][1])
    return dist_matrix

def solve_tsp_bitmask_dp(targets):
    """
    Finds the absolute shortest path starting at Packing Station (index 0), 
    visiting all picked item locations, and returning back to Packing Station.
    """
    n = len(targets)
    if n <= 1:
        return [0]
        
    dist_matrix = compute_distance_matrix(targets)
    
    # DP table state: memo[mask][position]
    memo = {}
    
    def tsp(mask, pos):
        # Base case: all nodes visited, must return to packing station (0)
        if mask == (1 << n) - 1:
            return dist_matrix[pos][0], [0]
            
        state = (mask, pos)
        if state in memo:
            return memo[state]
            
        min_dist = float('inf')
        best_path = []
        
        for next_node in range(n):
            if not (mask & (1 << next_node)):
                new_mask = mask | (1 << next_node)
                cost, path = tsp(new_mask, next_node)
                total_cost = dist_matrix[pos][next_node] + cost
                
                if total_cost < min_dist:
                    min_dist = total_cost
                    best_path = [next_node] + path
                    
        memo[state] = (min_dist, best_path)
        return memo[state]

    # Start at mask=1 (node 0 visited), position=0
    total_shortest_dist, final_path = tsp(1, 0)
    # Complete full cycle sequence path array
    full_route_indices = [0] + final_path
    return [targets[idx] for idx in full_route_indices], total_shortest_dist

# --- SIMULATOR & GENERATOR EXECUTION ---
def generate_random_order(size=5):
    """Selects random subsets of items based on their structural velocity probabilities."""
    weights = [sku_velocities[sku] for sku in SKUs]
    total_w = sum(weights)
    probs = [w/total_w for w in weights]
    chosen_skus = np.random.choice(SKUs, size=size, replace=False, p=probs)
    return list(chosen_skus)

# --- PYGAME VISUALIZATION ENGINE ---
pygame.init()
pygame.display.set_caption("Blinkit Dark-Store Optimization Engine")
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 14)
font_bold = pygame.font.SysFont("Arial", 16, bold=True)

# Application state machines
current_order = generate_random_order()
current_targets = [PACKING_STATION] + [sku_to_coords[sku] for sku in current_order if sku in sku_to_coords]
optimized_route, path_distance = solve_tsp_bitmask_dp(current_targets)

# Picker path movement tracking variables
picker_sub_target_idx = 0
picker_pos_x, picker_pos_y = PACKING_STATION[1] * TILE_SIZE + PADDING + TILE_SIZE // 2, PACKING_STATION[0] * TILE_SIZE + PADDING + TILE_SIZE // 2
movement_speed = 4.0

last_reslot_time = time.time()
orders_completed = 0
total_distance_saved_or_processed = 0.0

running = True
while running:
    dt = clock.tick(60) # Lock to 60 FPS frame rate updates
    
    # --- INTERACTION EVENT HANDLING ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
    # --- TIME-BASED SIMULATED DEMAND DRIFT (GREEDY EVENT) ---
    # Trigger an explicit inventory demand surge pattern modification shift every 10 seconds
    if time.time() - last_reslot_time > 10:
        for _ in range(5):
            lucky_sku = random.choice(SKUs)
            sku_velocities[lucky_sku] += random.randint(20, 50) # Generate dynamic high velocity surge
        run_greedy_reslotting()
        last_reslot_time = time.time()
        # Recalculate target locations immediately due to spatial changes
        current_targets = [PACKING_STATION] + [sku_to_coords[sku] for sku in current_order if sku in sku_to_coords]
        optimized_route, path_distance = solve_tsp_bitmask_dp(current_targets)
        picker_sub_target_idx = 0

    # --- PICKER ROUTING STATE ENGINE ---
    if picker_sub_target_idx < len(optimized_route):
        target_grid_pos = optimized_route[picker_sub_target_idx]
        target_pixel_x = target_grid_pos[1] * TILE_SIZE + PADDING + TILE_SIZE // 2
        target_pixel_y = target_grid_pos[0] * TILE_SIZE + PADDING + TILE_SIZE // 2
        
        dx = target_pixel_x - picker_pos_x
        dy = target_pixel_y - picker_pos_y
        distance_to_node = np.hypot(dx, dy)
        
        if distance_to_node > movement_speed:
            picker_pos_x += (dx / distance_to_node) * movement_speed
            picker_pos_y += (dy / distance_to_node) * movement_speed
        else:
            picker_pos_x, picker_pos_y = target_pixel_x, target_pixel_y
            picker_sub_target_idx += 1
    else:
        # Order completely fulfilled and returned back to base
        orders_completed += 1
        total_distance_saved_or_processed += path_distance
        
        # Pull new asynchronous stream order instantly
        current_order = generate_random_order()
        current_targets = [PACKING_STATION] + [sku_to_coords[sku] for sku in current_order if sku in sku_to_coords]
        optimized_route, path_distance = solve_tsp_bitmask_dp(current_targets)
        picker_sub_target_idx = 0

    # --- RENDERING ENGINE GRAPHICS PIPELINE ---
    screen.fill(COLOR_BACKGROUND)
    
    # 1. Render Map Layout Matrix Blocks
    for r in range(GRID_ROWS):
        for c in range(GRID_COLS):
            rect = pygame.Rect(c * TILE_SIZE + PADDING, r * TILE_SIZE + PADDING, TILE_SIZE, TILE_SIZE)
            if WAREHOUSE_MAP[r, c] == 1:
                pygame.draw.rect(screen, COLOR_WALL, rect)
                pygame.draw.rect(screen, (150, 150, 150), rect, 1) # Border
            elif WAREHOUSE_MAP[r, c] == 2:
                pygame.draw.rect(screen, COLOR_PACKING, rect)
            else:
                pygame.draw.rect(screen, COLOR_AISLE, rect)
                pygame.draw.rect(screen, (230, 230, 230), rect, 1) # Structural grid line trace
                
    # 2. Render Assigned Inventory Nodes
    for sku, (r, c) in sku_to_coords.items():
        rect = pygame.Rect(c * TILE_SIZE + PADDING + 4, r * TILE_SIZE + PADDING + 4, TILE_SIZE - 8, TILE_SIZE - 8)
        color = COLOR_ITEM_HOT if sku_velocities[sku] > 35 else COLOR_ITEM_NORMAL
        
        # Highlight if item is inside the current active picking batch
        if sku in current_order:
            pygame.draw.rect(screen, COLOR_PATH, rect) # Yield visual trace wrapper outline box
            pygame.draw.rect(screen, color, rect.inflate(-4, -4))
        else:
            pygame.draw.rect(screen, color, rect)
            
        # Optional: Print numerical velocity rating values directly inside boxes
        v_text = font.render(str(sku_velocities[sku]), True, (255, 255, 255))
        screen.blit(v_text, (rect.x + 4, rect.y + 4))

    # 3. Render Calculated DP Route Pathway Trajectories
    if len(optimized_route) > 1:
        points = []
        for node in optimized_route:
            px = node[1] * TILE_SIZE + PADDING + TILE_SIZE // 2
            py = node[0] * TILE_SIZE + PADDING + TILE_SIZE // 2
            points.append((px, py))
        pygame.draw.lines(screen, COLOR_PATH, False, points, 3)

    # 4. Render Active Autonomous Automated Picker Bot Entity
    pygame.draw.circle(screen, COLOR_PICKER, (int(picker_pos_x), int(picker_pos_y)), 10)

    # 5. Render Metric HUD Informational Footer Dashboard
    panel_y = GRID_ROWS * TILE_SIZE + PADDING * 2
    pygame.draw.rect(screen, (255, 255, 255), (0, panel_y, SCREEN_WIDTH, INFO_PANEL_HEIGHT))
    pygame.draw.line(screen, (200, 200, 200), (0, panel_y), (SCREEN_WIDTH, panel_y), 2)
    
    # Text data strings variables
    txt_order = font_bold.render(f"Current Order Basket: {', '.join(current_order)}", True, COLOR_TEXT)
    txt_metrics = font.render(f"Orders Completed: {orders_completed}  |  Total Walk-Distance Accounted: {int(total_distance_saved_or_processed)} units", True, COLOR_TEXT)
    txt_dp_status = font.render(f"Optimal DP Path Found Matrix Metric Cost: {int(path_distance)} steps", True, COLOR_PICKER)
    txt_greedy_status = font.render("Hourly Greedy Demand Re-Slotting Engine: ACTIVE (Auto-shifts Red Hot SKUs to base)", True, COLOR_ITEM_HOT)
    
    screen.blit(txt_order, (PADDING, panel_y + 10))
    screen.blit(txt_metrics, (PADDING, panel_y + 35))
    screen.blit(txt_dp_status, (PADDING, panel_y + 55))
    screen.blit(txt_greedy_status, (PADDING, panel_y + 75))

    pygame.display.flip()

pygame.quit()
sys.exit()
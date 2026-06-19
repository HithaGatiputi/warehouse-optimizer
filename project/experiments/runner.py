"""
Headless experiment runner and scalability testing framework.
"""
import time
import random
from project.warehouse.layout import WarehouseLayout
from project.warehouse.inventory import InventoryManager
from project.algorithms.slotting import SlottingEngine
from project.algorithms.forecasting import DemandForecaster
from project.algorithms.pathfinding import compute_bfs_distance_matrix, bfs_shortest_path
from project.algorithms.routing import plan_route
from project.simulation.orders import OrderManager

def run_experiment(orders_count: int, strategy: str, num_skus: int = 100):
    layout = WarehouseLayout()
    inventory = InventoryManager()
    inventory.generate_inventory(num_skus)
    shelves = layout.get_shelf_cells()
    random.shuffle(shelves)
    for i, sku in enumerate(inventory.get_all_skus()):
        if i < len(shelves):
            inventory.assign_location(sku.sku_id, shelves[i])
            
    inventory.classify_abc()
    
    forecaster = DemandForecaster()
    slotting = SlottingEngine()
    slotting.optimize_slotting(inventory, layout, strategy, forecaster)
    
    order_manager = OrderManager(inventory)
    
    total_dist = 0
    start_time = time.time()
    
    packing = layout.packing_station
    for _ in range(orders_count):
        # Simulate demand drift
        for sku in inventory.get_all_skus():
            inventory.update_demand(sku.sku_id, random.uniform(0, 5))
        forecaster.update_forecasts(inventory)
        
        # Use Demand-Weighted Realistic Orders
        order = order_manager.generate_customer_order()
        order_shelves = order.locations
        
        targets = [packing]
        for shelf in order_shelves:
            aisle = layout.get_adjacent_aisle(shelf)
            if aisle: targets.append(aisle)
            
        dist_matrix = compute_bfs_distance_matrix(layout, targets)
        _, dist, _ = plan_route(dist_matrix)
        total_dist += dist

    end_time = time.time()
    runtime = end_time - start_time
    avg_dist = total_dist / orders_count
    
    print(f"Strategy: {strategy} | Orders: {orders_count}")
    print(f"Average Distance: {avg_dist:.1f}")
    print(f"Forecast Accuracy: {forecaster.get_average_accuracy():.1f}%")
    print(f"Runtime: {runtime:.2f}s")
    print("-" * 40)

def run_scalability_test():
    print("Running Scalability Tests...")
    sku_counts = [50, 100, 500, 1000]
    for count in sku_counts:
        inventory = InventoryManager()
        inventory.generate_inventory(count)
        order_manager = OrderManager(inventory)
        
        # We need a large enough layout for up to 1000 SKUs (1000 shelves)
        layout = WarehouseLayout(rows=max(20, count//10), cols=max(25, count//10))
        shelves = layout.get_shelf_cells()
        
        start_slot = time.time()
        for i, sku in enumerate(inventory.get_all_skus()):
            if i < len(shelves):
                inventory.assign_location(sku.sku_id, shelves[i])
                
        inventory.classify_abc()
        slotting = SlottingEngine()
        slotting.optimize_slotting(inventory, layout, "Greedy")
        end_slot = time.time()
        
        start_route = time.time()
        packing = layout.packing_station
        targets = [packing]
        
        # We force size 15 order to test NN scalability specifically
        order = order_manager.generate_customer_order(size=15)
        order_shelves = order.locations
        for shelf in order_shelves:
            aisle = layout.get_adjacent_aisle(shelf)
            if aisle: targets.append(aisle)
            
        dist_matrix = compute_bfs_distance_matrix(layout, targets)
        _, dist, is_dp = plan_route(dist_matrix)
        end_route = time.time()
        
        print(f"SKUs: {count} | Slotting: {end_slot - start_slot:.4f}s | Routing (size 15, DP={is_dp}): {end_route - start_route:.4f}s | Dist: {dist:.1f}")

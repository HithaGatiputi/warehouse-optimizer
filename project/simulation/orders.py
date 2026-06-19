"""
Order Management for live Quick-Commerce simulation.
"""
from dataclasses import dataclass
from typing import Optional
import time
import random
from project.warehouse.inventory import InventoryManager, SKUInfo

@dataclass
class Order:
    order_id: int
    customer_id: str
    items: list[SKUInfo]
    status: str = "Pending"  # Pending, Assigned, Picking, Completed
    picker_id: Optional[int] = None
    assignment_time: float = 0.0
    completion_time: float = 0.0
    
    @property
    def basket_size(self) -> int:
        return len(self.items)
        
    @property
    def locations(self) -> list[tuple[int, int]]:
        return [item.location for item in self.items if item.location]

class OrderManager:
    def __init__(self, inventory: InventoryManager):
        self.inventory = inventory
        self.pending_orders: list[Order] = []
        self.active_orders: list[Order] = []
        self.completed_orders: list[Order] = []
        self.order_counter = 0
        self.time_of_day = "Morning"  # Morning, Afternoon, Evening
        
        self.category_weights = {
            "Morning": {"Dairy": 2.0, "Staples": 1.5, "Fruits": 1.2, "General": 1.0},
            "Afternoon": {"Snacks": 1.5, "Beverages": 1.5, "General": 1.0},
            "Evening": {"Snacks": 2.0, "Beverages": 2.0, "Personal Care": 1.2, "General": 1.0}
        }
        
    def generate_customer_order(self, size: int = None) -> Order:
        """Generates a realistic order using demand velocity and time-of-day multipliers."""
        self.order_counter += 1
        
        if size is None:
            # Quick-commerce baskets are usually small (2-8 items)
            size = random.choice([2, 3, 3, 4, 4, 5, 6, 8])
            
        skus = self.inventory.get_all_skus()
        
        # Calculate dynamic weights
        weights = []
        tod_weights = self.category_weights.get(self.time_of_day, {"General": 1.0})
        
        for sku in skus:
            cat_mult = tod_weights.get(sku.category, tod_weights.get("General", 1.0))
            # Weight = Base Velocity * TimeOfDay Multiplier
            weight = (sku.velocity * cat_mult) + 1.0
            weights.append(weight)
            
        if sum(weights) == 0:
            weights = [1] * len(skus)
            
        # Sample without replacement
        sampled_items = []
        available_skus = list(skus)
        available_weights = list(weights)
        
        for _ in range(min(size, len(skus))):
            idx = random.choices(range(len(available_skus)), weights=available_weights, k=1)[0]
            sampled_items.append(available_skus[idx])
            available_skus.pop(idx)
            available_weights.pop(idx)
            
        order = Order(
            order_id=self.order_counter,
            customer_id=f"CUST_{random.randint(1000, 9999)}",
            items=sampled_items
        )
        self.pending_orders.append(order)
        return order
        
    def get_next_pending_order(self) -> Optional[Order]:
        if self.pending_orders:
            order = self.pending_orders.pop(0)
            order.status = "Assigned"
            order.assignment_time = time.time()
            self.active_orders.append(order)
            return order
        return None
        
    def complete_order(self, order: Order):
        order.status = "Completed"
        order.completion_time = time.time()
        if order in self.active_orders:
            self.active_orders.remove(order)
        self.completed_orders.append(order)
        
    def cycle_time_of_day(self):
        cycles = ["Morning", "Afternoon", "Evening"]
        idx = cycles.index(self.time_of_day)
        self.time_of_day = cycles[(idx + 1) % len(cycles)]
        
    def get_metrics(self) -> dict:
        total_completed = len(self.completed_orders)
        if total_completed > 0:
            avg_time = sum(o.completion_time - o.assignment_time for o in self.completed_orders) / total_completed
        else:
            avg_time = 0.0
            
        return {
            "pending": len(self.pending_orders),
            "active": len(self.active_orders),
            "completed": total_completed,
            "avg_fulfillment_time": avg_time,
            "time_of_day": self.time_of_day
        }

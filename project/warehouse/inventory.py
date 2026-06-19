"""
Inventory management system with ABC classification and realistic products.
"""
from dataclasses import dataclass, field
import random
from typing import Optional
from project.config import ABC_A_PERCENT, ABC_B_PERCENT

@dataclass
class SKUInfo:
    sku_id: str
    product_name: str
    category: str
    velocity: float
    abc_class: str = "C"
    location: Optional[tuple[int, int]] = None
    demand_history: list[float] = field(default_factory=list)

BASE_CATALOG = [
    ("Milk", "Dairy", 95), ("Curd", "Dairy", 85), ("Paneer", "Dairy", 75), ("Butter", "Dairy", 80), ("Cheese", "Dairy", 65), ("Yogurt", "Dairy", 70),
    ("Rice", "Staples", 85), ("Atta", "Staples", 90), ("Maida", "Staples", 60), ("Sugar", "Staples", 80), ("Salt", "Staples", 75), ("Dal", "Staples", 70), ("Cooking Oil", "Staples", 85),
    ("Onion", "Vegetables", 90), ("Potato", "Vegetables", 95), ("Tomato", "Vegetables", 85), ("Carrot", "Vegetables", 60), ("Cabbage", "Vegetables", 50), ("Chilli", "Vegetables", 80), ("Lemon", "Vegetables", 70),
    ("Banana", "Fruits", 85), ("Apple", "Fruits", 75), ("Orange", "Fruits", 65), ("Mango", "Fruits", 60), ("Grapes", "Fruits", 55), ("Papaya", "Fruits", 40),
    ("Maggi", "Snacks", 95), ("Chips", "Snacks", 90), ("Biscuits", "Snacks", 85), ("Chocolates", "Snacks", 80), ("Namkeen", "Snacks", 75), ("Popcorn", "Snacks", 60), ("Cookies", "Snacks", 70),
    ("Coke", "Beverages", 85), ("Pepsi", "Beverages", 80), ("Sprite", "Beverages", 75), ("Juice", "Beverages", 70), ("Water", "Beverages", 90), ("Tea", "Beverages", 65), ("Coffee", "Beverages", 60),
    ("Soap", "Household", 55), ("Shampoo", "Household", 50), ("Detergent", "Household", 60), ("Floor Cleaner", "Household", 45), ("Dish Wash", "Household", 65), ("Tissue Paper", "Household", 75), ("Garbage Bags", "Household", 60),
    ("Toothpaste", "Personal Care", 70), ("Face Wash", "Personal Care", 60), ("Hand Wash", "Personal Care", 65), ("Deodorant", "Personal Care", 45), ("Razor", "Personal Care", 35), ("Lotion", "Personal Care", 40)
]

CATALOG = []
for name, category, velocity in BASE_CATALOG:
    if velocity >= 85: count = 5
    elif velocity >= 75: count = 3
    elif velocity >= 60: count = 2
    else: count = 1
    for _ in range(count):
        CATALOG.append((name, category, velocity))


class InventoryManager:
    def __init__(self):
        self.skus: dict[str, SKUInfo] = {}

    def generate_inventory(self, num_skus: int = len(CATALOG)) -> None:
        """Generates realistic catalog or defaults to padded dummy items if > catalog size."""
        self.skus.clear()
        
        for i in range(num_skus):
            sku_id = f"SKU_{i:03d}"
            if i < len(CATALOG):
                name, category, base_vel = CATALOG[i]
                # Add slight random noise to base velocity
                velocity = base_vel + random.uniform(-5.0, 5.0)
            else:
                name = f"Product {i}"
                category = "General"
                velocity = random.uniform(5.0, 30.0)
                
            self.skus[sku_id] = SKUInfo(
                sku_id=sku_id, 
                product_name=name, 
                category=category, 
                velocity=velocity
            )

    def classify_abc(self) -> None:
        if not self.skus: return
            
        sorted_skus = sorted(self.skus.values(), key=lambda x: x.velocity, reverse=True)
        total_skus = len(sorted_skus)
        
        num_a = int(total_skus * ABC_A_PERCENT)
        num_b = int(total_skus * ABC_B_PERCENT)
        
        for i, sku in enumerate(sorted_skus):
            if i < num_a: sku.abc_class = "A"
            elif i < num_a + num_b: sku.abc_class = "B"
            else: sku.abc_class = "C"

    def assign_location(self, sku_id: str, location: tuple[int, int]) -> None:
        if sku_id in self.skus:
            self.skus[sku_id].location = location

    def update_demand(self, sku_id: str, amount: float) -> None:
        if sku_id in self.skus:
            sku = self.skus[sku_id]
            sku.demand_history.append(amount)
            sku.velocity += amount

    def get_sku(self, sku_id: str) -> Optional[SKUInfo]:
        return self.skus.get(sku_id)

    def get_all_skus(self) -> list[SKUInfo]:
        return list(self.skus.values())

    def get_location(self, sku_id: str) -> Optional[tuple[int, int]]:
        sku = self.get_sku(sku_id)
        return sku.location if sku else None

    def get_skus_by_class(self, abc_class: str) -> list[SKUInfo]:
        return [sku for sku in self.skus.values() if sku.abc_class == abc_class]

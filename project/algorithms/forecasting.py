"""
Lightweight demand prediction module.
"""
from project.warehouse.inventory import InventoryManager, SKUInfo
from project.config import FORECAST_WINDOW, SMOOTHING_ALPHA

class DemandForecaster:
    def __init__(self):
        self.forecasts: dict[str, float] = {}
        self.accuracy: dict[str, float] = {}
        
    def forecast_moving_average(self, sku: SKUInfo) -> float:
        history = sku.demand_history[-FORECAST_WINDOW:]
        if not history: return sku.velocity
        return sum(history) / len(history)
        
    def forecast_exponential_smoothing(self, sku: SKUInfo) -> float:
        if sku.sku_id not in self.forecasts:
            return self.forecast_moving_average(sku)
            
        prev_forecast = self.forecasts[sku.sku_id]
        actual = sku.demand_history[-1] if sku.demand_history else sku.velocity
        return SMOOTHING_ALPHA * actual + (1 - SMOOTHING_ALPHA) * prev_forecast

    def update_forecasts(self, inventory: InventoryManager, method: str = "exponential"):
        for sku in inventory.get_all_skus():
            # Calculate accuracy of previous forecast
            if sku.sku_id in self.forecasts and sku.demand_history:
                actual = sku.demand_history[-1]
                predicted = self.forecasts[sku.sku_id]
                error = abs(actual - predicted)
                acc = max(0, 1.0 - (error / (actual + 0.001)))
                self.accuracy[sku.sku_id] = acc * 100

            # Generate new forecast
            if method == "ma":
                f = self.forecast_moving_average(sku)
            else:
                f = self.forecast_exponential_smoothing(sku)
                
            self.forecasts[sku.sku_id] = f
            
    def get_average_accuracy(self) -> float:
        if not self.accuracy: return 100.0
        return sum(self.accuracy.values()) / len(self.accuracy)

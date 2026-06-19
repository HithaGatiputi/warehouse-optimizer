"""
Routing algorithms: Bitmask DP TSP and Nearest Neighbor fallback.
"""
import numpy as np
from project.config import DP_TSP_MAX_ITEMS

def solve_tsp_nearest_neighbor(dist_matrix: np.ndarray) -> tuple[list[int], float]:
    """Nearest Neighbor heuristic for TSP (used as fallback for large orders)."""
    n = len(dist_matrix)
    if n <= 1:
        return [0], 0.0
        
    unvisited = set(range(1, n))
    current = 0
    path = [0]
    total_dist = 0.0
    
    while unvisited:
        next_node = min(unvisited, key=lambda x: dist_matrix[current, x])
        total_dist += dist_matrix[current, next_node]
        path.append(next_node)
        unvisited.remove(next_node)
        current = next_node
        
    # Return to start
    total_dist += dist_matrix[current, 0]
    path.append(0)
    
    return path, total_dist

def solve_tsp_dp(dist_matrix: np.ndarray) -> tuple[list[int], float]:
    """Exact TSP using Bitmask Dynamic Programming."""
    n = len(dist_matrix)
    if n <= 1:
        return [0], 0.0
        
    memo = {}
    
    def tsp(mask: int, pos: int) -> tuple[float, list[int]]:
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
                cost, sub_path = tsp(new_mask, next_node)
                total_cost = dist_matrix[pos][next_node] + cost
                
                if total_cost < min_dist:
                    min_dist = total_cost
                    best_path = [next_node] + sub_path
                    
        memo[state] = (min_dist, best_path)
        return memo[state]
        
    min_dist, final_path = tsp(1, 0)
    return [0] + final_path, min_dist

def plan_route(dist_matrix: np.ndarray) -> tuple[list[int], float, bool]:
    """Chooses the appropriate routing algorithm based on order size."""
    n_items = len(dist_matrix) - 1  # Excluding start node
    
    if n_items <= DP_TSP_MAX_ITEMS:
        path, dist = solve_tsp_dp(dist_matrix)
        is_dp = True
    else:
        path, dist = solve_tsp_nearest_neighbor(dist_matrix)
        is_dp = False
        
    return path, dist, is_dp

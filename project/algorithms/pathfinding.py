"""
Breadth-First Search (BFS) pathfinding on the warehouse grid.
"""
from collections import deque
import numpy as np
from project.warehouse.layout import WarehouseLayout

def bfs_shortest_path(layout: WarehouseLayout, start: tuple[int, int], end: tuple[int, int]) -> tuple[list[tuple[int, int]], int]:
    """Finds shortest path between two walkable cells using BFS."""
    if start == end:
        return [start], 0
        
    queue = deque([(start, [start])])
    visited = {start}
    
    while queue:
        current, path = queue.popleft()
        
        if current == end:
            return path, len(path) - 1
            
        for neighbor in layout.get_neighbors(current[0], current[1]):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append((neighbor, path + [neighbor]))
                
    return [], float('inf')  # No path found

def compute_bfs_distance_matrix(layout: WarehouseLayout, targets: list[tuple[int, int]]) -> np.ndarray:
    """Precomputes BFS distances between all pairs of targets."""
    n = len(targets)
    dist_matrix = np.zeros((n, n))
    
    for i in range(n):
        for j in range(i + 1, n):
            _, dist = bfs_shortest_path(layout, targets[i], targets[j])
            dist_matrix[i, j] = dist
            dist_matrix[j, i] = dist
            
    return dist_matrix

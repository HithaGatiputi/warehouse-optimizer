DAA_EL — Dark-Store Automation and Simulation
===============================================

Table of Contents
- Project Overview
- Quick Start
- Architecture and Components
  - Warehouse Layout
  - Inventory Manager
  - Simulation Core
  - Algorithms
    - Assignment
    - Forecasting
    - Pathfinding
    - Routing
    - Slotting
  - Visualization and UI
  - Manual Mode & Sliders
- Data Flows and Runtime Behavior
- File Map and Responsibilities
- Extension Points and How to Add Features
- Testing and Validation
- Performance Considerations
- Frequently Asked Questions (FAQ)
- Contact / Contributing


Project Overview
----------------
This repository implements a realistic dark-store (micro-fulfillment) simulator intended for research and experimentation with routing, slotting, assignment, and demand forecasting strategies. The system simulates a compact warehouse floorplan with shelves, aisles, pickers, and an order stream. It combines algorithmic modules (pathfinding, routing, slotting, assignment, forecasting) with a visualization layer (Pygame) and a lightweight simulation engine.

Goals
- Provide a modular research platform to compare routing and slotting strategies.
- Visualize picker movements, congestion, heatmaps, and order fulfillment behavior.
- Offer a manual interactive mode to tune parameters (via sliders) and observe immediate effects.
- Keep code modular so that new algorithms or heuristics can be plugged in with minimal friction.

Quick Start
-----------
1. Install dependencies:

```powershell
pip install -r requirements.txt
```

2. Run the simulator:

```powershell
python run.py
```

3. Or launch the project entrypoint:

```powershell
python project/main.py
```

4. Use the UI keys:
- `Space`: generate some orders
- `d`: toggle demo mode
- Other interactive controls: clicks on catalog in the right-hand panel

Architecture and Components
---------------------------
Top-level structure (key files and directories):
- `project/` — primary application code
  - `config.py` — simulation constants and tunables
  - `main.py` — orchestrates initialization, main loop, event handling, slider integration
  - `algorithms/` — algorithm implementations (assignment, forecasting, pathfinding, routing, slotting)
  - `simulation/` — runtime actors and managers (pickers, orders, congestion, heatmap)
  - `warehouse/` — layout and inventory models
  - `visualization/` — Pygame rendering, colors, UI state
- `manual_sim.py` — sandbox used to prototype the slider UI and interactions
- `run.py` — convenience script to launch the simulation

Warehouse Layout (`project/warehouse/layout.py`)
- Models the grid-based warehouse layout: number of rows/cols, shelf cell positions, aisle locations, and packing station.
- Provides convenience functions: `get_shelf_cells()`, `get_adjacent_aisle(cell)`, and packing station coordinates.
- Used by pathfinding and renderer for mapping grid cells to pixel coordinates.

Inventory Manager (`project/warehouse/inventory.py`)
- Stores SKU definitions, locations, demand history, and ABC classification.
- Responsibilities:
  - `generate_inventory()` to seed SKU locations
  - `assign_location(sku_id, cell)` to map SKUs to cell coordinates
  - `update_demand(sku_id, value)` consumed by the `DemandForecaster`
  - `classify_abc()` to label SKUs (A/B/C) for slotting heuristics

Simulation Core
---------------
Core runtime pieces live under `project/simulation/`:
- `picker.py` — `Picker` agent class with `update()` to advance along planned path; holds properties like `speed`, current order, pixel position, and state.
- `orders.py` — `OrderManager` that creates, queues, assigns, and completes orders. Orders include multiple SKUs and map to shelf locations.
- `congestion.py` — `CongestionManager` that tracks busy tiles or congested areas (used for visualization and possibly routing penalties).
- `heatmap.py` — collects pick frequencies across cells and exposes heatmap tiles for visualization.

Algorithms (location: `project/algorithms/`)
-------------------------------------------
This project intentionally separates algorithm implementations into modules, enabling experimentation.

Assignment (`project/algorithms/assignment.py`)
- Purpose: Map pending orders to pickers. Current default is a nearest-available heuristic.
- Key function: `assign_nearest_available_picker(picker_list, order, layout)`
- Behavior: compute pickup distance from each idle picker to the order's first target (or packing station) and assign to the picker with minimum travel time. Tie-breaking and more advanced load-balancing can be added.

Forecasting (`project/algorithms/forecasting.py`)
- Purpose: Provide demand predictions used by slotting and to drive scenario generation.
- `DemandForecaster` maintains per-SKU demand estimates and exposes `update_forecasts(inventory)` to compute future demand windows.
- Often used to produce prioritized SKU lists for `SlottingEngine`.

Pathfinding (`project/algorithms/pathfinding.py`)
- Purpose: Compute shortest paths on the discrete grid layout.
- Primary utilities:
  - `bfs_shortest_path(layout, start, goal)` — BFS on grid cells returning a path (list of cells).
  - `compute_bfs_distance_matrix(layout, targets)` — computes pairwise shortest distances between a set of target cells (used by routing planner).
- BFS is chosen for simplicity and deterministic predictable behavior. It can be replaced by A* if heuristics/weighted metrics are needed.

Routing (`project/algorithms/routing.py`)
- Purpose: Solve the order-picking routing problem: given a sequence of targets, produce an efficient route.
- Key function: `plan_route(distance_matrix)` — uses a small TSP-style planner (or dynamic programming) to compute an ordered visiting sequence of targets and returns route indices, total distance, and a boolean flag `is_dp` if solved via dynamic programming.
- The routing module interacts with the pathfinding component to translate index sequences into explicit cell paths by calling `bfs_shortest_path` between adjacent route targets.

Slotting (`project/algorithms/slotting.py`)
- Purpose: Compute SKU placements (slotting) to reduce travel distance given a forecast or observed demand.
- `SlottingEngine.optimize_slotting(inventory, layout, strategy, forecaster)` is the entrypoint: it accepts strategies such as `ForecastDriven`, `Greedy`, `ABC`, or `Random`.
- Outputs a metrics dict potentially containing `executed` flags, moved SKUs, and reslotting cost/benefit metrics.

Visualization and UI (`project/visualization/`)
----------------------------------------------
- `renderer.py` — central Pygame rendering logic that draws:
  - Warehouse grid and shelves scaled to screen size
  - Pickers and their routes
  - Heatmap overlays
  - Inventory catalog and small UI controls (catalog, submit/clear buttons)
  - Tooltip overlays for hovered SKU info
  - Right-hand sidebar for controls and slider widgets (manual mode)

- `colors.py` — defines colors used by the renderer (picker colors, heatmap colors, background)

- `ui_state.py` — transient UI state (hovered cell, custom cart, catalog rects, sliders list). `UIState` is used to store clickable rectangles and widget references so input handling in `main.py` can act on them.

Manual Mode & Sliders (`manual_sim.py` and `project/main.py`)
------------------------------------------------------------
A small interactive slider widget was prototyped in `manual_sim.py` and integrated into `project/main.py` for manual control of key simulation parameters. Current sliders include:
- Basket Order Size (SKUs): controls the number of SKUs per generated customer order
- Picker Speed Factor: multiplier applied to pickers' base speed
- Demand Surge Timer (s): how often a manual surge event triggers
- Surge Intensity: how many hot SKUs are affected during a manual surge

These sliders live in `UIState.sliders` and are drawn by the `Renderer` when manual mode is active. Slider events are fed first so they can capture mouse interactions.

Data Flows and Runtime Behavior
-------------------------------
1. Initialization (`project/main.py` / `run.py`):
   - Layout and inventory are created and seeded.
   - Forecaster and slotting engine are instantiated and an initial slotting optimization is executed.
   - Pickers are created and placed at the packing station.
   - Renderer and UIState are created and the main loop starts.

2. Main Loop:
   - Read input events; sliders and UI clicks are processed.
   - Possibly generate new orders (random or via slider/key)
   - Assignment module assigns available pickers to orders.
   - Routing computes pick sequences and pathfinding yields explicit cell sequences.
   - Pickers update positions using `Picker.update()` using their `speed` and current route.
   - Simulation managers update congestion and heatmap counters.
   - Renderer draws the world and UI.

3. Order Completion:
   - When a picker finishes a route, the order is marked completed; statistics are recorded and heatmap/congestion counters are updated.

File Map and Responsibilities
-----------------------------
- `run.py` — launcher stub.
- `manual_sim.py` — slider sandbox (can be used standalone)
- `project/main.py` — app bootstrap, main loop, slider hookup, event handling.
- `project/config.py` — constants such as `FPS`, base tile sizes, default picker speed.
- `project/warehouse/layout.py` — grid layout model and utility methods.
- `project/warehouse/inventory.py` — SKU management and demand recording.
- `project/algorithms/assignment.py` — picker assignment heuristics.
- `project/algorithms/forecasting.py` — demand forecasting logic.
- `project/algorithms/pathfinding.py` — BFS pathfinding and distance matrix computation.
- `project/algorithms/routing.py` — route planning (TSP/DP heuristics).
- `project/algorithms/slotting.py` — slotting optimization strategies.
- `project/simulation/picker.py` — `Picker` agent and state machine.
- `project/simulation/orders.py` — `OrderManager`, `Order` data structures.
- `project/simulation/congestion.py` — congestion tracking and metrics.
- `project/simulation/heatmap.py` — pick frequency heatmap.
- `project/visualization/renderer.py` — Pygame renderer, layout scaling, overlay drawing.
- `project/visualization/ui_state.py` — UI transient state and slider container.

Extension Points and How to Add Features
----------------------------------------
- Add new routing heuristics: Implement a new planner in `project/algorithms/routing.py` and expose it via a small strategy flag in `project/main.py` or `slotting`/`assignment` workflows.
- Swap BFS for A*: Replace `bfs_shortest_path` with an A* implementation in `project/algorithms/pathfinding.py` and keep the same function signature.
- New slotting strategy: Extend `SlottingEngine.optimize_slotting(...)` to accept and run new strategies; return comparable metrics for automated evaluation.
- Experiment harness: Add a script under `project/experiments/runner.py` (exists) to automate comparative runs with different config seeds and output CSV results.

Testing and Validation
----------------------
- Unit tests: add tests for algorithmic components (pathfinding distance correctness, routing feasibility, slotting objective improvements).
- Integration tests: simulate small layouts with deterministic random seeds and assert order completion times under different strategies.
- Visual validation: run the simulation and use the manual sliders to stress-test routing and observe heatmaps.

Performance Considerations
--------------------------
- BFS distance matrix scales O(N * cells) for N targets. For large target sets, consider caching or using heuristics to reduce pairwise computations.
- Slotting optimization currently is localized and may reassign many SKUs — ensure reslotting is bounded by budget or frequency.
- Rendering: Pygame draw calls are per-frame; reduce redraws, batch static overlays, or lower FPS for large layouts.

FAQ
---
Q: How do I change warehouse size?
A: Edit `project/warehouse/layout.py` where row/col constants are defined. The renderer will scale to the window size.

Q: How do I add more pickers?
A: In `project/main.py` adjust the number used when creating `Picker` instances.

Q: Where are the sliders configured?
A: Sliders are instantiated in `project/main.py` (look for the `Slider` class near the top) and are attached to `UIState.sliders`.

Contact / Contributing
----------------------
- To contribute, fork and open a PR. Prefer small focused changes with tests where applicable.
- If you'd like help adding a new routing strategy or scaling the experiments harness, open an issue with a short description and example input/expected behavior.


Appendix: Algorithmic Notes (Detailed)
--------------------------------------
Assignment heuristic
- Nearest-available is simple and performs well in many small warehouses; however it can cause imbalance. If you need better throughput under high load, consider adding lookahead, reservation windows, or load-aware balancing (e.g., minimize maximum completion time across all pickers).

Forecasting
- Current `DemandForecaster` exposes a thin abstraction: ingest updates (recent demand observations) and predict near-term demand. For experiments, replace the forecasting module with ARIMA, exponential smoothing, or ML-based models and feed resulting forecasts into the slotting engine.

Pathfinding & Distance Matrix
- BFS is used to ensure paths avoid obstacles (shelves). It's deterministic and grid-perfect. When computing a pairwise distance matrix for route planning, ensure unreachable states are handled (infinite cost or filtered targets).

Routing (TSP / DP)
- `plan_route` receives a distance matrix between targets and returns an index ordering plus a DP-solved flag. For small target sets exact DP is feasible; for larger sets, the module falls back to nearest neighbor or greedy improvements.

Slotting
- The `SlottingEngine` tries to reduce expected overall travel by moving popular SKUs closer to packing/aisles. Consider adding penalty terms for reslotting effort and constraints such as fixed SKUs or multi-slot SKUs.


-- End of Documentation --

# DAA_EL
Warehouse Storage Optimisation
# Blinkit Dark-Store Optimization Engine (B-DOE)

A hybrid algorithmic framework designed for ultra-low latency warehouse slotting and routing in Quick-Commerce "Dark Stores." This project models a Blinkit-style micro-fulfillment center (3,000–5,000 sq. ft.) where the entire picking phase must execute within **60–90 seconds**.

By combining a **Real-Time Greedy Slotting Engine** with a **Bitmask Dynamic Programming (DP) Router**, this system bridges the gap between rapid demand volatility and mathematically optimal picker routing.

---

## 🚀 The Challenge: Quick-Commerce Bottlenecks

Traditional fulfillment centers optimize for **Space Utilization**. Blinkit dark stores must optimize exclusively for **Picking Velocity**.

When a 10-minute delivery order comes in, picking multi-item orders efficiently is heavily bottlenecked by two factors:

1. **Dynamic Demand Shifts:** High-velocity items change rapidly throughout the day (e.g., milk/bread at 8 AM vs. snacks/soda at 11 PM).
2. **The Myopic Picker Problem:** Standard "nearest-neighbor" heuristic picking paths often trap pickers in dead-ends, inflating travel times.

---

## 🛠️ Architecture: The Hybrid Algorithmic Framework

This engine decouples layout organization from routing execution using a two-tier architectural model:

```
                  [ Real-Time Blinkit Order Stream ]
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│ Tier 1: Greedy Slotting Engine (Runs hourly/upon inventory influx)│
│ ──> Dynamically re-allocates "Trending SKUs" to the Golden Zone │
└──────────────────────────────────────────────────────────────────┘
                                  │
                       Updates Warehouse Grid
                                  │
                                  ▼
┌──────────────────────────────────────────────────────────────────┐
│ Tier 2: Bitmask DP Route Optimizer (Runs instantly per order)    │
│ ──> Computes the exact, absolute shortest path for multi-items   │
└──────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
                    [ Optimal 90s Picker Route ]

```

### 1. Tier 1: Demand-Aware Greedy Slotting

A real-time sorting heuristic that tracks SKU velocity scores ($V_i$) dynamically calculated over rolling windows.

* **Logic:** $V_i = \frac{\text{Order Frequency}_i}{\text{Distance from Packing Station}}$
* **Execution:** As item velocities spike, the algorithm executes local swaps to pull items into the "Golden Zone" (bins nearest to the packer), requiring minimal computational overhead ($O(N \log N)$).

### 2. Tier 2: Bitmask DP Multi-Pick Router

Once a multi-item basket is generated, standard greedy heuristics fail to find the global shortest path. Because a dark store order typically contains fewer than 15 items, we bypass the "Curse of Dimensionality" and solve the Traveling Salesperson Problem (TSP) exactly using **Dynamic Programming with Bitmasking**.

* **State Representation:** $dp[\text{mask}][i]$ represents the shortest path visiting the subset of items defined by the bitmask `mask`, ending at item `i`.
* **Complexity:** $O(2^n \cdot n^2)$ where $n$ is the number of unique item locations in the order. For $n \le 15$, this executes in milliseconds—well within the 90-second operational window.

---
---

## 📊 Core Performance Metrics

To validate the architecture, the project tracks the following key performance indicators (KPIs) against a baseline "Static-Slotting + Nearest-Neighbor" warehouse:

* **Picking Path Reduction (%)**: Total meters traveled per picker shift.
* **Order Fulfilment Latency**: Time elapsed from order arrival to path computation.
* **Congestion Multiplier**: Heatmaps identifying aisle blockages when multiple pickers target highly correlated zones.

---

## 🏃‍♂️ Getting Started

### Prerequisites

* Python 3.10+
* NumPy
* Matplotlib / Pygame (for visual simulation updates)

---

## 📚 Literature Gaps Filled by This Project

1. **Dynamic Context Drift:** Most logistics literature assumes static slotting layouts changed quarterly. This project tackles hourly demand fluctuations characteristic of modern quick-commerce.
2. **Exact Small-Scale Optimization:** While DP is generally dismissed in massive Amazon-sized fulfillment hubs due to scale, this project highlights its extreme efficacy when intentionally applied to the small-bounds framework of micro-fulfillment center order limits.


---
# Blinkit Dark-Store Optimization Engine (B-DOE)

B-DOE is a hybrid algorithmic simulation framework designed for ultra-low latency warehouse layout management and picker routing in Quick-Commerce "Dark Stores." The system models a high-velocity micro-fulfillment hub where total order picking turnaround must happen within a restrictive **60–90 second window**.

This engine decouples spatial layout optimization (**Tier 1: Demand-Aware Greedy Slotting**) from operational route execution (**Tier 2: Bitmask Dynamic Programming Pathfinder**).

## 🚀 Repository Content

* `manual_sim.py`: The complete interactive simulation environment built on Pygame. It features a real-time Control Panel allowing users to manipulate warehouse variables (basket sizes, picker speeds, demand volatility rates) and watch the dual-tier algorithmic engine adapt instantly.

---

## 🏃‍♂️ Setup and Running Instructions

### 1. Prerequisites

Ensure you have Python 3.10+ installed along with the required core scientific computing and visualization libraries:

```bash
pip install pygame numpy

```

### 2. Execution

Run the interactive simulation directly from your terminal:

```bash
python manual_sim.py

```

### 3. Interactive Sandbox Controls (Right Panel)

Use your mouse to drag the sliders on the right sidebar to modify dark store dynamics in real-time:

* **Basket Order Size (SKUs):** Sets how many distinct products are pulled into a customer's cart (Bounded up to 11 to guarantee near-instantaneous exact DP computation).
* **Picker Speed Factor:** Accelerates or decelerates the visual movement velocity of the picker bot.
* **Demand Surge Engine Timer:** Changes how often flash sales or seasonal spikes shift inventory demands.
* **Surge Spike Velocity Weight:** Controls the amplitude of popularity spikes when an item suddenly trends.

---

# 📊 Algorithmic Analysis & Deep-Dive

To take this project further, it is critical to evaluate how the underlying mathematics of Greedy Heuristics and Dynamic Programming behave under operational stress.

### 1. Mathematical Formalization of the Engines

#### Tier 1: The Greedy Slotting Heuristic

The warehouse is modeled as a 2D discrete coordinate matrix. The Packing Station is anchored at coordinate $P = (r_p, c_p)$. For every item $i \in \text{SKUs}$, the engine tracks a dynamic demand velocity score $V_i$.

The optimization metric is a Priority Score ($S_i$) defined by:

$$S_i = \frac{V_i}{\text{Manhattan Distance}((\text{row}_i, \text{col}_i), P) + \epsilon}$$

Where $\epsilon$ is a small smoothing constant preventing division by zero. The Greedy engine sorts the layout matrix such that the item ranking vector ordered by descending $S_i$ is mapped injectively to the shelf coordinate vectors ordered by ascending distance to $P$.

* **Time Complexity:** $O(N \log N)$ due to the sorting step of $N$ items.
* **Space Complexity:** $O(N)$ to preserve tracking indices.

#### Tier 2: The Bitmask TSP Dynamic Programming Router

Given an order containing a subset of items $k \subset \text{SKUs}$ along with the packing station, we construct an implicit complete graph where the nodes $n = |k| + 1$.

The state of our DP framework is tracked via a tuple: `(mask, pos)`

* `mask`: An integer bitmask of length $n$ where the $j$-th bit is $1$ if node $j$ has been visited, and $0$ otherwise.
* `pos`: The current integer node index location of the picker ($0 \le \text{pos} < n$).

The recurrence relation implemented is:

$$\text{TSP}(\text{mask}, \text{pos}) = \min_{j \notin \text{mask}} \Big( \text{Dist}(\text{pos}, j) + \text{TSP}(\text{mask} \cup \{j\}, j) \Big)$$

* **Base Case:** When $\text{mask} = (1 \in \mathbb{R}^n) - 1$ (all bits are $1$), return $\text{Dist}(\text{pos}, 0)$ to loop back to the packing dock.
* **Time Complexity:** $O(2^n \cdot n^2)$. While solving standard warehouse TSP is typically NP-hard, bounding $n \le 12$ inside micro-fulfillment architectures keeps $2^{12} \cdot 144 \approx 589,824$ operations, completing in microseconds.
* **Space Complexity:** $O(2^n \cdot n)$ to preserve memoized calculation matrices.

---

## 🔮 Future Optimization Roadmap (Extending the Project)

As you scale this project up, here are the major architectural and solution gaps you can fill to make this a publication-grade system:

### 1. Replacing Manhattan Distances with A* Search (Obstacle Aware)

* **Current Limitation:** The DP routing engine utilizes basic Manhattan distance ($|x_1 - x_2| + |y_1 - y_2|$), assuming the picker can pass diagonally through solid shelving units.
* **Further Optimization:** Write an **A* Pathfinding script** as a distance matrix pre-processor. The DP engine will then calculate the shortest path using true obstacle-aware walking metrics, forcing the picker to navigate cleanly through actual aisles.

### 2. Multi-Picker Congestion Control (Conflict Resolution)

* **Current Limitation:** The simulator tracks a single isolated picker. Real Blinkit dark stores use 3 to 7 pickers simultaneously.
* **Further Optimization:** Introduce multiple picker entities. When multiple pickers try to enter the same aisle to grab hot items, introduce a "congestion penalty multiplier" to the routing weight matrix. This forces the DP router to send picker #2 along a slightly longer but completely open alternative aisle.

### 3. SKU Affinity Correlation (Market Basket Clustering)

* **Current Limitation:** Tier 1 slots items purely based on individual item velocity.
* **Further Optimization:** Mine order history data using the **Apriori Algorithm** or **FP-Growth** to find SKU correlations (e.g., if Item A is bought, probability of Item B being bought is 85%). Modify the Greedy algorithm to score *item pairs* rather than single items, forcing correlated items to be slotted on adjacent shelves regardless of their individual velocity profiles.

### 4. Rolling-Horizon Stochastic DP

* **Current Limitation:** The system relies on reactive adjustments after demand shifts occur.
* **Further Optimization:** Shift from a purely reactive framework to a predictive **Markov Decision Process (MDP)** or **Stochastic Dynamic Programming** model. The layout can proactively re-slot items 1 hour *before* an expected localized peak (e.g., pre-slotting breakfast goods at 6:30 AM based on predictive historic trends).
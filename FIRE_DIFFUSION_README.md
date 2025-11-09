# Fire Diffusion System - Awaiting Paper Implementation

## ✅ What's Ready

### 1. Grid System
- **0.5m x 0.5m grid** fully implemented and visible
- Grid overlay displayed in visualization
- Grid resolution configurable in `params.json`

### 2. Layout Dimensions
- **Room size**: 15.64m x 12.68m (each office)
- **Total office**: 46.92m x 34.06m
- **6 offices** + **1 hallway** + **2 exits**
- Layout file: `layouts/office_correct_dimensions.json`

### 3. Infrastructure Ready
- Grid-based coordinate system
- Room adjacency tracking
- Hazard level tracking per room
- Visualization of hazard levels (yellow → orange → red gradient)

## ❌ What Needs the Paper

### Current Fire Logic (WRONG)
The current fire diffusion (`sim/env/hazard.py`) uses a **room-based** model:

```python
# Current (INCORRECT) - diffuses between rooms, not grid cells
new_hazard = room.hazard + spread_rate * dt
new_hazard += diffusion * (avg_neighbor - room.hazard) * dt
```

**Problems:**
1. Treats entire room as single hazard value
2. No spatial resolution within rooms
3. Doesn't account for fire origin point
4. Simplified neighbor averaging

### What I Need from the Paper

Please provide the paper so I can implement:

1. **Grid-Cell Based Diffusion**
   - Fire spreads between individual 0.5m x 0.5m cells
   - Not just between rooms

2. **Fire Physics Constants**
   - Diffusion coefficient (m²/s)
   - Heat transfer rate
   - Combustion parameters
   - Temperature thresholds

3. **Spread Model**
   - How fire spreads from cell to cell
   - Boundary conditions (walls, doors)
   - Ventilation effects
   - Time-dependent behavior

4. **Initial Conditions**
   - Where does fire start?
   - Initial temperature/intensity
   - Growth rate over time

## Implementation Plan

Once I have the paper, I will:

### Step 1: Create Grid-Based Hazard System
```python
class GridHazardSystem:
    def __init__(self, rooms, grid_resolution=0.5):
        # Create 2D grid of hazard cells
        self.grid_resolution = grid_resolution
        self.cells = {}  # (x, y) -> hazard_value
        
    def update(self, dt):
        # Apply diffusion equation to each cell
        for cell in self.cells:
            # Use paper's diffusion equation here
            pass
```

### Step 2: Update Visualization
- Show hazard gradient across grid cells (not just rooms)
- Color each 0.5m x 0.5m cell based on local hazard

### Step 3: Update Agent Logic
- Agents respond to local cell hazard, not room average
- Path planning avoids high-hazard cells

## Current Placeholder Values

In `params.json`:
```json
"hazard": {
  "enabled": true,
  "initial_level": 0.0,
  "spread_rate": 0.02,  // PLACEHOLDER - needs paper value
  "stair_up_bias": 1.5,  // PLACEHOLDER - needs paper value
  "diffusion_coefficient": 0.1  // PLACEHOLDER - needs paper value
}
```

These are **temporary approximations** that will be replaced with paper-based values.

## Grid Dimensions

### Layout Grid
```
Total: 46.92m x 34.06m
Grid cells: 94 x 68 = 6,392 cells (at 0.5m resolution)

Each room: 15.64m x 12.68m
Room cells: 31 x 25 = 775 cells per room
```

### Computational Considerations
- 6,392 cells total
- Update frequency: Every 1 second (configurable)
- Need efficient diffusion algorithm from paper

## Questions for the Paper

1. **What diffusion equation should I use?**
   - Fick's law?
   - Heat equation?
   - Custom fire spread model?

2. **What are the physical constants?**
   - Thermal diffusivity
   - Heat release rate
   - Ignition temperature

3. **How do boundaries work?**
   - Walls: reflective? absorbing?
   - Doors: how does fire spread through doorways?
   - Windows/ventilation: included?

4. **Initial fire location?**
   - Which room/cell starts on fire?
   - Initial size/intensity?
   - Growth curve?

5. **Time scale?**
   - How fast should fire spread?
   - Real-time seconds or scaled?

## Ready to Implement

As soon as you provide the paper, I can:
1. Replace the hazard diffusion logic in `sim/env/hazard.py`
2. Implement grid-cell-based fire spread
3. Add paper-specific constants to `params.json`
4. Update visualization to show cell-level hazards
5. Validate against paper's expected behavior

## Current Files to Modify

1. **`sim/env/hazard.py`** - Replace diffusion logic
2. **`params.json`** - Update constants from paper
3. **`sim/viz/matplotlib_animator.py`** - Show cell-level hazards (optional enhancement)
4. **`layouts/office_correct_dimensions.json`** - Add fire origin if needed

---

**Status**: ⏸️ Waiting for paper to implement correct fire diffusion

**What's working**: ✅ Grid display, layout dimensions, infrastructure

**What's needed**: 📄 Research paper with fire diffusion equations and constants


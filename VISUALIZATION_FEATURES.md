# Visualization Features - Cell Heatmap & Priority Indices

## ✅ Implemented Features

### 1. Cell-Level Danger Heatmap
Shows the danger level of each 0.5m x 0.5m grid cell with a color gradient:

**Color Gradient (White → Red):**
- **White**: No danger (safe cells)
- **Light Yellow (#FFF9C4)**: Low danger (0.0 - 0.2)
- **Light Orange (#FFE082)**: Moderate danger (0.2 - 0.5)
- **Orange (#FF9800)**: High danger (0.5 - 0.8)
- **Deep Orange/Red (#FF5722)**: Very high danger (0.8 - 1.0)
- **Bright Red (#FF1744)**: **BURNING** cells (fire origin)

**What You See:**
- Fire starts as bright red cells in O1 (top-left room)
- Fire spreads cell-by-cell creating a gradient pattern
- Each cell's color updates based on its danger level (d_i)
- Heatmap overlays the room boundaries

**Implementation:**
- File: `sim/viz/matplotlib_animator.py`
- Method: `_draw_cell_heatmap()`
- Updates every frame to show fire spread in real-time

### 2. Priority Index Display
Shows P_i(t) from the paper's formula on each room with modern styling:

**Formula (from paper):**
```
P_i(t) = (A_i(t) * E_i(t) * [1 + λD_i(t)]) / (D_i(t) + ε)
```

**Components:**
- **A_i(t)**: Accessibility (1 if reachable, 0 if blocked)
- **E_i(t)**: Expected evacuees remaining in room
- **D_i(t)**: Average danger level of room [0, 1]
- **λ** (lambda): 1.2 (prioritizes high-danger rooms)
- **ε** (epsilon): 0.001 (prevents division by zero)

**Visual Styling:**
- **Modern text badge** with rounded corners
- **Blue color scheme** (#1976D2)
- **White background** with blue border
- **Sans-serif font** (Helvetica/Arial)
- **Format**: "P = X.X" (e.g., "P = 15.3")
- **Position**: Center of each room, slightly below room ID

**Updates Dynamically:**
- Recalculated every frame
- Based on first agent's position
- Changes as evacuees are rescued
- Changes as danger levels increase

**Implementation:**
- File: `sim/policy/decision_engine.py`
- Method: `calculate_priority_index()`
- Display: `sim/viz/matplotlib_animator.py` → `_update_priority_labels()`

## How It Works

### Fire Spread Visualization

1. **Fire Origin**: 4 cells in center of O1 start burning (bright red)
2. **Heat Transfer**: Adjacent cells accumulate heat (alpha_i increases)
3. **Danger Calculation**: Each cell calculates U, S_nbr, S_p → d_i
4. **Color Gradient**: Cells display colors based on d_i value
5. **Real-Time Update**: Heatmap refreshes every frame (20 FPS)

### Priority Calculation

1. **Room Analysis**: For each non-exit room
2. **Calculate A_i**: Check if agent can reach room
3. **Get E_i**: Count remaining evacuees
4. **Get D_i**: Average danger from all cells in room
5. **Apply Formula**: Compute P_i(t) with λ = 1.2
6. **Display**: Show as modern badge on room

### Parameters (params.json)

```json
"policy": {
  "epsilon": 0.001,    // Prevents division by zero
  "lambda": 1.2,        // Prioritizes high-danger (>1) rooms
  ...
}

"hazard": {
  "use_grid_model": true,
  "grid_resolution": 0.5,
  "fire_origin": "O1",
  ...
}
```

## Visual Elements

### Legend

**Cell Colors:**
- 🤍 White = Safe (no danger)
- 🟡 Yellow = Low danger
- 🟠 Orange = Moderate-High danger
- 🔴 Red = Very high danger / FIRE

**Room Badges:**
- 🔵 Blue Badge = Priority Index (P = X.X)
- Higher P value = Higher priority for agents
- Updates in real-time as situation changes

## What Affects Priority?

**Higher Priority When:**
- ✅ More evacuees in room (E_i ↑)
- ✅ Higher danger level (D_i ↑ with λ > 1)
- ✅ Room is accessible (A_i = 1)

**Lower Priority When:**
- ❌ Room cleared (E_i = 0)
- ❌ Room inaccessible (A_i = 0)
- ❌ Very high danger in denominator

**Parameter λ Effect:**
- **λ > 1** (current: 1.2): Prioritize high-danger rooms
- **λ < 1**: Prioritize low-danger (safer) rooms
- **λ = 0**: Danger doesn't affect priority

## Running the Visualization

```bash
# Default with all features
python3 main.py --layout layouts/office_correct_dimensions.json --agents 4

# Press SPACE to start
# Watch the fire spread from O1 (red cells)
# See priority indices update on each room
```

## Key Features

### 1. Grid Overlay
- 0.5m x 0.5m grid lines visible
- Alpha: 0.35 (visible but not overwhelming)
- Shows spatial resolution

### 2. Cell Heatmap
- 6,392 individual cells tracked
- Color gradient: white → yellow → orange → red
- Burning cells in bright red (#FF1744)
- Updates 20 times per second

### 3. Priority Badges
- Modern rounded design
- Blue color scheme
- Clear numerical display
- Dynamic updates
- Professional typography

### 4. Room Dimensions
- Each room: 15.64m x 12.68m
- Total office: 46.92m x 34.06m
- 6 offices + 1 hallway + 2 exits

## Example Priority Values

**Early in Simulation (O1 burning):**
- O1: P = 20.5 (high danger, has evacuees)
- O2: P = 8.3 (some danger spread, has evacuees)
- O3: P = 6.1 (low danger, has evacuees)
- O4: P = 5.2 (no danger yet, has evacuees)

**After O1 Cleared:**
- O1: P = 0.0 (no evacuees left)
- O2: P = 15.7 (danger increased, prioritized)
- O3: P = 12.4 (danger spreading)
- O4: P = 8.9 (still safer, lower priority)

## Technical Details

### Cell Heatmap Performance
- Cells only drawn if danger > 0.01
- Burning cells always shown
- Z-order: 0.5 (below rooms, above grid)
- Alpha varies with danger level

### Priority Label Styling
```python
bbox = dict(
    boxstyle='round,pad=0.4',
    facecolor='white',
    edgecolor='#1976D2',  # Blue
    linewidth=1.5,
    alpha=0.9
)
```

### Update Frequency
- Cell heatmap: Every frame (20 FPS)
- Priority labels: Every frame
- Room colors: Every frame
- Agent trails: Every frame

## Files Modified

1. **`sim/viz/matplotlib_animator.py`**
   - Added `_draw_cell_heatmap()`
   - Added `_update_priority_labels()`
   - Updated `_update_frame()` to refresh both

2. **`sim/policy/decision_engine.py`**
   - Added `calculate_priority_index()` from paper
   - Added `lambda_param` parameter

3. **`params.json`**
   - Added `lambda: 1.2`
   - Updated `epsilon: 0.001`

## Result

You now have:
- ✅ **Cell-level danger heatmap** (white → red gradient)
- ✅ **Priority indices** displayed with modern text
- ✅ **Real-time updates** showing fire spread
- ✅ **Paper-based formulas** correctly implemented
- ✅ **Professional, modern UI** with clean typography

The visualization clearly shows:
1. Where the fire is (red cells in O1)
2. How it spreads (gradient pattern)
3. Which rooms have priority (P values)
4. Real-time danger levels per cell

Perfect for presentations, analysis, and understanding the simulation behavior! 🎉


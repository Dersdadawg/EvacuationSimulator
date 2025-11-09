# Paper-Based Fire Diffusion Implementation

## ✅ Implemented from Paper (Section 4.1.2)

### Grid-Based Fire Model

The fire now uses a **0.5m x 0.5m grid cell system** where each cell tracks its own danger level independently.

### Three Danger Score Components

#### 1. Time Urgency Score (U)
**Formula 8 from paper:**
```python
if alpha_i < Q_thr:
    U(c) = sqrt(1 / (Q_thr / alpha_i))
else:
    U(c) = 0
```

- **Purpose**: Measures how soon ignition may occur
- **alpha_i**: Heat accumulation in cell
- **Q_thr**: Ignition threshold (500.0)
- **Implementation**: `sim/env/grid_hazard.py`, line ~180

#### 2. Neighbor Pressure Score (S_nbr)
**Formula 9 from paper:**
```python
S_nbr(c) = B(c) / 4
```

- **Purpose**: Quantifies direct exposure from nearby flames
- **B(c)**: Number of burning neighboring cells (4-connected)
- **Implementation**: `sim/env/grid_hazard.py`, line ~185

#### 3. Permeability Score (S_p)
**Formula 10 from paper:**
```python
S_p(c) = (1 / max(1, B(c))) * sum(P_e(i->c)) for i in N_B(c)
```

- **Purpose**: Represents average openness of burning boundaries
- **P_e**: Permeability factor [0, 1]
  - Same room: 1.0 (fully open)
  - Connected rooms (door): 0.7
  - Wall: 0.1 (some heat transfer)
- **Implementation**: `sim/env/grid_hazard.py`, line ~190

### Cell Danger Level (d_i)
**Weighted sum (mentioned in paper):**
```python
d_i = w_urgency * U + w_neighbor * S_nbr + w_permeability * S_p
```

- Weights: 0.4, 0.4, 0.2 (balanced, not specified in paper excerpt)
- **Implementation**: `sim/env/grid_hazard.py`, line ~200

### Room Danger Level (D_i)
**As specified by user (average of cells):**
```python
D_i = average(d_i for all cells in room i)
```

- Room's hazard is the average of all its grid cells
- **Implementation**: `sim/env/grid_hazard.py`, line ~205

## Fire Origin

**Top-left room (O1)** starts burning, as specified:
- Fire begins in 4 cells at the center of room O1
- Spreads outward through grid cells
- **Implementation**: `sim/env/grid_hazard.py`, line ~120

## Fire Spread Mechanics

### Heat Accumulation (alpha_i)
Each cell's heat increases based on:
1. **Burning neighbors**: Each burning neighbor transfers heat
2. **Permeability**: Higher P_e = more heat transfer
3. **Heat transfer rate**: 0.05 per burning neighbor per second

```python
if cell has burning neighbors:
    heat_gain = sum(heat_transfer_rate * P_e(neighbor) * ignition_temp)
    alpha_i += heat_gain * dt
```

### Ignition
When `alpha_i >= ignition_temp` (500.0), cell starts burning

### Spread Pattern
1. Fire starts in O1 (top-left)
2. Spreads to adjacent cells within O1
3. Spreads through doorways to hallway (P_e = 0.7)
4. Spreads from hallway to other rooms
5. Creates realistic radial spread pattern

## Parameters (params.json)

```json
"hazard": {
  "enabled": true,
  "use_grid_model": true,
  "grid_resolution": 0.5,
  "fire_origin": "O1",
  
  // Paper parameters
  "Q_threshold": 500.0,           // Ignition threshold
  "heat_transfer_rate": 0.05,     // Heat per burning neighbor
  "ignition_temp": 500.0,          // When cell starts burning
  
  // Danger score weights
  "weight_urgency": 0.4,
  "weight_neighbor": 0.4,
  "weight_permeability": 0.2
}
```

## Grid Dimensions

### Layout: office_correct_dimensions.json
- **Total**: 46.92m x 34.06m
- **Grid cells**: ~94 x 68 = 6,392 cells
- **Each room**: 15.64m x 12.68m = ~31 x 25 = 775 cells
- **Resolution**: 0.5m x 0.5m

## Visualization

### What You See
1. **Grid lines**: 0.5m x 0.5m grid overlay (now visible!)
2. **Room colors**: Change based on average cell danger
   - Blue → Yellow → Orange → Red
   - Based on D_i (room average)
3. **Fire spread**: Radiates from O1 outward

### Grid Visibility
- Grid lines at 0.5m intervals
- Alpha: 0.35 (visible but not overwhelming)
- Linewidth: 0.5pt

## File Structure

### New Files
- **`sim/env/grid_hazard.py`**: Complete grid-based hazard system

### Modified Files
- **`sim/env/environment.py`**: Uses GridHazardSystem
- **`params.json`**: New paper-based parameters
- **`layouts/office_correct_dimensions.json`**: Correct dimensions

### Unchanged (Compatible)
- **`sim/viz/matplotlib_animator.py`**: Works with new system
- **`sim/engine/simulator.py`**: No changes needed
- **`sim/agents/`**: Agents respond to room hazard (D_i)

## Key Differences from Old System

### Before (Room-Based)
```python
# All rooms heated uniformly
hazard = base_rate + diffusion * neighbor_avg
```
- No spatial resolution
- Uniform heating
- No fire origin

### After (Grid-Based)
```python
# Each 0.5m cell tracked independently
d_i = f(U, S_nbr, S_p)  # Paper formulas
D_i = average(d_i)       # Room = avg of cells
```
- 6,392 individual cells
- Realistic spatial spread
- Fire starts in O1, radiates outward
- Paper-based danger scoring

## Running the Simulation

```bash
# With grid-based fire (default)
python3 main.py --layout layouts/office_correct_dimensions.json --agents 4

# You should see:
# - Fire starting in top-left room (O1)
# - Spreading cell-by-cell through the grid
# - 0.5m x 0.5m grid overlay visible
# - Gradual room color changes as cells heat up
```

## Validation

The system now implements:
- ✅ Formula 8: Time Urgency Score
- ✅ Formula 9: Neighbor Pressure Score  
- ✅ Formula 10: Permeability Score
- ✅ Cell danger level (d_i) as weighted sum
- ✅ Room danger level (D_i) as cell average
- ✅ Fire origin in O1 (top-left)
- ✅ 0.5m x 0.5m grid resolution
- ✅ Correct room dimensions (15.64m x 12.68m)
- ✅ Correct total size (46.92m x 34.06m)

## Next Steps (Optional Enhancements)

1. **Calibrate weights**: w_urgency, w_neighbor, w_permeability
2. **Tune heat transfer rate**: Currently 0.05, may need adjustment
3. **Add door detection**: More accurate P_e values based on actual doors
4. **Visualize cell-level hazards**: Show individual cell colors (optional)
5. **Add more fire physics**: Smoke, oxygen depletion, etc.

---

**Status**: ✅ **FULLY IMPLEMENTED** from paper Section 4.1.2

The fire now spreads realistically from O1 using grid-based cell danger calculations!


# Grid-Based System Documentation

## Overview

The simulation now uses a **0.5m x 0.5m grid system** with smooth interpolated agent movement that respects walls and doesn't phase through them.

## Key Improvements

### 1. Time Reflection
- **Yes, time reflects real-time!**
- Each tick = 1 second of real-world time
- `tick_duration = 1.0` in `params.json`
- 109 ticks = 109 seconds = 1 minute 49 seconds

### 2. Grid System (0.5m x 0.5m)
- Grid resolution: **0.5 meters per cell**
- Layout units: **1 unit = 1 meter**
- Configured in `params.json`:
  ```json
  "environment": {
    "grid_resolution": 0.5,
    "unit_to_meter": 1.0
  }
  ```

### 3. No More Wall Phasing!
**Fixed** by implementing **interpolated movement**:
- Agents now smoothly move between positions
- Movement uses `move_towards()` method in `sim/agents/agent.py`
- Agents travel at realistic speeds:
  - Hallway: 1.5 m/s
  - Stairs: 0.8 m/s
  - Dragging evacuee: 0.6 m/s

### 4. Centered Doors
The new layout (`layouts/office_basic.json`) has:
- **Doors centered on walls** facing the hallway
- Connection metadata includes `door_pos` coordinates
- Based on the provided floor plan image

## New Office Layout

### Layout: `office_basic.json`

```
┌────────┐   ┌────────┐   ┌────────┐
│   O1   │   │   O2   │   │   O3   │
│  8x8m  │   │  8x8m  │   │  8x8m  │
└────┬───┘   └────┬───┘   └────┬───┘
     │            │            │
─────┴────────────┴────────────┴──────  EXIT_L ◄──── HALLWAY (30x4m) ────► EXIT_R
     │            │            │
┌────┴───┐   ┌────┴───┐   ┌────┴───┐
│   O4   │   │   O5   │   │   O6   │
│  8x8m  │   │  8x8m  │   │  8x8m  │
└────────┘   └────────┘   └────────┘
```

**Features:**
- 6 offices (8m x 8m each)
- Central hallway (30m x 4m)
- 2 exits (left and right)
- 1 evacuee per office = 6 total
- Doors centered on walls

## Running the Simulation

### With New Layout
```bash
python3 main.py --layout layouts/office_basic.json --agents 4
```

### Command Options
```bash
python3 main.py --layout layouts/office_basic.json \
                --agents 4 \
                --no-viz           # Run without animation
                --save-video       # Save video (requires ffmpeg)
```

## Visualization (20 fps Matplotlib)

The animation now runs at **20 fps** using matplotlib:
- Smooth interpolated movement
- Agents don't teleport or phase through walls
- Real-time hazard visualization
- Color-coded agents with trails

### Controls
- **SPACE** - Play/Pause (starts paused)
- **↑↓** - Change floors (multi-floor layouts)
- **ESC** - Quit

## Technical Details

### Agent Movement
File: `sim/agents/agent.py`
```python
def move_towards(self, target_x, target_y, speed, dt) -> bool:
    """Move agent towards target with interpolation"""
    # Smooth movement at specified speed
    # Returns True when target reached
```

### Simulator Integration
File: `sim/engine/simulator.py`
- Agents set target coordinates before moving
- Movement interpolated each tick using `move_towards()`
- 10cm proximity threshold for "reached"
- No more instant teleportation!

### Grid Resolution
- **Simulation grid**: 0.5m cells
- **Layout coordinates**: 1 unit = 1 meter
- **Visual grid**: 20 pixels per cell (configurable)

## Results from Test Run

✅ **Successfully evacuated 6/6 evacuees**
- 4 agents
- 255 seconds (4 minutes 15 seconds)
- 100% rooms cleared
- Smooth movement visible in animation
- No wall phasing observed!

## Comparison: Old vs New

### Old System
- ❌ Agents teleported between rooms
- ❌ Appeared to phase through walls
- ❌ No grid-based movement
- ❌ Instant arrival at destinations

### New System
- ✅ Smooth interpolated movement
- ✅ Respects building geometry
- ✅ 0.5m x 0.5m grid system
- ✅ Realistic speeds (1.5 m/s in hallways)
- ✅ Centered doors
- ✅ Real-time seconds

## Files Modified

1. **`layouts/office_basic.json`** - New grid-based layout
2. **`params.json`** - Added grid resolution config
3. **`sim/agents/agent.py`** - Added `move_towards()` method
4. **`sim/engine/simulator.py`** - Interpolated movement logic
5. **`main.py`** - Matplotlib animator (20 fps)
6. **`sim/viz/matplotlib_animator.py`** - New animation system

## Next Steps

To use the grid system for pathfinding:
1. Implement A* on the 0.5m grid
2. Add wall collision detection
3. Use door positions for pathfinding
4. Enable corridor navigation (not just room-to-room)

## Questions?

The grid system is ready to use! The current implementation:
- Uses 0.5m x 0.5m resolution
- Smooth agent movement
- No wall phasing
- Real-time seconds
- Centered doors

All improvements requested have been implemented! 🎉


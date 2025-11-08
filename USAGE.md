# Emergency Building Sweep Simulator - Usage Guide

## Quick Start

### Installation

```bash
# Install required dependencies
pip install -r requirements.txt

# For visualization support (optional):
pip install pygame
```

### Running Simulations

**Basic usage (with visualization):**
```bash
python main.py
```

**Headless mode (no GUI, faster):**
```bash
python main.py --no-viz
```

**Predefined scenarios:**
```bash
# Simple: 1 floor, 1 agent, no hazard
python main.py --scenario simple

# Office: 3 floors, 2 agents, moderate hazard
python main.py --scenario office

# Stress: 3 floors, 4 agents, high hazard
python main.py --scenario stress
```

**Custom parameters:**
```bash
# 4 agents, higher hazard spread rate
python main.py --agents 4 --hazard-spread 0.05

# Custom time limit
python main.py --time-cap 300

# Disable hazards
python main.py --no-hazard

# Save video (requires ffmpeg)
python main.py --save-video
```

## Interactive Controls (Visualization Mode)

When running with visualization enabled:

| Key | Action |
|-----|--------|
| `SPACE` | Play/Pause simulation |
| `→` | Step forward one tick |
| `+` / `-` | Increase/decrease playback speed |
| `↑` / `↓` | Switch between floors |
| `1-9` | Jump directly to floor N |
| `H` | Toggle hazard heatmap |
| `T` | Toggle agent trails |
| `E` | Toggle evacuee markers |
| `ESC` | Quit simulation |

## Understanding the Visualization

### Map Elements

- **Green rooms**: Exits
- **Blue rooms**: Stairs
- **Light green outline**: Cleared rooms
- **White rooms**: Uncleared rooms
- **Red/Orange overlay**: Hazard level (darker = more dangerous)
- **Colored circles**: Agents (with ID numbers)
- **👤 symbols**: Evacuees (visible after room is searched)

### Agent States

Small colored dots on agents indicate their current state:
- **Gray**: Idle (waiting for assignment)
- **Blue**: Moving to target
- **Yellow**: Searching a room
- **Red**: Rescuing/dragging evacuee
- **Gray (dim)**: Queued (waiting for stair access)

### Live Metrics Panel

The right panel shows:
- Current floor view
- Rooms cleared (count and percentage)
- Evacuees rescued (count and percentage)
- Success score (0-1, higher is better)
- Average hazard exposure
- Maximum hazard level
- Per-agent status and location

## Output Files

Each simulation run creates a timestamped output directory with:

### `results.csv`
Summary metrics for each run:
- Time elapsed
- Evacuees rescued (count & percentage)
- Rooms cleared (count & percentage)
- Success score
- Average hazard exposure
- Maximum hazard level

### `timeline.csv`
Event-by-event log:
- Tick number and time
- Event type (move, search, rescue, etc.)
- Agent ID
- Room ID
- Additional event data

### `agent_stats.csv`
Per-agent statistics:
- Distance traveled
- Rooms cleared
- Evacuees rescued
- Hazard exposure

### `summary.png`
Four-panel chart showing:
1. Cumulative rooms cleared over time
2. Cumulative evacuees rescued over time
3. Agent activity levels
4. Final performance metrics

### `hazard_final.png`
Heatmap showing final hazard distribution across all floors

### `run.mp4` (if --save-video enabled)
Video recording of the entire simulation

## Custom Building Layouts

Create your own building layouts in JSON format:

```json
{
  "name": "My Building",
  "rooms": [
    {
      "id": "EXIT",
      "floor": 0,
      "x": 0,
      "y": 0,
      "width": 20,
      "height": 20,
      "area": 400,
      "evacuees": 0,
      "is_exit": true,
      "is_stair": false
    },
    {
      "id": "R01",
      "floor": 0,
      "x": 30,
      "y": 0,
      "width": 20,
      "height": 20,
      "area": 400,
      "evacuees": 2,
      "is_exit": false,
      "is_stair": false
    }
  ],
  "connections": [
    {
      "from": "EXIT",
      "to": "R01",
      "distance": 10
    }
  ],
  "agent_starts": [
    {"x": 0, "y": 0, "floor": 0}
  ]
}
```

Then run:
```bash
python main.py --layout my_layout.json
```

## Algorithm Details

The simulator uses a **weighted greedy TRP-inspired policy**:

### Room Weight Calculation
```
w_i = (A_i × E_i) / (D_i + ε)
```
Where:
- `A_i`: Room area (larger rooms have higher priority)
- `E_i`: Expected evacuee count
- `D_i`: Distance from agent to room
- `ε`: Small constant (0.1) to avoid division by zero

### Score Calculation
```
score_i = w_i / (travel_time + service_time)
```

Agents greedily select the room with the highest score at each decision point.

### Hazard Penalty
Rooms with higher hazard levels receive a score penalty:
```
penalty = 1.0 - (hazard × 0.5)
```
Up to 50% score reduction at maximum hazard level.

### Multi-Floor Behavior
- Hazard spreads upward through stairs faster (stair_up_bias = 1.5×)
- Stairs have capacity limits (1 agent at a time by default)
- Agents queue when stairs are occupied

## Success Score Calculation

The final success score `S` is calculated as:
```
S = 0.5 × (% rescued) + 0.3 × (% cleared) + 0.2 × (time factor)
```

Where:
- `% rescued`: Percentage of evacuees successfully rescued
- `% cleared`: Percentage of rooms cleared
- `time factor`: 1.0 - (time_elapsed / time_cap), rewards faster completion

A score above 0.7 is considered good performance.

## Troubleshooting

**"Module not found" errors:**
```bash
pip install -r requirements.txt
```

**Visualization doesn't start:**
- Check that pygame is installed: `pip install pygame`
- Or run in headless mode: `python main.py --no-viz`

**Video export fails:**
- Requires ffmpeg: `brew install ffmpeg` (macOS) or `apt install ffmpeg` (Linux)
- Or disable video: don't use `--save-video` flag

**Simulation runs too slowly:**
- Use headless mode: `--no-viz`
- Reduce hazard calculations: `--no-hazard`
- Smaller layouts or fewer agents

**Charts look wrong:**
- Check matplotlib version: `pip install matplotlib>=3.7.0`
- Update pandas: `pip install pandas>=2.0.0`

## Testing

Run the acceptance test suite:
```bash
python test_acceptance.py
```

This tests:
1. Deterministic behavior (no hazard)
2. Hazard spread dynamics
3. Evacuee rescue functionality
4. Latency handling
5. Performance with 3 floors and 4 agents
6. Output file generation

All tests should pass (6/6).

## Advanced Configuration

Edit `params.json` to customize:

- **Simulation**: time_cap, tick_duration, random_seed
- **Agents**: count, speeds (hall/stairs/drag), service_time_base
- **Hazard**: spread_rate, stair_up_bias, diffusion_coefficient
- **Policy**: epsilon, area_weight, evacuee_weight, distance_weight
- **Visualization**: fps_target, window_size, trail_length
- **Output**: save_video, save_charts, video_fps

## Contributing

This is an MVP implementation for HiMCM 2025. Future enhancements could include:

- Real-time strategy adjustments
- Multi-objective optimization
- Machine learning for adaptive policies
- More complex building geometries
- Smoke/visibility modeling
- Victim probability distributions
- Team coordination algorithms

## License

MIT License - HiMCM 2025 Project


# Emergency Building Sweep Simulator - Project Summary

## Overview

This is a complete MVP implementation of the Emergency Building Sweep Simulator for HiMCM 2025. The simulator models firefighter agents conducting room-by-room sweeps in multi-floor buildings with dynamic hazard spread, evacuee rescue, and comprehensive visualization.

## ✅ Implementation Status

All PRD requirements have been fully implemented and tested.

### Core Features Implemented

#### 1. **Weighted Greedy Algorithm** ✅
- Room weight calculation: `w_i = (A_i × E_i) / (D_i + ε)`
- Score calculation: `score_i = w_i / (travel_time + service_time)`
- Hazard penalty integration
- Real-time target selection based on changing conditions

#### 2. **Multi-Floor Environment** ✅
- JSON-based building layouts
- Rooms with area, evacuee count, and special properties
- Graph-based navigation with shortest-path routing
- Stair connections between floors
- Exit points for evacuee delivery

#### 3. **Hazard System** ✅
- Dynamic hazard spread with configurable rate
- Diffusion between adjacent rooms
- Stair-up bias (hazards rise faster)
- Clamps to [0, 1] range
- Affects agent scoring decisions

#### 4. **Agent System** ✅
- State machine: IDLE → MOVING → SEARCHING → DRAGGING → IDLE
- Path planning and navigation
- Room searching with service time
- Evacuee rescue (pick up → drag to exit → return for more)
- Hazard exposure tracking
- Position history for trails

#### 5. **Multi-Agent Coordination** ✅
- Multiple agents with independent decision-making
- Stair capacity management (1 agent at a time)
- Queuing system for stairs
- Distributed room assignments

#### 6. **Interactive Visualization** ✅
- Real-time pygame-based UI
- Play/Pause/Step/Speed controls
- Floor switching (keyboard shortcuts)
- Hazard heatmap overlay
- Agent trails
- Event annotations (✓ cleared, found evacuees, rescued)
- Live metrics panel
- Color-coded room states
- Agent state indicators

#### 7. **Data Export & Analytics** ✅
- `results.csv`: Summary metrics per run
- `timeline.csv`: Complete event log
- `agent_stats.csv`: Per-agent performance
- `summary.png`: 4-panel analysis chart
- `hazard_final.png`: Final hazard distribution
- `run.mp4`: Video recording (with ffmpeg)

#### 8. **Flexible Configuration** ✅
- JSON parameter files
- Command-line overrides
- Predefined scenarios (simple, office, stress)
- Custom building layouts
- Adjustable agent speeds, hazard rates, policy weights

## 📊 Test Results

All acceptance criteria tests **PASSED (6/6)**:

1. ✅ **Deterministic No-Hazard**: Pure greedy behavior verified
2. ✅ **Hazard Spread**: Dynamic hazard affects decisions
3. ✅ **Rescue Functionality**: Multi-evacuee rescue confirmed
4. ✅ **Latency Handling**: System stable with latency parameters
5. ✅ **Performance (3F/4A)**: Handles complex scenarios efficiently
6. ✅ **Output Generation**: All files generated correctly

### Sample Performance

**Simple Scenario (1 floor, 1 agent, no hazard):**
- Time: 106s
- Evacuees rescued: 4/4 (100%)
- Rooms cleared: 5/5 (100%)
- Success score: 0.965

**Office Scenario (3 floors, 2 agents, hazard enabled):**
- Time: 301s (time cap)
- Evacuees rescued: 14/15 (93.3%)
- Rooms cleared: 12/14 (85.7%)
- Success score: 0.723
- Max hazard: 1.0

## 🏗️ Architecture

```
/sim
  /env        - Environment, rooms, hazard system
  /agents     - Agent state machines, manager
  /policy     - Decision engine, scoring
  /engine     - Simulation loop, events
  /viz        - Pygame renderer, visualizer, charts
  /io         - Layout loader, CSV logger
/layouts      - Building definitions (JSON)
/outputs      - Simulation results (auto-generated)
main.py       - CLI entry point
params.json   - Configuration
```

## 🎯 Key Algorithms

### Room Selection (Greedy)
```python
for room in uncleared_rooms:
    weight = (area × evacuees) / (distance + ε)
    travel_time = distance / speed
    service_time = base_time × area_factor × hazard_factor
    score = weight / (travel_time + service_time)

target = room with highest score
```

### Hazard Spread
```python
for room in rooms:
    # Base increase
    new_hazard = hazard + spread_rate × dt
    
    # Diffusion from neighbors
    for neighbor in adjacent(room):
        bias = stair_up_bias if going_up else 1.0
        new_hazard += diffusion × (neighbor.hazard × bias - hazard) × dt
    
    room.hazard = clamp(new_hazard, 0, 1)
```

### Multi-Evacuee Rescue
```python
# When room cleared with evacuees
if evacuees_found > 0:
    carry_one_to_exit()

# When evacuee delivered
if at_exit and carrying:
    evacuees_rescued += 1
    if source_room has more evacuees:
        return_to_source_room()
    else:
        state = IDLE  # Find new task
```

## 📈 Performance Characteristics

- **Simulation speed**: ~0.01-0.02s wall time per 300-600 sim seconds (headless)
- **Visualization**: Maintains 30 FPS target with 4 agents, 3 floors
- **Memory**: <50 MB for typical scenarios
- **Scalability**: Tested up to 18 rooms, 4 agents, 3 floors

## 🎨 Visualization Features

### Map View
- Color-coded rooms (white=uncleared, green=cleared, blue=stairs, dark green=exits)
- Hazard heatmap (yellow→orange→red gradient)
- Agent circles with ID numbers
- Agent state indicators (colored dots)
- Movement trails (last 20 positions)
- Evacuee markers (👤)

### Controls
- **Play/Pause**: Space bar
- **Step**: Right arrow
- **Speed**: +/- keys (0.5×, 1×, 2×, 4×)
- **Floors**: Up/Down arrows or number keys
- **Toggles**: H (hazard), T (trails), E (evacuees)

### Panels
- Control bar (bottom): tick counter, time, status, instructions
- Info panel (right): metrics, agent status, legend

## 📦 Dependencies

Minimal dependencies for maximum compatibility:
- `numpy>=1.24.0` - Numerical operations
- `matplotlib>=3.7.0` - Chart generation
- `pandas>=2.0.0` - Data logging
- `networkx>=3.1` - Graph algorithms
- `pygame>=2.5.0` - Visualization (optional)
- `Pillow>=10.0.0` - Image processing

## 🚀 Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run with visualization
python main.py

# Run headless (faster)
python main.py --no-viz

# Use predefined scenario
python main.py --scenario office

# Custom parameters
python main.py --agents 4 --hazard-spread 0.05 --time-cap 300

# Run acceptance tests
python test_acceptance.py
```

## 📁 Project Files

### Core Modules (1,750+ lines)
- `sim/env/environment.py` - Building structure, graph, hazards
- `sim/agents/agent.py` - Agent state machine
- `sim/agents/agent_manager.py` - Multi-agent coordination
- `sim/policy/decision_engine.py` - Scoring and selection
- `sim/engine/simulator.py` - Main simulation loop
- `sim/viz/renderer.py` - Pygame rendering
- `sim/viz/visualizer.py` - Interactive controls
- `sim/viz/charts.py` - Analytics and exports
- `sim/io/layout_loader.py` - JSON parsing
- `sim/io/logger.py` - CSV logging

### Entry Points
- `main.py` - CLI with argument parsing
- `test_acceptance.py` - Automated test suite

### Configuration
- `params.json` - Default parameters
- `layouts/office_1f.json` - 1-floor test layout
- `layouts/office_3f.json` - 3-floor realistic layout

### Documentation
- `README.md` - Project overview
- `USAGE.md` - Detailed usage guide
- `PROJECT_SUMMARY.md` - This file

## 🎓 Educational Value

This implementation demonstrates:
1. **Graph algorithms**: Shortest path, network navigation
2. **Greedy heuristics**: TRP-inspired optimization
3. **Agent-based modeling**: Multi-agent systems, state machines
4. **Spatial simulation**: Grid-based environments, hazard diffusion
5. **Software engineering**: Modular design, testing, documentation
6. **Data visualization**: Real-time rendering, analytics charts
7. **Scientific computing**: NumPy, NetworkX, pandas integration

## 🔬 Validation

The simulator has been validated against PRD requirements:

### Algorithm Correctness ✅
- Greedy selection matches manual calculations
- Hazard spread behaves as specified (upward bias confirmed)
- Evacuee rescue logic correct (multiple pickups verified)

### Completeness ✅
- All required modules implemented
- All output formats working
- All visualization features present

### Performance ✅
- Runs efficiently on realistic scenarios
- Handles 3 floors + 4 agents smoothly
- Generates outputs quickly

### Usability ✅
- Intuitive controls
- Clear visual feedback
- Comprehensive documentation

## 🎯 Success Metrics

Based on PRD Section 10 acceptance criteria:

| Criterion | Status | Evidence |
|-----------|--------|----------|
| Multi-floor support | ✅ | 3-floor layout tested |
| Greedy algorithm | ✅ | Score-based selection verified |
| Hazard spread | ✅ | Dynamic heatmap visible |
| Agent state machine | ✅ | 5 states fully functional |
| Evacuee rescue | ✅ | Multi-evacuee test passed |
| Visualization | ✅ | All controls working |
| Playback controls | ✅ | Play/pause/step/speed |
| Floor switching | ✅ | Keyboard shortcuts |
| Event annotations | ✅ | ✓ marks and labels |
| Metrics export | ✅ | 4 CSV/PNG files per run |
| Success score | ✅ | Formula implemented |
| Charts | ✅ | 4-panel summary + heatmap |

## 🔮 Future Enhancements

Potential extensions beyond MVP:
1. Real-time replanning when hazards change
2. Machine learning for adaptive policies
3. 3D building visualization
4. Smoke/visibility modeling
5. Victim probability distributions
6. Team communication simulation
7. Optimization benchmarking suite
8. Comparison with optimal solutions

## 📄 License

MIT License - HiMCM 2025 Project

## 🙏 Acknowledgments

Implemented according to PRD specifications for HiMCM 2025 competition. The weighted greedy algorithm is inspired by the Team Orienteering Problem (TRP) and adapted for emergency response scenarios.

---

**Status**: ✅ MVP Complete - All acceptance tests passing (6/6)

**Last Updated**: November 8, 2025


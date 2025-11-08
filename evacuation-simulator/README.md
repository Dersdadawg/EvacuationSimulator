# Emergency Evacuation Sweep Simulator

**HiMCM 2025 Problem A — Emergency Evacuation Sweeps**

A grid-based simulation modeling emergency responders sweeping buildings to rescue evacuees under different hazard scenarios (fire, gas leak, active shooter).

## 🎯 Features

- **Dynamic Hazards**: Fire spread, gas diffusion, active shooter movement
- **Smart Agents**: 
  - Evacuees use flow-field pathfinding to exits
  - Responders use A* pathfinding with task assignment
- **Multiple Scenarios**: Office, two-floor building, school layouts
- **Visualization**: Matplotlib debugging + Blender animation export
- **Metrics**: Sweep time, evacuation success rate, hazard coverage

## 🚀 Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Run Simulation

```bash
python main.py --scenario fire --layout office
```

### Generate Blender Visualization

1. Run simulation (exports frames to `outputs/frames/`)
2. Open Blender
3. Run script: `blender/blender_import.py`

## 📊 Scenarios

- **Fire**: Spreads radially with configurable probability
- **Gas**: Diffuses throughout building, evacuees faint above threshold
- **Shooter**: Random walk biased toward visible evacuees

## 🏗 Project Structure

```
evacuation-simulator/
├── src/               # Core simulation modules
│   ├── environment.py # Grid and building layout
│   ├── agents.py      # Responders and evacuees
│   ├── hazards.py     # Fire, gas, shooter logic
│   ├── pathfinding.py # A* and flow-field algorithms
│   ├── simulation.py  # Main simulation controller
│   ├── exporter.py    # Data export
│   └── visualize.py   # Matplotlib visualization
├── blender/           # Blender animation scripts
├── data/layouts/      # Building configurations
├── outputs/           # Simulation results
└── main.py            # Entry point
```

## 📈 Metrics Tracked

- Total sweep time (timesteps)
- Evacuation success rate
- Average responder distance traveled
- Hazard coverage over time
- Number of blocked evacuees

## 🛠 Configuration

Edit parameters in simulation config or via command line:
- `fire_spread_prob`: Fire spread probability (default: 0.2)
- `gas_diffusion_rate`: Gas diffusion rate (default: 0.1)
- `vision_radius_shooter`: Shooter vision range (default: 5)
- `responder_speed`: Responder movement speed (default: 1.0)
- `evacuee_speed`: Evacuee movement speed (default: 1.0)

## 📝 License

MIT License - HiMCM 2025 Team 16955


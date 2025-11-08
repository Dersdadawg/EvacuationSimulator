"""
Main entry point for Emergency Evacuation Sweep Simulator
"""

import argparse
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.environment import Environment, create_office_layout, create_school_layout
from src.simulation import Simulation, SimulationConfig
from src.exporter import Exporter
from src.visualize import quick_visualize


def create_fire_scenario():
    """Create fire scenario in office building"""
    print("\n=== FIRE SCENARIO: Office Building ===")
    
    # Create office layout
    env = create_office_layout(50, 50)
    
    # Configure simulation
    config = SimulationConfig()
    config.fire_spread_prob = 0.05  # MUCH slower fire (was 0.2) - gives responders more time
    config.max_timesteps = 200
    
    sim = Simulation(env, config)
    
    # Add evacuees at spawn points
    sim.add_evacuees(env.spawn_points)
    
    # Add responders at entrance
    sim.add_responders([(5, 25), (45, 25)])
    
    # Add fire hazard
    fire_origin = (29, 25)  # Fire starts in one of the rooms
    sim.add_fire_hazard(fire_origin)
    
    return sim


def create_gas_scenario():
    """Create gas leak scenario in office building"""
    print("\n=== GAS SCENARIO: Office Building ===")
    
    # Create office layout
    env = create_office_layout(50, 50)
    
    # Configure simulation
    config = SimulationConfig()
    config.gas_diffusion_rate = 0.15
    config.gas_faint_threshold = 0.4
    config.max_timesteps = 600
    
    sim = Simulation(env, config)
    
    # Add evacuees at spawn points
    sim.add_evacuees(env.spawn_points)
    
    # Add responders at entrance
    sim.add_responders([(5, 25), (45, 25)])
    
    # Add gas leak
    gas_origin = (25, 20)  # Gas leak in central area
    sim.add_gas_hazard(gas_origin)
    
    return sim


def create_shooter_scenario():
    """Create active shooter scenario in school"""
    print("\n=== SHOOTER SCENARIO: School Building ===")
    
    # Create school layout
    env = create_school_layout(60, 60)
    
    # Configure simulation
    config = SimulationConfig()
    config.shooter_vision_radius = 7
    config.max_timesteps = 400
    
    sim = Simulation(env, config)
    
    # Add evacuees at spawn points
    sim.add_evacuees(env.spawn_points)
    
    # Add responders at multiple entrances
    sim.add_responders([(30, 5), (30, 55), (5, 30), (55, 30)])
    
    # Add shooter
    shooter_start = (30, 30)  # Shooter starts in center
    sim.add_shooter_hazard(shooter_start)
    
    return sim


def create_custom_scenario():
    """Create a custom small scenario for testing"""
    print("\n=== CUSTOM TEST SCENARIO ===")
    
    # Create simple environment
    env = Environment(30, 30)
    
    # Add perimeter walls
    for x in range(30):
        env.set_cell(x, 0, 0)
        env.set_cell(x, 29, 0)
    for y in range(30):
        env.set_cell(0, y, 0)
        env.set_cell(29, y, 0)
    
    # Add a simple room
    env.create_room(10, 10, 20, 20, room_id=0)
    env.create_door(15, 20)
    
    # Add exits
    env.add_exit(15, 1)
    env.add_exit(15, 28)
    
    # Configure simulation
    config = SimulationConfig()
    config.fire_spread_prob = 0.1  # Slower fire spread
    config.max_timesteps = 1000
    
    sim = Simulation(env, config)
    
    # Add evacuees INSIDE the room
    sim.add_evacuees([(15, 15)])  # Just one for testing
    
    # Add responders OUTSIDE near door
    sim.add_responders([(15, 21)])  # Right outside door
    
    # Add fire FAR from door
    sim.add_fire_hazard((10, 25))
    
    return sim


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Emergency Evacuation Sweep Simulator - HiMCM 2025"
    )
    parser.add_argument(
        '--scenario',
        type=str,
        choices=['fire', 'gas', 'shooter', 'custom', 'all'],
        default='fire',
        help='Scenario to simulate'
    )
    parser.add_argument(
        '--visualize',
        action='store_true',
        help='Show matplotlib visualization'
    )
    parser.add_argument(
        '--export',
        action='store_true',
        default=True,
        help='Export simulation data'
    )
    parser.add_argument(
        '--max-steps',
        type=int,
        default=None,
        help='Maximum simulation steps (overrides scenario default)'
    )
    
    args = parser.parse_args()
    
    # Determine which scenarios to run
    if args.scenario == 'all':
        scenarios = ['fire', 'gas', 'shooter']
    else:
        scenarios = [args.scenario]
    
    # Run each scenario
    exporter = Exporter()
    
    for scenario_name in scenarios:
        print(f"\n{'='*60}")
        print(f"Running scenario: {scenario_name.upper()}")
        print(f"{'='*60}")
        
        # Create simulation
        if scenario_name == 'fire':
            sim = create_fire_scenario()
        elif scenario_name == 'gas':
            sim = create_gas_scenario()
        elif scenario_name == 'shooter':
            sim = create_shooter_scenario()
        elif scenario_name == 'custom':
            sim = create_custom_scenario()
        else:
            print(f"Unknown scenario: {scenario_name}")
            continue
        
        # Run simulation
        metrics = sim.run(max_steps=args.max_steps)
        
        # Export data
        if args.export:
            print(f"\nExporting simulation data...")
            history = sim.get_history()
            exporter.export_all(history, metrics, scenario_name=f"{scenario_name}_scenario")
        
        # Visualize
        if args.visualize:
            print(f"\nGenerating visualization...")
            history = sim.get_history()
            quick_visualize(history, metrics, show_animation=True, show_metrics=True)
        
        print(f"\n{'='*60}")
        print(f"Scenario {scenario_name.upper()} complete!")
        print(f"{'='*60}\n")
    
    print("\n✅ All simulations complete!")
    print(f"📁 Data exported to: {exporter.output_dir}")
    print("\n📊 Next steps:")
    print("  1. Check outputs/metrics/ for CSV data")
    print("  2. Open Blender and run blender/blender_import.py to visualize")
    print("  3. Analyze results for your HiMCM report")


if __name__ == "__main__":
    main()


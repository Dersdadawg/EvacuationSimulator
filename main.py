#!/usr/bin/env python3
"""
Emergency Building Sweep Simulator - Main Entry Point
HiMCM 2025 MVP

Usage:
    python main.py                          # Run with default settings
    python main.py --layout layouts/office_3f.json
    python main.py --agents 4 --hazard-spread 0.05
    python main.py --no-viz                 # Headless mode
"""

import argparse
import json
import sys
from pathlib import Path

from sim.env.environment import Environment
from sim.engine.simulator import Simulator
from sim.viz.charts import ChartGenerator
from sim.io.layout_loader import LayoutLoader
from sim.io.logger import SimulationLogger


def load_params(params_file: str = 'params.json') -> dict:
    """Load parameters from JSON file"""
    path = Path(params_file)
    
    if not path.exists():
        print(f"Warning: {params_file} not found, using defaults")
        return get_default_params()
    
    with open(path, 'r') as f:
        return json.load(f)


def get_default_params() -> dict:
    """Get default simulation parameters"""
    return {
        "simulation": {"time_cap": 600, "tick_duration": 1.0, "random_seed": 42},
        "agents": {"count": 2, "speed_hall": 1.5, "speed_stairs": 0.8, 
                  "speed_drag": 0.6, "service_time_base": 5.0},
        "hazard": {"enabled": True, "initial_level": 0.0, "spread_rate": 0.02,
                  "stair_up_bias": 1.5, "diffusion_coefficient": 0.1},
        "latency": {"enabled": False},
        "policy": {"epsilon": 0.1, "area_weight": 1.0, "evacuee_weight": 1.0,
                  "distance_weight": 1.0},
        "visualization": {"enabled": True, "fps_target": 30, "window_width": 1600,
                         "window_height": 900, "save_video": False},
        "output": {"save_video": False, "save_charts": True}
    }


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description='Emergency Building Sweep Simulator',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py
  python main.py --layout layouts/office_3f.json --agents 4
  python main.py --no-viz --output results/test1
  python main.py --hazard-spread 0.05 --time-cap 300
        """
    )
    
    # Input/Output
    parser.add_argument('--layout', type=str, default='layouts/office_1f.json',
                       help='Path to building layout JSON file')
    parser.add_argument('--params', type=str, default='params.json',
                       help='Path to parameters JSON file')
    parser.add_argument('--output', type=str, default=None,
                       help='Output directory (auto-generated if not specified)')
    
    # Simulation parameters
    parser.add_argument('--agents', type=int, default=None,
                       help='Number of agents')
    parser.add_argument('--time-cap', type=int, default=None,
                       help='Time cap in seconds')
    parser.add_argument('--hazard-spread', type=float, default=None,
                       help='Hazard spread rate (0.0-1.0)')
    parser.add_argument('--no-hazard', action='store_true',
                       help='Disable hazard simulation')
    parser.add_argument('--seed', type=int, default=None,
                       help='Random seed')
    
    # Visualization
    parser.add_argument('--no-viz', action='store_true',
                       help='Run headless (no visualization)')
    parser.add_argument('--save-video', action='store_true',
                       help='Save video of simulation')
    
    # Quick scenarios
    parser.add_argument('--scenario', type=str, choices=['simple', 'office', 'stress'],
                       help='Load predefined scenario')
    
    return parser.parse_args()


def apply_cli_overrides(params: dict, args) -> dict:
    """Apply command line argument overrides to parameters"""
    if args.agents is not None:
        params['agents']['count'] = args.agents
    
    if args.time_cap is not None:
        params['simulation']['time_cap'] = args.time_cap
    
    if args.hazard_spread is not None:
        params['hazard']['spread_rate'] = args.hazard_spread
    
    if args.no_hazard:
        params['hazard']['enabled'] = False
    
    if args.seed is not None:
        params['simulation']['random_seed'] = args.seed
    
    if args.no_viz:
        params['visualization']['enabled'] = False
    
    if args.save_video:
        params['visualization']['save_video'] = True
        params['output']['save_video'] = True
    
    return params


def get_scenario_config(scenario: str) -> tuple:
    """Get layout and parameter overrides for predefined scenarios"""
    scenarios = {
        'simple': {
            'layout': 'layouts/office_1f.json',
            'overrides': {
                'agents': {'count': 1},
                'hazard': {'enabled': False}
            }
        },
        'office': {
            'layout': 'layouts/office_3f.json',
            'overrides': {
                'agents': {'count': 2},
                'hazard': {'spread_rate': 0.02}
            }
        },
        'stress': {
            'layout': 'layouts/office_3f.json',
            'overrides': {
                'agents': {'count': 4},
                'hazard': {'spread_rate': 0.05, 'stair_up_bias': 2.0}
            }
        }
    }
    
    config = scenarios.get(scenario)
    if not config:
        return None, {}
    
    return config['layout'], config['overrides']


def merge_params(base: dict, overrides: dict) -> dict:
    """Deep merge parameter overrides into base parameters"""
    result = base.copy()
    
    for key, value in overrides.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_params(result[key], value)
        else:
            result[key] = value
    
    return result


def run_simulation(layout_path: str, params: dict, output_dir: str = None):
    """Run a complete simulation"""
    
    print("="*60)
    print("EMERGENCY BUILDING SWEEP SIMULATOR")
    print("HiMCM 2025 MVP")
    print("="*60)
    
    # Load layout
    print(f"\nLoading layout: {layout_path}")
    try:
        layout = LayoutLoader.load(layout_path)
        print(f"Layout loaded: {layout.get('name', 'Unnamed')}")
    except FileNotFoundError:
        print(f"Error: Layout file not found: {layout_path}")
        print("Available layouts:")
        layouts_dir = Path('layouts')
        if layouts_dir.exists():
            for f in layouts_dir.glob('*.json'):
                print(f"  - {f}")
        return None
    
    # Create environment
    print("Initializing environment...")
    env = Environment(layout, params)
    print(f"  {env}")
    print(f"  Total evacuees: {env.get_total_evacuees()}")
    
    # Create simulator
    print("\nInitializing simulator...")
    sim = Simulator(env, params)
    print(f"  Agents: {len(sim.agent_manager.agents)}")
    print(f"  Time cap: {sim.time_cap}s")
    print(f"  Hazard enabled: {params['hazard']['enabled']}")
    
    # Create logger
    logger = SimulationLogger(output_dir)
    sim.add_event_callback(logger.log_event)
    print(f"  Output directory: {logger.output_dir}")
    
    # Run simulation
    viz_enabled = params.get('visualization', {}).get('enabled', True)
    
    if viz_enabled:
        print("\nStarting matplotlib animation (20 fps)...")
        print("Controls:")
        print("  SPACE: Play/Pause")
        print("  ↑↓: Change floors")
        print("  ESC: Quit")
        print()
        
        try:
            from sim.viz.matplotlib_animator import MatplotlibAnimator
            animator = MatplotlibAnimator(sim, fps=120)  # 120 FPS for ultra-smooth animation
            animator.run()
        except ImportError as e:
            print(f"Error: Visualization requires matplotlib. Install with: pip install matplotlib")
            print(f"Running in headless mode instead...")
            sim.run()
    else:
        print("\nRunning simulation (headless mode)...")
        sim.run()
        print("Simulation complete!")
    
    # Get results
    results = sim.get_results()
    
    # Log results
    logger.print_summary(results)
    logger.save_results(results)
    logger.save_timeline()
    logger.save_agent_stats(results['agents'])
    
    # Generate charts
    if params.get('output', {}).get('save_charts', True):
        print("\nGenerating charts...")
        chart_gen = ChartGenerator(str(logger.output_dir))
        chart_gen.generate_summary_charts(sim.events, results)
        chart_gen.generate_hazard_heatmap(env)
    
    print(f"\nAll outputs saved to: {logger.output_dir}")
    print("="*60)
    
    return results


def main():
    """Main entry point"""
    args = parse_args()
    
    # Load base parameters
    params = load_params(args.params)
    
    # Handle scenario shortcuts
    if args.scenario:
        layout_path, overrides = get_scenario_config(args.scenario)
        if layout_path:
            args.layout = layout_path
            params = merge_params(params, overrides)
            print(f"Loaded scenario: {args.scenario}")
    
    # Apply CLI overrides
    params = apply_cli_overrides(params, args)
    
    # Check if layout exists, if not try to create simple one
    layout_path = Path(args.layout)
    if not layout_path.exists():
        print(f"Layout {args.layout} not found.")
        
        # Try to create it if it's the default
        if args.layout == 'layouts/office_1f.json':
            print("Creating default layout...")
            layout_path.parent.mkdir(parents=True, exist_ok=True)
            layout = LayoutLoader.create_simple_layout(6, 0)
            LayoutLoader.save(layout, str(layout_path))
            print(f"Created {layout_path}")
        else:
            print("Error: Please specify a valid layout file.")
            return 1
    
    # Run simulation
    try:
        results = run_simulation(str(layout_path), params, args.output)
        
        if results is None:
            return 1
        
        # Return success code based on results
        if results['success_score'] > 0.7:
            return 0
        else:
            return 0  # Still successful run, just lower score
    
    except KeyboardInterrupt:
        print("\n\nSimulation interrupted by user.")
        return 130
    
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())


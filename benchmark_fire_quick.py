"""
Quick Fire Benchmark - Just 5 runs to test fire safety improvements
"""

import json
import time
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime

from sim.engine.simulator import Simulator
from sim.env.environment import Environment
from sim.io.layout_loader import LayoutLoader


def run_fire_test(num_agents: int, evacuees_per_room: int, run_num: int):
    """Run a single fire simulation"""
    print(f"\n{'='*60}")
    print(f"🔥 Run {run_num}/5: {num_agents} agents, {evacuees_per_room} evac/room")
    print(f"{'='*60}")
    
    # Load params
    with open("params.json") as f:
        params = json.load(f)
    
    params['agents']['count'] = num_agents
    params['visualization']['enabled'] = False
    params['hazard']['enabled'] = True  # FIRE ON!
    
    # Load and modify layout
    layout_data = LayoutLoader.load("layouts/office_correct_dimensions.json")
    for room in layout_data.get('rooms', []):
        if room.get('type') == 'office':
            room['evacuee_count'] = evacuees_per_room
    
    # Create environment and simulator
    env = Environment(layout_data, params)
    sim = Simulator(env, params)
    
    # Run simulation
    start_time = time.time()
    max_steps = 10000
    step_count = 0
    
    while not sim.complete and step_count < max_steps:
        sim.step(fire_enabled=True)
        step_count += 1
    
    elapsed = time.time() - start_time
    results = sim.get_results()
    
    # Count deaths and retreats
    num_deaths = sum(1 for a in sim.agent_manager.agents if a.is_dead)
    num_escaped = sum(1 for a in sim.agent_manager.agents if a.escaped)
    num_alive = num_agents - num_deaths
    
    print(f"✓ Time: {results['time']:.0f}s (real: {elapsed:.1f}s)")
    print(f"  Rescued: {results['evacuees_rescued']}/{results['total_evacuees']} ({results['evacuees_rescued']/results['total_evacuees']*100:.1f}%)")
    print(f"  🚒 Agents: {num_alive} alive, {num_escaped} escaped, {num_deaths} died")
    print(f"  🔥 Max Hazard: {results['max_hazard']*100:.0f}%")
    print(f"  📊 Success Score: {results['success_score']:.4f}")
    
    return {
        'num_agents': num_agents,
        'evacuees_per_room': evacuees_per_room,
        'rescued': results['evacuees_rescued'],
        'total': results['total_evacuees'],
        'rescue_rate': results['evacuees_rescued'] / results['total_evacuees'],
        'agent_deaths': num_deaths,
        'agents_escaped': num_escaped,
        'agents_alive': num_alive,
        'agent_survival_rate': num_alive / num_agents,
        'max_hazard': results['max_hazard'],
        'time': results['time'],
        'success_score': results['success_score']
    }


def main():
    print(f"\n{'='*70}")
    print(f"🔥 QUICK FIRE BENCHMARK (5 runs)")
    print(f"Testing improved fire safety with:")
    print(f"  - Slower fire spread (α_medium vs α_fast)")
    print(f"  - Higher Q_threshold (75 kW vs 50 kW)")
    print(f"  - Self-preservation retreat at danger > 0.70")
    print(f"{'='*70}")
    
    # Test configurations
    configs = [
        (1, 3),  # 1 agent, 3 evacuees/room
        (2, 3),  # 2 agents, 3 evacuees/room
        (3, 3),  # 3 agents, 3 evacuees/room
        (4, 3),  # 4 agents, 3 evacuees/room
        (5, 3),  # 5 agents, 3 evacuees/room
    ]
    
    results = []
    for i, (agents, evac) in enumerate(configs, 1):
        result = run_fire_test(agents, evac, i)
        results.append(result)
    
    # Summary
    print(f"\n{'='*70}")
    print(f"🔥 FIRE BENCHMARK COMPLETE")
    print(f"{'='*70}")
    print(f"\n{'Agents':<10}{'Rescued':<15}{'Alive':<15}{'Escaped':<15}{'Deaths':<10}")
    print(f"{'-'*70}")
    for r in results:
        print(f"{r['num_agents']:<10}{r['rescued']}/{r['total']:<13}"
              f"{r['agents_alive']}/{r['num_agents']:<13}"
              f"{r['agents_escaped']:<15}{r['agent_deaths']:<10}")
    
    # Save results
    output_path = Path("benchmark_results")
    output_path.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    filepath = output_path / f"fire_quick_{timestamp}.json"
    with open(filepath, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n✓ Results saved to: {filepath}")


if __name__ == "__main__":
    main()


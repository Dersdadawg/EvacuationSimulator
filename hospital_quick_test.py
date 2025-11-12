"""
Quick Hospital Simulation Tests
Run hospital layout with various responder counts
"""

import json
import time
from sim.engine.simulator import Simulator
from sim.env.environment import Environment
from sim.io.layout_loader import LayoutLoader


def run_hospital_test(num_responders: int, with_fire: bool = False):
    """Run single hospital simulation"""
    # Load params
    with open("params.json") as f:
        params = json.load(f)
    
    params['agents']['count'] = num_responders
    params['visualization']['enabled'] = False
    params['hazard']['enabled'] = with_fire
    
    # Load hospital layout
    layout_data = LayoutLoader.load("layouts/hospital_complex.json")
    env = Environment(layout_data, params)
    sim = Simulator(env, params)
    
    # Run simulation
    start = time.time()
    while not sim.complete and sim.tick < 15000:
        sim.step(fire_enabled=with_fire)
    
    elapsed = time.time() - start
    results = sim.get_results()
    
    # Count responder stats
    num_alive = sum(1 for a in sim.agent_manager.agents if not a.is_dead)
    num_escaped = sum(1 for a in sim.agent_manager.agents if a.escaped)
    num_deaths = num_responders - num_alive
    
    return {
        'responders': num_responders,
        'fire': with_fire,
        'time': results['time'],
        'real_time': elapsed,
        'rescued': results['evacuees_rescued'],
        'total': results['total_evacuees'],
        'rescue_pct': results['evacuees_rescued'] / results['total_evacuees'] * 100,
        'rooms_cleared': results['rooms_cleared'],
        'total_rooms': results['total_rooms'],
        'success_score': results['success_score'],
        'responders_alive': num_alive,
        'responders_escaped': num_escaped,
        'responder_deaths': num_deaths
    }


def main():
    print("="*70)
    print("🏥 HOSPITAL COMPLEX - QUICK TESTS")
    print("="*70)
    print("Building: 71.80m × 52.11m, 8 patient areas, 100 occupants")
    print()
    
    # Test without fire
    print("📊 TESTS WITHOUT FIRE:")
    print("-"*70)
    print(f"{'Resp':<6}{'Time':<12}{'Rescued':<15}{'Success':<12}{'Real Time':<12}")
    print("-"*70)
    
    no_fire_results = []
    for num in [4, 6, 8, 10]:
        result = run_hospital_test(num, with_fire=False)
        no_fire_results.append(result)
        print(f"{result['responders']:<6}"
              f"{result['time']:.0f}s ({result['time']/60:.1f}m){'':<2}"
              f"{result['rescued']}/{result['total']:<11}"
              f"{result['success_score']:<12.4f}"
              f"{result['real_time']:<12.2f}s")
    
    print()
    
    # Test with fire
    print("🔥 TESTS WITH FIRE:")
    print("-"*70)
    print(f"{'Resp':<6}{'Time':<12}{'Rescued':<15}{'Deaths':<10}{'Success':<12}")
    print("-"*70)
    
    fire_results = []
    for num in [4, 6, 8]:
        result = run_hospital_test(num, with_fire=True)
        fire_results.append(result)
        print(f"{result['responders']:<6}"
              f"{result['time']:.0f}s ({result['time']/60:.1f}m){'':<2}"
              f"{result['rescued']}/{result['total']:<11}"
              f"{result['responder_deaths']}/{result['responders']:<8}"
              f"{result['success_score']:<12.4f}")
    
    print()
    print("="*70)
    print("✓ Hospital tests complete!")
    print()
    
    # Summary
    print("💡 KEY FINDINGS:")
    print(f"  No Fire - Optimal: {no_fire_results[0]['responders']} responders, "
          f"{no_fire_results[0]['time']/60:.1f} min sweep")
    print(f"  With Fire - Best: {fire_results[0]['responders']} responders, "
          f"{fire_results[0]['rescued']}/{fire_results[0]['total']} rescued, "
          f"{fire_results[0]['responder_deaths']} deaths")


if __name__ == "__main__":
    main()


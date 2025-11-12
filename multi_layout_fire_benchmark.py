"""
Multi-Layout Fire Benchmark
Run fire simulations across different building layouts and compare results
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


def run_fire_simulation(layout_path: str, num_agents: int, evacuees_per_room: int = 3):
    """Run a single fire simulation"""
    
    # Load params
    with open("params.json") as f:
        params = json.load(f)
    
    params['agents']['count'] = num_agents
    params['visualization']['enabled'] = False
    params['hazard']['enabled'] = True  # Enable fire
    
    # Load and modify layout
    layout_data = LayoutLoader.load(layout_path)
    for room in layout_data.get('rooms', []):
        if room.get('type') in ['office', 'hospital_room', 'classroom']:
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
    
    # Count deaths and survival
    num_deaths = sum(1 for a in sim.agent_manager.agents if a.is_dead)
    num_escaped = sum(1 for a in sim.agent_manager.agents if a.escaped)
    num_alive = num_agents - num_deaths
    
    return {
        'num_agents': num_agents,
        'evacuees_per_room': evacuees_per_room,
        'total_evacuees': results['total_evacuees'],
        'evacuees_rescued': results['evacuees_rescued'],
        'evacuees_trapped': results['total_evacuees'] - results['evacuees_rescued'],
        'rescue_rate': results['evacuees_rescued'] / results['total_evacuees'] if results['total_evacuees'] > 0 else 0,
        'agent_deaths': num_deaths,
        'agents_escaped': num_escaped,
        'agents_alive': num_alive,
        'agent_survival_rate': num_alive / num_agents if num_agents > 0 else 0,
        'max_hazard': results['max_hazard'],
        'simulation_time': results['time'],
        'success_score': results['success_score'],
        'rooms_cleared': results['rooms_cleared'],
        'total_rooms': len([r for r in layout_data.get('rooms', []) if r.get('type') != 'hallway']),
        'real_time': elapsed
    }


def run_layout_benchmark(layout_path: str, layout_name: str, agent_counts: list, repetitions: int = 2):
    """Run fire benchmark for a single layout"""
    print(f"\n{'='*70}")
    print(f"🔥 FIRE BENCHMARK: {layout_name}")
    print(f"{'='*70}")
    
    results = []
    total_runs = len(agent_counts) * repetitions
    current_run = 0
    
    for num_agents in agent_counts:
        for rep in range(repetitions):
            current_run += 1
            print(f"\n[{current_run}/{total_runs}] {num_agents} agents, run {rep+1}/{repetitions}...", end=" ", flush=True)
            
            try:
                result = run_fire_simulation(layout_path, num_agents, evacuees_per_room=3)
                results.append(result)
                print(f"✓ Rescued: {result['evacuees_rescued']}/{result['total_evacuees']} ({result['rescue_rate']*100:.1f}%), "
                      f"Agents alive: {result['agents_alive']}/{num_agents}")
            except Exception as e:
                print(f"✗ Error: {e}")
    
    return results


def aggregate_layout_data(results):
    """Aggregate results by agent count"""
    aggregated = {}
    
    for entry in results:
        agents = entry['num_agents']
        if agents not in aggregated:
            aggregated[agents] = []
        aggregated[agents].append(entry)
    
    # Compute averages
    summary = {}
    for agents, entries in aggregated.items():
        summary[agents] = {
            'rescue_rate': np.mean([e['rescue_rate'] for e in entries]),
            'rescue_rate_std': np.std([e['rescue_rate'] for e in entries]),
            'agent_survival': np.mean([e['agent_survival_rate'] for e in entries]),
            'agent_survival_std': np.std([e['agent_survival_rate'] for e in entries]),
            'success_score': np.mean([e['success_score'] for e in entries]),
            'success_score_std': np.std([e['success_score'] for e in entries]),
            'evacuees_rescued': np.mean([e['evacuees_rescued'] for e in entries]),
            'agent_deaths': np.mean([e['agent_deaths'] for e in entries]),
            'total_evacuees': entries[0]['total_evacuees'],
            'total_rooms': entries[0]['total_rooms'],
        }
    
    return summary


def create_comparison_graphs(all_results, layouts_info):
    """Create comparison graphs across all layouts"""
    
    print("\n" + "="*70)
    print("📊 GENERATING COMPARISON GRAPHS")
    print("="*70)
    
    plt.style.use('seaborn-v0_8-darkgrid')
    fig = plt.figure(figsize=(20, 12), facecolor='#FAFAFA')
    
    colors = {
        'Office': '#FF6B35',
        'Hospital': '#1976D2',
        'School': '#43A047'
    }
    
    markers = {
        'Office': 'o',
        'Hospital': 's',
        'School': '^'
    }
    
    # 1. Rescue Rate Comparison
    ax1 = plt.subplot(2, 3, 1)
    ax1.set_facecolor('#FFFFFF')
    
    for layout_name, summary in all_results.items():
        agents = sorted(summary.keys())
        rescue_rates = [summary[a]['rescue_rate'] * 100 for a in agents]
        rescue_stds = [summary[a]['rescue_rate_std'] * 100 for a in agents]
        
        ax1.errorbar(agents, rescue_rates, yerr=rescue_stds,
                    marker=markers[layout_name], linewidth=2.5, markersize=10,
                    label=layout_name, color=colors[layout_name],
                    capsize=5, capthick=2, markeredgecolor='white', markeredgewidth=1.5)
    
    ax1.set_xlabel('Number of Agents', fontweight='bold', fontsize=12)
    ax1.set_ylabel('Rescue Rate (%)', fontweight='bold', fontsize=12)
    ax1.set_title('Rescue Rate by Building Type', fontweight='bold', fontsize=14, pad=12)
    ax1.legend(frameon=True, fancybox=True, shadow=True, fontsize=11)
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.set_ylim(0, 105)
    
    # 2. Agent Survival Rate Comparison
    ax2 = plt.subplot(2, 3, 2)
    ax2.set_facecolor('#FFFFFF')
    
    for layout_name, summary in all_results.items():
        agents = sorted(summary.keys())
        survival_rates = [summary[a]['agent_survival'] * 100 for a in agents]
        survival_stds = [summary[a]['agent_survival_std'] * 100 for a in agents]
        
        ax2.errorbar(agents, survival_rates, yerr=survival_stds,
                    marker=markers[layout_name], linewidth=2.5, markersize=10,
                    label=layout_name, color=colors[layout_name],
                    capsize=5, capthick=2, markeredgecolor='white', markeredgewidth=1.5)
    
    ax2.set_xlabel('Number of Agents', fontweight='bold', fontsize=12)
    ax2.set_ylabel('Agent Survival Rate (%)', fontweight='bold', fontsize=12)
    ax2.set_title('Agent Survival Rate by Building Type', fontweight='bold', fontsize=14, pad=12)
    ax2.legend(frameon=True, fancybox=True, shadow=True, fontsize=11)
    ax2.grid(True, alpha=0.3, linestyle='--')
    ax2.set_ylim(0, 105)
    
    # 3. Success Score Comparison
    ax3 = plt.subplot(2, 3, 3)
    ax3.set_facecolor('#FFFFFF')
    
    for layout_name, summary in all_results.items():
        agents = sorted(summary.keys())
        success_scores = [summary[a]['success_score'] for a in agents]
        success_stds = [summary[a]['success_score_std'] for a in agents]
        
        ax3.errorbar(agents, success_scores, yerr=success_stds,
                    marker=markers[layout_name], linewidth=2.5, markersize=10,
                    label=layout_name, color=colors[layout_name],
                    capsize=5, capthick=2, markeredgecolor='white', markeredgewidth=1.5)
    
    ax3.set_xlabel('Number of Agents', fontweight='bold', fontsize=12)
    ax3.set_ylabel('Success Score', fontweight='bold', fontsize=12)
    ax3.set_title('Success Score by Building Type', fontweight='bold', fontsize=14, pad=12)
    ax3.legend(frameon=True, fancybox=True, shadow=True, fontsize=11)
    ax3.grid(True, alpha=0.3, linestyle='--')
    
    # 4. Building Characteristics
    ax4 = plt.subplot(2, 3, 4)
    ax4.set_facecolor('#FFFFFF')
    
    building_names = list(all_results.keys())
    total_evacuees = [list(summary.values())[0]['total_evacuees'] for summary in all_results.values()]
    total_rooms = [list(summary.values())[0]['total_rooms'] for summary in all_results.values()]
    
    x = np.arange(len(building_names))
    width = 0.35
    
    bars1 = ax4.bar(x - width/2, total_evacuees, width, label='Evacuees',
                   color=[colors[name] for name in building_names],
                   edgecolor='#212121', linewidth=2, alpha=0.85)
    bars2 = ax4.bar(x + width/2, total_rooms, width, label='Rooms',
                   color=[colors[name] for name in building_names],
                   edgecolor='#212121', linewidth=2, alpha=0.5)
    
    ax4.set_ylabel('Count', fontweight='bold', fontsize=12)
    ax4.set_title('Building Size Comparison', fontweight='bold', fontsize=14, pad=12)
    ax4.set_xticks(x)
    ax4.set_xticklabels(building_names)
    ax4.legend(frameon=True, fancybox=True, shadow=True, fontsize=11)
    ax4.grid(True, alpha=0.3, axis='y', linestyle='--')
    
    # Add value labels on bars
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height,
                    f'{int(height)}', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # 5. Agent Deaths Comparison
    ax5 = plt.subplot(2, 3, 5)
    ax5.set_facecolor('#FFFFFF')
    
    for layout_name, summary in all_results.items():
        agents = sorted(summary.keys())
        deaths = [summary[a]['agent_deaths'] for a in agents]
        
        ax5.plot(agents, deaths, marker=markers[layout_name], linewidth=2.5, markersize=10,
                label=layout_name, color=colors[layout_name],
                markeredgecolor='white', markeredgewidth=1.5)
    
    ax5.set_xlabel('Number of Agents', fontweight='bold', fontsize=12)
    ax5.set_ylabel('Average Agent Deaths', fontweight='bold', fontsize=12)
    ax5.set_title('Agent Deaths by Building Type', fontweight='bold', fontsize=14, pad=12)
    ax5.legend(frameon=True, fancybox=True, shadow=True, fontsize=11)
    ax5.grid(True, alpha=0.3, linestyle='--')
    
    # 6. Summary Statistics
    ax6 = plt.subplot(2, 3, 6)
    ax6.set_facecolor('#FFFFFF')
    ax6.axis('off')
    
    summary_text = "FIRE SAFETY COMPARISON\n"
    summary_text += "═" * 45 + "\n\n"
    
    for layout_name, summary in all_results.items():
        # Find best configuration for this layout
        best_agents = max(summary.keys(), key=lambda a: summary[a]['rescue_rate'])
        summary_text += f"{layout_name}:\n"
        summary_text += f"  Occupants: {summary[best_agents]['total_evacuees']}\n"
        summary_text += f"  Rooms: {summary[best_agents]['total_rooms']}\n"
        summary_text += f"  Best: {best_agents} agents\n"
        summary_text += f"    Rescue: {summary[best_agents]['rescue_rate']*100:.1f}%\n"
        summary_text += f"    Agent Survival: {summary[best_agents]['agent_survival']*100:.1f}%\n"
        summary_text += f"    Deaths: {summary[best_agents]['agent_deaths']:.1f}\n\n"
    
    ax6.text(0.5, 0.5, summary_text, transform=ax6.transAxes,
            fontsize=10, verticalalignment='center', horizontalalignment='center',
            bbox=dict(boxstyle='round,pad=1.5', facecolor='#FFEBEE',
                     edgecolor='#C62828', linewidth=3, alpha=0.95),
            fontfamily='monospace', fontweight='600')
    
    # Main title
    fig.suptitle('FIRE EVACUATION: MULTI-BUILDING COMPARISON',
                fontsize=20, fontweight='bold', y=0.98,
                bbox=dict(boxstyle='round,pad=0.8', facecolor='#E53935',
                         edgecolor='none', alpha=1.0),
                color='white')
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    # Save
    output_path = Path("benchmark_results")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = output_path / f"multi_layout_fire_comparison_{timestamp}.png"
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"\n✓ Comparison graph saved: {filepath}")
    
    return filepath


def main():
    """Main function"""
    print("="*70)
    print("🔥 MULTI-LAYOUT FIRE BENCHMARK")
    print("="*70)
    print("\nTesting fire evacuation across different building types:")
    print("  - Office Building")
    print("  - Hospital Complex")
    print("  - School Building")
    print("\nEach with varying numbers of first responders")
    print("="*70)
    
    # Define layouts to test
    layouts = {
        'Office': {
            'path': 'layouts/office_correct_dimensions.json',
            'agent_counts': [1, 2, 3, 4, 5]
        },
        'Hospital': {
            'path': 'layouts/hospital_complex.json',
            'agent_counts': [4, 6, 8, 10, 12]
        },
        'School': {
            'path': 'layouts/school_building.json',
            'agent_counts': [6, 8, 10, 12, 15]
        }
    }
    
    all_results = {}
    all_raw_data = {}
    
    # Run benchmarks for each layout
    for layout_name, config in layouts.items():
        results = run_layout_benchmark(
            config['path'],
            layout_name,
            config['agent_counts'],
            repetitions=2
        )
        all_raw_data[layout_name] = results
        all_results[layout_name] = aggregate_layout_data(results)
    
    # Create comparison graphs
    output_file = create_comparison_graphs(all_results, layouts)
    
    # Save all data to JSON
    output_path = Path("benchmark_results")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    data_file = output_path / f"multi_layout_fire_data_{timestamp}.json"
    
    with open(data_file, 'w') as f:
        json.dump(all_raw_data, f, indent=2)
    
    print(f"✓ Data saved: {data_file}")
    
    # Print final summary
    print("\n" + "="*70)
    print("FINAL SUMMARY")
    print("="*70)
    
    for layout_name, summary in all_results.items():
        best_agents = max(summary.keys(), key=lambda a: summary[a]['rescue_rate'])
        print(f"\n{layout_name}:")
        print(f"  Total Occupants: {summary[best_agents]['total_evacuees']}")
        print(f"  Total Rooms: {summary[best_agents]['total_rooms']}")
        print(f"  Best Configuration: {best_agents} agents")
        print(f"    Rescue Rate: {summary[best_agents]['rescue_rate']*100:.1f}%")
        print(f"    Agent Survival: {summary[best_agents]['agent_survival']*100:.1f}%")
        print(f"    Agent Deaths: {summary[best_agents]['agent_deaths']:.1f}")
        print(f"    Success Score: {summary[best_agents]['success_score']:.4f}")
    
    print("\n" + "="*70)
    print("✓ MULTI-LAYOUT FIRE BENCHMARK COMPLETE")
    print("="*70)


if __name__ == "__main__":
    main()


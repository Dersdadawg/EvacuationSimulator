"""
Generate comprehensive fire benchmark graphs
Shows performance across different agent counts and evacuees per room
"""

import json
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime


def load_fire_data(filepath):
    """Load fire benchmark data"""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return data


def aggregate_data(data):
    """Aggregate data by configuration (num_agents, evacuees_per_room)"""
    aggregated = {}
    
    for entry in data:
        key = (entry['num_agents'], entry['evacuees_per_room'])
        if key not in aggregated:
            aggregated[key] = []
        aggregated[key].append(entry)
    
    # Compute averages
    results = {}
    for key, entries in aggregated.items():
        results[key] = {
            'num_agents': key[0],
            'evacuees_per_room': key[1],
            'rescue_rate_mean': np.mean([e['rescue_rate'] for e in entries]),
            'rescue_rate_std': np.std([e['rescue_rate'] for e in entries]),
            'evacuees_rescued_mean': np.mean([e['evacuees_rescued'] for e in entries]),
            'evacuees_trapped_mean': np.mean([e['evacuees_trapped'] for e in entries]),
            'success_score_mean': np.mean([e['success_score'] for e in entries]),
            'success_score_std': np.std([e['success_score'] for e in entries]),
            'agent_survival_mean': np.mean([e['agent_survival_rate'] for e in entries]),
            'agent_survival_std': np.std([e['agent_survival_rate'] for e in entries]),
            'agent_deaths_mean': np.mean([e['agent_deaths'] for e in entries]),
            'time_mean': np.mean([e['simulation_time'] for e in entries]),
            'time_std': np.std([e['simulation_time'] for e in entries]),
            'rooms_cleared_mean': np.mean([e['rooms_cleared'] for e in entries]),
            'total_distance_mean': np.mean([e['total_distance'] for e in entries]),
            'avg_path_length_mean': np.mean([e['avg_path_length'] for e in entries]),
        }
    
    return results


def create_fire_graphs(fire_data_file):
    """Create comprehensive fire benchmark graphs"""
    
    print(f"Loading fire data from {fire_data_file}...")
    data = load_fire_data(fire_data_file)
    
    print(f"Aggregating {len(data)} data points...")
    results = aggregate_data(data)
    
    # Get unique agent counts and evacuees per room
    agent_counts = sorted(set(k[0] for k in results.keys()))
    evac_per_room_counts = sorted(set(k[1] for k in results.keys()))
    
    print(f"Agent counts: {agent_counts}")
    print(f"Evacuees per room: {evac_per_room_counts}")
    
    # Set up the plot style
    plt.style.use('seaborn-v0_8-darkgrid')
    
    # Create comprehensive figure
    fig = plt.figure(figsize=(20, 16), facecolor='#FAFAFA')
    
    # Color palette
    colors = ['#E53935', '#1E88E5', '#43A047', '#FB8C00', '#8E24AA']
    
    # 1. Rescue Rate by Number of Agents
    ax1 = plt.subplot(3, 3, 1)
    ax1.set_facecolor('#FFFFFF')
    
    for i, evac in enumerate(evac_per_room_counts):
        x = []
        y = []
        yerr = []
        for agents in agent_counts:
            if (agents, evac) in results:
                x.append(agents)
                y.append(results[(agents, evac)]['rescue_rate_mean'] * 100)
                yerr.append(results[(agents, evac)]['rescue_rate_std'] * 100)
        
        if x:  # Only plot if we have data
            ax1.errorbar(x, y, yerr=yerr, marker='o', linewidth=2.5, markersize=8,
                        label=f'{evac} evac/room', color=colors[i % len(colors)],
                        capsize=5, capthick=2, markeredgecolor='white', markeredgewidth=1.5,
                        alpha=0.8)
    
    ax1.set_xlabel('Number of Agents', fontweight='bold', fontsize=11)
    ax1.set_ylabel('Rescue Rate (%)', fontweight='bold', fontsize=11)
    ax1.set_title('🚨 Rescue Rate vs Number of Agents', fontweight='bold', fontsize=13, pad=12)
    ax1.legend(frameon=True, fancybox=True, shadow=True, loc='best')
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.set_ylim(0, 105)
    
    # 2. Agent Survival Rate by Number of Agents
    ax2 = plt.subplot(3, 3, 2)
    ax2.set_facecolor('#FFFFFF')
    
    line_styles = ['-', '--', '-.', ':']
    for i, evac in enumerate(evac_per_room_counts):
        x = []
        y = []
        yerr = []
        for agents in agent_counts:
            if (agents, evac) in results:
                x.append(agents)
                y.append(results[(agents, evac)]['agent_survival_mean'] * 100)
                yerr.append(results[(agents, evac)]['agent_survival_std'] * 100)
        
        if x:  # Only plot if we have data
            ax2.errorbar(x, y, yerr=yerr, marker='s', linewidth=2.5, markersize=8,
                        label=f'{evac} evac/room', color=colors[i % len(colors)],
                        capsize=5, capthick=2, markeredgecolor='white', markeredgewidth=1.5,
                        linestyle=line_styles[i % len(line_styles)], alpha=0.8)
    
    ax2.set_xlabel('Number of Agents', fontweight='bold', fontsize=11)
    ax2.set_ylabel('Agent Survival Rate (%)', fontweight='bold', fontsize=11)
    ax2.set_title('🚒 Agent Survival Rate vs Number of Agents', fontweight='bold', fontsize=13, pad=12)
    ax2.legend(frameon=True, fancybox=True, shadow=True, loc='best')
    ax2.grid(True, alpha=0.3, linestyle='--')
    ax2.set_ylim(0, 105)
    
    # 3. Success Score by Number of Agents
    ax3 = plt.subplot(3, 3, 3)
    ax3.set_facecolor('#FFFFFF')
    
    markers_list = ['^', 'o', 's', 'D']
    for i, evac in enumerate(evac_per_room_counts):
        x = []
        y = []
        yerr = []
        for agents in agent_counts:
            if (agents, evac) in results:
                x.append(agents)
                y.append(results[(agents, evac)]['success_score_mean'])
                yerr.append(results[(agents, evac)]['success_score_std'])
        
        if x:  # Only plot if we have data
            ax3.errorbar(x, y, yerr=yerr, marker=markers_list[i % len(markers_list)], 
                        linewidth=2.5, markersize=8,
                        label=f'{evac} evac/room', color=colors[i % len(colors)],
                        capsize=5, capthick=2, markeredgecolor='white', markeredgewidth=1.5,
                        alpha=0.8)
    
    ax3.set_xlabel('Number of Agents', fontweight='bold', fontsize=11)
    ax3.set_ylabel('Success Score', fontweight='bold', fontsize=11)
    ax3.set_title('📊 Success Score vs Number of Agents', fontweight='bold', fontsize=13, pad=12)
    ax3.legend(frameon=True, fancybox=True, shadow=True, loc='best')
    ax3.grid(True, alpha=0.3, linestyle='--')
    
    # 4. Agent Deaths by Number of Agents
    ax4 = plt.subplot(3, 3, 4)
    ax4.set_facecolor('#FFFFFF')
    
    for i, evac in enumerate(evac_per_room_counts):
        x = []
        y = []
        for agents in agent_counts:
            if (agents, evac) in results:
                x.append(agents)
                y.append(results[(agents, evac)]['agent_deaths_mean'])
        
        if x:  # Only plot if we have data
            ax4.plot(x, y, marker=markers_list[i % len(markers_list)], linewidth=2.5, markersize=8,
                    label=f'{evac} evac/room', color=colors[i % len(colors)],
                    markeredgecolor='white', markeredgewidth=1.5,
                    linestyle=line_styles[i % len(line_styles)], alpha=0.8)
    
    ax4.set_xlabel('Number of Agents', fontweight='bold', fontsize=11)
    ax4.set_ylabel('Average Agent Deaths', fontweight='bold', fontsize=11)
    ax4.set_title('☠️ Agent Deaths vs Number of Agents', fontweight='bold', fontsize=13, pad=12)
    ax4.legend(frameon=True, fancybox=True, shadow=True, loc='best')
    ax4.grid(True, alpha=0.3, linestyle='--')
    
    # 5. Evacuees Rescued by Number of Agents
    ax5 = plt.subplot(3, 3, 5)
    ax5.set_facecolor('#FFFFFF')
    
    for i, evac in enumerate(evac_per_room_counts):
        x = []
        y = []
        for agents in agent_counts:
            if (agents, evac) in results:
                x.append(agents)
                y.append(results[(agents, evac)]['evacuees_rescued_mean'])
        
        if x:  # Only plot if we have data
            ax5.plot(x, y, marker=markers_list[i % len(markers_list)], linewidth=2.5, markersize=8,
                    label=f'{evac} evac/room', color=colors[i % len(colors)],
                    markeredgecolor='white', markeredgewidth=1.5,
                    linestyle=line_styles[i % len(line_styles)], alpha=0.8)
    
    ax5.set_xlabel('Number of Agents', fontweight='bold', fontsize=11)
    ax5.set_ylabel('Evacuees Rescued', fontweight='bold', fontsize=11)
    ax5.set_title('👥 Evacuees Rescued vs Number of Agents', fontweight='bold', fontsize=13, pad=12)
    ax5.legend(frameon=True, fancybox=True, shadow=True, loc='best')
    ax5.grid(True, alpha=0.3, linestyle='--')
    
    # 6. Simulation Time by Number of Agents
    ax6 = plt.subplot(3, 3, 6)
    ax6.set_facecolor('#FFFFFF')
    
    for i, evac in enumerate(evac_per_room_counts):
        x = []
        y = []
        yerr = []
        for agents in agent_counts:
            if (agents, evac) in results:
                x.append(agents)
                y.append(results[(agents, evac)]['time_mean'])
                yerr.append(results[(agents, evac)]['time_std'])
        
        if x:  # Only plot if we have data
            ax6.errorbar(x, y, yerr=yerr, marker=markers_list[i % len(markers_list)], 
                        linewidth=2.5, markersize=8,
                        label=f'{evac} evac/room', color=colors[i % len(colors)],
                        capsize=5, capthick=2, markeredgecolor='white', markeredgewidth=1.5,
                        linestyle=line_styles[i % len(line_styles)], alpha=0.8)
    
    ax6.set_xlabel('Number of Agents', fontweight='bold', fontsize=11)
    ax6.set_ylabel('Simulation Time (steps)', fontweight='bold', fontsize=11)
    ax6.set_title('⏱️ Simulation Time vs Number of Agents', fontweight='bold', fontsize=13, pad=12)
    ax6.legend(frameon=True, fancybox=True, shadow=True, loc='best')
    ax6.grid(True, alpha=0.3, linestyle='--')
    
    # 7. Rooms Cleared by Number of Agents
    ax7 = plt.subplot(3, 3, 7)
    ax7.set_facecolor('#FFFFFF')
    
    for i, evac in enumerate(evac_per_room_counts):
        x = []
        y = []
        for agents in agent_counts:
            if (agents, evac) in results:
                x.append(agents)
                y.append(results[(agents, evac)]['rooms_cleared_mean'])
        
        if x:  # Only plot if we have data
            ax7.plot(x, y, marker=markers_list[i % len(markers_list)], linewidth=2.5, markersize=8,
                    label=f'{evac} evac/room', color=colors[i % len(colors)],
                    markeredgecolor='white', markeredgewidth=1.5,
                    linestyle=line_styles[i % len(line_styles)], alpha=0.8)
    
    ax7.set_xlabel('Number of Agents', fontweight='bold', fontsize=11)
    ax7.set_ylabel('Rooms Cleared', fontweight='bold', fontsize=11)
    ax7.set_title('🏠 Rooms Cleared vs Number of Agents', fontweight='bold', fontsize=13, pad=12)
    ax7.legend(frameon=True, fancybox=True, shadow=True, loc='best')
    ax7.grid(True, alpha=0.3, linestyle='--')
    
    # 8. Average Path Length by Number of Agents
    ax8 = plt.subplot(3, 3, 8)
    ax8.set_facecolor('#FFFFFF')
    
    for i, evac in enumerate(evac_per_room_counts):
        x = []
        y = []
        for agents in agent_counts:
            if (agents, evac) in results:
                x.append(agents)
                y.append(results[(agents, evac)]['avg_path_length_mean'])
        
        if x:  # Only plot if we have data
            ax8.plot(x, y, marker=markers_list[i % len(markers_list)], linewidth=2.5, markersize=8,
                    label=f'{evac} evac/room', color=colors[i % len(colors)],
                    markeredgecolor='white', markeredgewidth=1.5,
                    linestyle=line_styles[i % len(line_styles)], alpha=0.8)
    
    ax8.set_xlabel('Number of Agents', fontweight='bold', fontsize=11)
    ax8.set_ylabel('Avg Path Length', fontweight='bold', fontsize=11)
    ax8.set_title('📏 Average Path Length per Agent', fontweight='bold', fontsize=13, pad=12)
    ax8.legend(frameon=True, fancybox=True, shadow=True, loc='best')
    ax8.grid(True, alpha=0.3, linestyle='--')
    
    # 9. Summary Statistics Table
    ax9 = plt.subplot(3, 3, 9)
    ax9.set_facecolor('#FFFFFF')
    ax9.axis('off')
    
    # Find best configuration
    best_rescue = max(results.items(), key=lambda x: x[1]['rescue_rate_mean'])
    best_survival = max(results.items(), key=lambda x: x[1]['agent_survival_mean'])
    best_success = max(results.items(), key=lambda x: x[1]['success_score_mean'])
    
    summary = "FIRE BENCHMARK SUMMARY\n"
    summary += "═" * 40 + "\n\n"
    summary += f"Best Rescue Rate:\n"
    summary += f"  {best_rescue[0][0]} agents, {best_rescue[0][1]} evac/room\n"
    summary += f"  {best_rescue[1]['rescue_rate_mean']*100:.1f}% rescued\n\n"
    
    summary += f"Best Agent Survival:\n"
    summary += f"  {best_survival[0][0]} agents, {best_survival[0][1]} evac/room\n"
    summary += f"  {best_survival[1]['agent_survival_mean']*100:.1f}% survived\n\n"
    
    summary += f"Best Success Score:\n"
    summary += f"  {best_success[0][0]} agents, {best_success[0][1]} evac/room\n"
    summary += f"  Score: {best_success[1]['success_score_mean']:.4f}\n"
    
    ax9.text(0.5, 0.5, summary, transform=ax9.transAxes,
            fontsize=11, verticalalignment='center', horizontalalignment='center',
            bbox=dict(boxstyle='round,pad=1.5', facecolor='#FFEBEE',
                     edgecolor='#C62828', linewidth=3, alpha=0.95),
            fontfamily='monospace', fontweight='600')
    
    # Add main title
    fig.suptitle('🔥 FIRE EVACUATION BENCHMARK ANALYSIS 🔥',
                fontsize=20, fontweight='bold', y=0.98,
                bbox=dict(boxstyle='round,pad=0.8', facecolor='#E53935',
                         edgecolor='none', alpha=1.0),
                color='white')
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    # Save
    output_path = Path("benchmark_results")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = output_path / f"fire_analysis_{timestamp}.png"
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()
    
    print(f"\n✓ Graph saved: {filepath}")
    
    # Print summary
    print("\n" + "="*70)
    print("FIRE BENCHMARK SUMMARY")
    print("="*70)
    print(f"\nBest Rescue Rate:")
    print(f"  Configuration: {best_rescue[0][0]} agents, {best_rescue[0][1]} evacuees/room")
    print(f"  Rescue Rate: {best_rescue[1]['rescue_rate_mean']*100:.1f}%")
    print(f"  Agent Survival: {best_rescue[1]['agent_survival_mean']*100:.1f}%")
    
    print(f"\nBest Agent Survival:")
    print(f"  Configuration: {best_survival[0][0]} agents, {best_survival[0][1]} evacuees/room")
    print(f"  Agent Survival: {best_survival[1]['agent_survival_mean']*100:.1f}%")
    print(f"  Rescue Rate: {best_survival[1]['rescue_rate_mean']*100:.1f}%")
    
    print(f"\nBest Success Score:")
    print(f"  Configuration: {best_success[0][0]} agents, {best_success[0][1]} evacuees/room")
    print(f"  Success Score: {best_success[1]['success_score_mean']:.4f}")
    print(f"  Rescue Rate: {best_success[1]['rescue_rate_mean']*100:.1f}%")
    print(f"  Agent Survival: {best_success[1]['agent_survival_mean']*100:.1f}%")
    
    return filepath


def main():
    """Main function"""
    # Use the most recent fire benchmark file
    fire_files = [
        "benchmark_results/benchmark_fire_20251111_205538.json",
        "benchmark_results/benchmark_fire_20251111_131440.json",
    ]
    
    print("="*70)
    print("🔥 FIRE BENCHMARK GRAPH GENERATOR")
    print("="*70)
    
    for fire_file in fire_files:
        filepath = Path(fire_file)
        if filepath.exists():
            print(f"\nProcessing: {fire_file}")
            output = create_fire_graphs(fire_file)
            print(f"✓ Complete: {output}")
        else:
            print(f"⚠️  File not found: {fire_file}")


if __name__ == "__main__":
    main()


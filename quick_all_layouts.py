"""
Quick Benchmark - All Layouts
Generate graphs for Office, Hospital, and School
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


def run_quick_sim(layout_path: str, num_responders: int):
    """Run single simulation fast"""
    with open("params.json") as f:
        params = json.load(f)
    
    params['agents']['count'] = num_responders
    params['visualization']['enabled'] = False
    params['hazard']['enabled'] = False
    
    layout_data = LayoutLoader.load(layout_path)
    env = Environment(layout_data, params)
    sim = Simulator(env, params)
    
    start = time.time()
    while not sim.complete and sim.tick < 15000:
        sim.step(fire_enabled=False)
    
    results = sim.get_results()
    
    return {
        'responders': num_responders,
        'time': results['time'],
        'rescued': results['evacuees_rescued'],
        'total': results['total_evacuees'],
        'success_score': results['success_score'],
        'real_time': time.time() - start
    }


def main():
    print("="*70)
    print("🚀 QUICK LAYOUT COMPARISON")
    print("="*70)
    
    layouts = {
        'office': ('layouts/office_correct_dimensions.json', [1, 2, 3, 4, 5], 'Office'),
        'hospital': ('layouts/hospital_complex.json', [4, 6, 8, 10, 12], 'Hospital'),
        'school': ('layouts/school_building.json', [6, 8, 10, 12, 15], 'School')
    }
    
    all_results = {}
    
    for layout_name, (path, responder_counts, label) in layouts.items():
        print(f"\n📊 {label}...", end=" ", flush=True)
        results = []
        for num in responder_counts:
            r = run_quick_sim(path, num)
            results.append(r)
        all_results[layout_name] = results
        print(f"✓ {len(results)} runs")
    
    # Generate plots
    print("\n📊 Generating comparison graphs...")
    
    plt.style.use('seaborn-v0_8-darkgrid')
    fig = plt.figure(figsize=(18, 12), facecolor='#FAFAFA')
    
    colors = {
        'office': '#FF6B35',
        'hospital': '#1976D2',
        'school': '#43A047'
    }
    
    # 1. Sweep Time
    ax1 = plt.subplot(2, 3, 1)
    ax1.set_facecolor('#FFFFFF')
    
    for layout_name, results in all_results.items():
        resp = [r['responders'] for r in results]
        times = [r['time'] for r in results]
        ax1.plot(resp, times, 'o-', linewidth=3, markersize=10,
                color=colors[layout_name], label=layouts[layout_name][2],
                markeredgecolor='white', markeredgewidth=2)
    
    ax1.set_xlabel('Number of Responders', fontweight='bold', fontsize=11)
    ax1.set_ylabel('Sweep Time (seconds)', fontweight='bold', fontsize=11)
    ax1.set_title('⏱️  Sweep Time by Building Type', fontweight='bold', fontsize=13, pad=12)
    ax1.legend(frameon=True, fancybox=True, shadow=True)
    ax1.grid(True, alpha=0.2, linestyle='--')
    
    # 2. Success Score
    ax2 = plt.subplot(2, 3, 2)
    ax2.set_facecolor('#FFFFFF')
    
    for layout_name, results in all_results.items():
        resp = [r['responders'] for r in results]
        scores = [r['success_score'] for r in results]
        ax2.plot(resp, scores, 's-', linewidth=3, markersize=10,
                color=colors[layout_name], label=layouts[layout_name][2],
                markeredgecolor='white', markeredgewidth=2)
    
    ax2.set_xlabel('Number of Responders', fontweight='bold', fontsize=11)
    ax2.set_ylabel('Success Score', fontweight='bold', fontsize=11)
    ax2.set_title('📊 Success Score by Building Type', fontweight='bold', fontsize=13, pad=12)
    ax2.legend(frameon=True, fancybox=True, shadow=True)
    ax2.grid(True, alpha=0.2, linestyle='--')
    
    # 3. Occupants per Building
    ax3 = plt.subplot(2, 3, 3)
    ax3.set_facecolor('#FFFFFF')
    
    building_occupants = {
        'Office': all_results['office'][0]['total'],
        'Hospital': all_results['hospital'][0]['total'],
        'School': all_results['school'][0]['total']
    }
    
    gradient_colors = ['#FF6B35', '#1976D2', '#43A047']
    bars = ax3.bar(building_occupants.keys(), building_occupants.values(),
                  color=gradient_colors, edgecolor='#212121', linewidth=2.5, alpha=0.85)
    
    ax3.set_ylabel('Total Occupants', fontweight='bold', fontsize=11)
    ax3.set_title('👥 Building Occupancy', fontweight='bold', fontsize=13, pad=12)
    ax3.grid(True, alpha=0.2, axis='y', linestyle='--')
    
    for bar in bars:
        height = bar.get_height()
        ax3.text(bar.get_x() + bar.get_width()/2., height + 5,
                f'{int(height)}', ha='center', fontsize=11, fontweight='bold')
    
    # 4. Optimal Responder Count
    ax4 = plt.subplot(2, 3, 4)
    ax4.set_facecolor('#FFFFFF')
    
    optimal = {
        'Office': min(all_results['office'], key=lambda x: x['time'])['responders'],
        'Hospital': min(all_results['hospital'], key=lambda x: x['time'])['responders'],
        'School': min(all_results['school'], key=lambda x: x['time'])['responders']
    }
    
    bars = ax4.bar(optimal.keys(), optimal.values(),
                  color=gradient_colors, edgecolor='#212121', linewidth=2.5, alpha=0.85)
    
    ax4.set_ylabel('Optimal Responders', fontweight='bold', fontsize=11)
    ax4.set_title('🚒 Optimal Team Size (Fastest Sweep)', fontweight='bold', fontsize=13, pad=12)
    ax4.grid(True, alpha=0.2, axis='y', linestyle='--')
    
    for bar in bars:
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height + 0.2,
                f'{int(height)}', ha='center', fontsize=11, fontweight='bold')
    
    # 5. Time per Occupant
    ax5 = plt.subplot(2, 3, 5)
    ax5.set_facecolor('#FFFFFF')
    
    time_per_occ = {}
    for layout_name, (path, counts, label) in layouts.items():
        min_time_result = min(all_results[layout_name], key=lambda x: x['time'])
        time_per_occ[label] = min_time_result['time'] / min_time_result['total']
    
    bars = ax5.bar(time_per_occ.keys(), time_per_occ.values(),
                  color=gradient_colors, edgecolor='#212121', linewidth=2.5, alpha=0.85)
    
    ax5.set_ylabel('Seconds per Occupant', fontweight='bold', fontsize=11)
    ax5.set_title('⚡ Efficiency: Time per Occupant', fontweight='bold', fontsize=13, pad=12)
    ax5.grid(True, alpha=0.2, axis='y', linestyle='--')
    
    for bar in bars:
        height = bar.get_height()
        ax5.text(bar.get_x() + bar.get_width()/2., height + 1,
                f'{height:.1f}s', ha='center', fontsize=10, fontweight='bold')
    
    # 6. Summary Table
    ax6 = plt.subplot(2, 3, 6)
    ax6.set_facecolor('#FFFFFF')
    ax6.axis('off')
    
    summary = "BUILDING COMPARISON\n"
    summary += "═" * 35 + "\n\n"
    
    for layout_name, (path, counts, label) in layouts.items():
        best = min(all_results[layout_name], key=lambda x: x['time'])
        summary += f"{label}:\n"
        summary += f"  Occupants: {best['total']}\n"
        summary += f"  Optimal: {best['responders']} responders\n"
        summary += f"  Time: {best['time']/60:.1f} min\n"
        summary += f"  Score: {best['success_score']:.4f}\n\n"
    
    ax6.text(0.5, 0.5, summary, transform=ax6.transAxes,
            fontsize=11, verticalalignment='center', horizontalalignment='center',
            bbox=dict(boxstyle='round,pad=1.5', facecolor='#FFF9C4',
                     edgecolor='#F57F17', linewidth=3, alpha=0.95),
            fontfamily='monospace', fontweight='600')
    
    fig.suptitle('MULTI-BUILDING PERFORMANCE COMPARISON',
                fontsize=18, fontweight='bold', y=0.98,
                bbox=dict(boxstyle='round,pad=0.8', facecolor='#FF6B35',
                         edgecolor='none', alpha=1.0),
                color='white')
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    # Save
    output_path = Path("benchmark_results")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = output_path / f"multi_building_comparison_{timestamp}.png"
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()
    
    # Print summary
    print("\n" + "="*70)
    print("MULTI-BUILDING COMPARISON RESULTS")
    print("="*70)
    
    for layout_name, (path, counts, label) in layouts.items():
        print(f"\n{label}:")
        print(f"  Total Occupants: {all_results[layout_name][0]['total']}")
        best = min(all_results[layout_name], key=lambda x: x['time'])
        print(f"  Optimal: {best['responders']} responders")
        print(f"  Min Time: {best['time']:.0f}s ({best['time']/60:.1f} min)")
        print(f"  Success Score: {best['success_score']:.4f}")
        print(f"  Time/Occupant: {best['time']/best['total']:.1f}s")
    
    print(f"\n✓ Graph saved: {filepath}")
    
    # Save data
    data_file = output_path / f"multi_building_data_{timestamp}.json"
    with open(data_file, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    print(f"✓ Data saved: {data_file}")


if __name__ == "__main__":
    main()


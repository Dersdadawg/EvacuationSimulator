"""ULTRA FAST - 3 layouts, 3 tests each, 9 total runs"""
import json
import time
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
from sim.engine.simulator import Simulator
from sim.env.environment import Environment
from sim.io.layout_loader import LayoutLoader

def run_fast(layout, responders):
    with open("params.json") as f:
        params = json.load(f)
    params['agents']['count'] = responders
    params['visualization']['enabled'] = False
    params['hazard']['enabled'] = False
    
    env = Environment(LayoutLoader.load(layout), params)
    sim = Simulator(env, params)
    
    while not sim.complete and sim.tick < 5000:  # SHORTER CAP
        sim.step(fire_enabled=False)
    
    r = sim.get_results()
    return {
        'resp': responders,
        'time': r['time'],
        'rescued': r['evacuees_rescued'],
        'total': r['total_evacuees'],
        'score': r['success_score']
    }

# RUN FAST
print("RUNNING ULTRA FAST...")
layouts = {
    'Office': ('layouts/office_correct_dimensions.json', [2, 3, 5]),
    'Hospital': ('layouts/hospital_complex.json', [6, 8, 10]),
    'School': ('layouts/school_building.json', [8, 10, 12])
}

results = {}
for name, (path, counts) in layouts.items():
    print(f"{name}...", end=" ", flush=True)
    results[name] = [run_fast(path, n) for n in counts]
    print(f"✓")

# PLOT FAST
plt.style.use('seaborn-v0_8-darkgrid')
fig = plt.figure(figsize=(16, 10), facecolor='#FAFAFA')

colors = {'Office': '#FF6B35', 'Hospital': '#1976D2', 'School': '#43A047'}

# Time comparison
ax1 = plt.subplot(2, 2, 1)
ax1.set_facecolor('#FFFFFF')
for name, data in results.items():
    resp = [d['resp'] for d in data]
    times = [d['time'] for d in data]
    ax1.plot(resp, times, 'o-', linewidth=3, markersize=10,
            color=colors[name], label=name, markeredgecolor='white', markeredgewidth=2)
ax1.set_xlabel('Responders', fontweight='bold')
ax1.set_ylabel('Time (s)', fontweight='bold')
ax1.set_title('⏱️  Sweep Time', fontweight='bold', fontsize=14)
ax1.legend()
ax1.grid(True, alpha=0.2, linestyle='--')

# Success Score
ax2 = plt.subplot(2, 2, 2)
ax2.set_facecolor('#FFFFFF')
for name, data in results.items():
    resp = [d['resp'] for d in data]
    scores = [d['score'] for d in data]
    ax2.plot(resp, scores, 's-', linewidth=3, markersize=10,
            color=colors[name], label=name, markeredgecolor='white', markeredgewidth=2)
ax2.set_xlabel('Responders', fontweight='bold')
ax2.set_ylabel('Success Score', fontweight='bold')
ax2.set_title('📊 Success Score', fontweight='bold', fontsize=14)
ax2.legend()
ax2.grid(True, alpha=0.2, linestyle='--')

# Occupants
ax3 = plt.subplot(2, 2, 3)
ax3.set_facecolor('#FFFFFF')
occupants = {name: data[0]['total'] for name, data in results.items()}
bars = ax3.bar(occupants.keys(), occupants.values(),
              color=[colors[k] for k in occupants.keys()],
              edgecolor='black', linewidth=2, alpha=0.85)
ax3.set_ylabel('Total Occupants', fontweight='bold')
ax3.set_title('👥 Building Occupancy', fontweight='bold', fontsize=14)
ax3.grid(True, alpha=0.2, axis='y')
for bar in bars:
    h = bar.get_height()
    ax3.text(bar.get_x() + bar.get_width()/2., h + 5, f'{int(h)}',
            ha='center', fontsize=11, fontweight='bold')

# Summary
ax4 = plt.subplot(2, 2, 4)
ax4.set_facecolor('#FFFFFF')
ax4.axis('off')

summary = "QUICK COMPARISON\n" + "═"*30 + "\n\n"
for name, data in results.items():
    best = min(data, key=lambda x: x['time'])
    summary += f"{name}:\n"
    summary += f"  Occupants: {best['total']}\n"
    summary += f"  Best: {best['resp']} resp\n"
    summary += f"  Time: {best['time']/60:.1f}min\n\n"

ax4.text(0.5, 0.5, summary, transform=ax4.transAxes, fontsize=11,
        va='center', ha='center',
        bbox=dict(boxstyle='round,pad=1.5', facecolor='#FFF9C4',
                 edgecolor='#F57F17', linewidth=3, alpha=0.95),
        fontfamily='monospace', fontweight='600')

fig.suptitle('BUILDING TYPE COMPARISON', fontsize=18, fontweight='bold',
            y=0.98, bbox=dict(boxstyle='round,pad=0.8', facecolor='#FF6B35',
            edgecolor='none', alpha=1.0), color='white')

plt.tight_layout(rect=[0, 0, 1, 0.96])

# SAVE
output_path = Path("benchmark_results")
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
filepath = output_path / f"FAST_comparison_{timestamp}.png"
plt.savefig(filepath, dpi=150, bbox_inches='tight')
plt.close()

print(f"\n✓ DONE: {filepath}")

# Print results
print("\nRESULTS:")
for name, data in results.items():
    print(f"{name}: {data[0]['total']} occupants, best={min(data, key=lambda x: x['time'])['resp']} resp")


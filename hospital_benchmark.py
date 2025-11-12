"""
Hospital Benchmark - Fast Analysis
Run hospital simulations without visualization and generate graphs
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


def run_hospital_sim(num_responders: int, with_fire: bool = False):
    """Run single hospital simulation - NO VISUALIZATION"""
    # Load params
    with open("params.json") as f:
        params = json.load(f)
    
    params['agents']['count'] = num_responders
    params['visualization']['enabled'] = False
    params['hazard']['enabled'] = with_fire
    
    # Load hospital
    layout_data = LayoutLoader.load("layouts/hospital_complex.json")
    env = Environment(layout_data, params)
    sim = Simulator(env, params)
    
    # Run fast
    start = time.time()
    while not sim.complete and sim.tick < 15000:
        sim.step(fire_enabled=with_fire)
    
    elapsed = time.time() - start
    results = sim.get_results()
    
    # Responder stats
    num_alive = sum(1 for a in sim.agent_manager.agents if not a.is_dead)
    num_deaths = num_responders - num_alive
    
    return {
        'responders': num_responders,
        'time': results['time'],
        'real_time': elapsed,
        'rescued': results['evacuees_rescued'],
        'total': results['total_evacuees'],
        'rescue_rate': results['evacuees_rescued'] / results['total_evacuees'] * 100,
        'success_score': results['success_score'],
        'responders_alive': num_alive,
        'responder_deaths': num_deaths,
        'fire': with_fire
    }


def plot_results(no_fire_results, fire_results):
    """Generate comparison plots"""
    plt.style.use('seaborn-v0_8-darkgrid')
    fig = plt.figure(figsize=(18, 11), facecolor='#FAFAFA')
    
    # Extract data
    nf_resp = [r['responders'] for r in no_fire_results]
    nf_time = [r['time'] for r in no_fire_results]
    nf_rescued = [r['rescued'] for r in no_fire_results]
    nf_score = [r['success_score'] for r in no_fire_results]
    
    f_resp = [r['responders'] for r in fire_results]
    f_time = [r['time'] for r in fire_results]
    f_rescued = [r['rescued'] for r in fire_results]
    f_score = [r['success_score'] for r in fire_results]
    f_deaths = [r['responder_deaths'] for r in fire_results]
    
    # 1. Sweep Time Comparison
    ax1 = plt.subplot(2, 3, 1)
    ax1.set_facecolor('#FFFFFF')
    ax1.plot(nf_resp, nf_time, 'o-', linewidth=3, markersize=10, 
            color='#1976D2', label='No Fire', markeredgecolor='white', markeredgewidth=2)
    ax1.plot(f_resp, f_time, 's-', linewidth=3, markersize=10,
            color='#E53935', label='With Fire', markeredgecolor='white', markeredgewidth=2)
    ax1.set_xlabel('Number of Responders', fontweight='bold', fontsize=11)
    ax1.set_ylabel('Sweep Time (seconds)', fontweight='bold', fontsize=11)
    ax1.set_title('⏱️  Sweep Time: Fire vs No Fire', fontweight='bold', fontsize=13, pad=12)
    ax1.legend(frameon=True, fancybox=True, shadow=True)
    ax1.grid(True, alpha=0.2, linestyle='--')
    
    # 2. Occupants Rescued
    ax2 = plt.subplot(2, 3, 2)
    ax2.set_facecolor('#FFFFFF')
    ax2.plot(nf_resp, nf_rescued, 'o-', linewidth=3, markersize=10,
            color='#1976D2', label='No Fire', markeredgecolor='white', markeredgewidth=2)
    ax2.plot(f_resp, f_rescued, 's-', linewidth=3, markersize=10,
            color='#E53935', label='With Fire', markeredgecolor='white', markeredgewidth=2)
    ax2.set_xlabel('Number of Responders', fontweight='bold', fontsize=11)
    ax2.set_ylabel('Occupants Rescued', fontweight='bold', fontsize=11)
    ax2.set_title('🚑 Occupants Rescued', fontweight='bold', fontsize=13, pad=12)
    ax2.legend(frameon=True, fancybox=True, shadow=True)
    ax2.grid(True, alpha=0.2, linestyle='--')
    ax2.set_ylim([0, 105])
    
    # 3. Success Score
    ax3 = plt.subplot(2, 3, 3)
    ax3.set_facecolor('#FFFFFF')
    ax3.plot(nf_resp, nf_score, 'o-', linewidth=3, markersize=10,
            color='#1976D2', label='No Fire', markeredgecolor='white', markeredgewidth=2)
    ax3.plot(f_resp, f_score, 's-', linewidth=3, markersize=10,
            color='#E53935', label='With Fire', markeredgecolor='white', markeredgewidth=2)
    ax3.set_xlabel('Number of Responders', fontweight='bold', fontsize=11)
    ax3.set_ylabel('Success Score', fontweight='bold', fontsize=11)
    ax3.set_title('📊 Success Score Comparison', fontweight='bold', fontsize=13, pad=12)
    ax3.legend(frameon=True, fancybox=True, shadow=True)
    ax3.grid(True, alpha=0.2, linestyle='--')
    
    # 4. Rescue Rate Comparison
    ax4 = plt.subplot(2, 3, 4)
    ax4.set_facecolor('#FFFFFF')
    
    nf_rate = [r['rescue_rate'] for r in no_fire_results]
    f_rate = [r['rescue_rate'] for r in fire_results]
    
    x = np.arange(len(nf_resp))
    width = 0.35
    
    bars1 = ax4.bar(x - width/2, nf_rate, width, label='No Fire',
                   color='#81C784', edgecolor='#388E3C', linewidth=2, alpha=0.85)
    bars2 = ax4.bar(x + width/2, f_rate, width, label='With Fire',
                   color='#FF8A65', edgecolor='#D84315', linewidth=2, alpha=0.85)
    
    ax4.set_xlabel('Number of Responders', fontweight='bold', fontsize=11)
    ax4.set_ylabel('Rescue Rate (%)', fontweight='bold', fontsize=11)
    ax4.set_title('📈 Rescue Rate Comparison', fontweight='bold', fontsize=13, pad=12)
    ax4.set_xticks(x)
    ax4.set_xticklabels(nf_resp)
    ax4.legend(frameon=True, fancybox=True, shadow=True)
    ax4.grid(True, alpha=0.2, axis='y', linestyle='--')
    ax4.set_ylim([0, 110])
    
    # Add percentage labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + 2,
                    f'{height:.0f}%', ha='center', fontsize=9, fontweight='bold')
    
    # 5. Responder Deaths (Fire Only)
    ax5 = plt.subplot(2, 3, 5)
    ax5.set_facecolor('#FFFFFF')
    
    # Orange gradient for death bars
    gradient_colors = []
    for i, val in enumerate(f_deaths):
        intensity = val / max(f_deaths) if max(f_deaths) > 0 else 0
        r = 1.0
        g = 0.42 - (0.2 * intensity)
        b = 0.21 - (0.15 * intensity)
        gradient_colors.append((r, g, b))
    
    bars = ax5.bar(f_resp, f_deaths, color=gradient_colors,
                  edgecolor='#BF360C', linewidth=2.5, alpha=0.85)
    
    ax5.set_xlabel('Number of Responders', fontweight='bold', fontsize=11)
    ax5.set_ylabel('Responder Deaths', fontweight='bold', fontsize=11)
    ax5.set_title('💀 Responder Casualties (With Fire)', fontweight='bold', fontsize=13, pad=12)
    ax5.grid(True, alpha=0.2, axis='y', linestyle='--')
    
    # Add labels
    for bar in bars:
        height = bar.get_height()
        ax5.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                f'{int(height)}', ha='center', fontsize=10, fontweight='bold')
    
    # 6. Summary Box
    ax6 = plt.subplot(2, 3, 6)
    ax6.set_facecolor('#FFFFFF')
    ax6.axis('off')
    
    avg_nf_rescued = np.mean([r['rescued'] for r in no_fire_results])
    avg_f_rescued = np.mean([r['rescued'] for r in fire_results])
    avg_f_deaths = np.mean(f_deaths)
    
    summary = (
        f"🏥 HOSPITAL SUMMARY\n"
        f"{'═'*35}\n\n"
        f"Building: 71.8m × 52.1m\n"
        f"Occupants: 100 total\n"
        f"Rooms: 8 patient areas\n\n"
        f"NO FIRE RESULTS:\n"
        f"  Avg Rescued: {avg_nf_rescued:.0f}/100\n"
        f"  Best Time: {min(nf_time):.0f}s\n\n"
        f"WITH FIRE RESULTS:\n"
        f"  Avg Rescued: {avg_f_rescued:.0f}/100\n"
        f"  Avg Deaths: {avg_f_deaths:.1f}\n"
        f"  Best Score: {max(f_score):.4f}\n\n"
        f"Area-based priority:\n"
        f"ICU (592 sq m) = 2.0x boost\n"
        f"Small rooms = 0.75x"
    )
    
    ax6.text(0.5, 0.5, summary, transform=ax6.transAxes,
            fontsize=11, verticalalignment='center', horizontalalignment='center',
            bbox=dict(boxstyle='round,pad=1.5', facecolor='#E3F2FD',
                     edgecolor='#1976D2', linewidth=3, alpha=0.95),
            fontfamily='monospace', fontweight='600')
    
    # Title
    fig.suptitle('🏥 HOSPITAL COMPLEX PERFORMANCE ANALYSIS',
                fontsize=18, fontweight='bold', y=0.98,
                bbox=dict(boxstyle='round,pad=0.8', facecolor='#1976D2',
                         edgecolor='none', alpha=1.0),
                color='white')
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    # Save
    output_path = Path("benchmark_results")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = output_path / f"hospital_analysis_{timestamp}.png"
    plt.savefig(filepath, dpi=150, bbox_inches='tight')
    plt.close()
    
    return filepath


def main():
    print("\n" + "="*70)
    print("🏥 HOSPITAL COMPLEX - FAST BENCHMARK")
    print("="*70)
    print("Building: 8 rooms, 100 occupants, variable room sizes")
    print()
    
    # Run without fire
    print("📊 Running NO FIRE tests...")
    no_fire_results = []
    for num in [4, 6, 8, 10]:
        print(f"  {num} responders...", end=" ", flush=True)
        result = run_hospital_sim(num, with_fire=False)
        no_fire_results.append(result)
        print(f"✓ {result['time']:.0f}s, {result['rescued']}/{result['total']} rescued")
    
    print()
    
    # Run with fire
    print("🔥 Running WITH FIRE tests...")
    fire_results = []
    for num in [4, 6, 8]:
        print(f"  {num} responders...", end=" ", flush=True)
        result = run_hospital_sim(num, with_fire=True)
        fire_results.append(result)
        print(f"✓ {result['time']:.0f}s, {result['rescued']}/{result['total']} rescued, {result['responder_deaths']} deaths")
    
    print()
    print("="*70)
    
    # Summary table
    print("\n📋 NO FIRE RESULTS:")
    print("-"*70)
    print(f"{'Resp':<8}{'Time':<15}{'Rescued':<15}{'Success Score':<15}")
    print("-"*70)
    for r in no_fire_results:
        print(f"{r['responders']:<8}{r['time']:.0f}s ({r['time']/60:.1f}m){'':<3}"
              f"{r['rescued']}/{r['total']:<11}{r['success_score']:<15.4f}")
    
    print("\n🔥 WITH FIRE RESULTS:")
    print("-"*70)
    print(f"{'Resp':<8}{'Time':<15}{'Rescued':<15}{'Deaths':<10}{'Success':<15}")
    print("-"*70)
    for r in fire_results:
        print(f"{r['responders']:<8}{r['time']:.0f}s ({r['time']/60:.1f}m){'':<3}"
              f"{r['rescued']}/{r['total']:<11}{r['responder_deaths']}/{r['responders']:<8}"
              f"{r['success_score']:<15.4f}")
    
    # Generate plots
    print("\n📊 Generating graphs...")
    plot_file = plot_results(no_fire_results, fire_results)
    
    # Save data
    output_path = Path("benchmark_results")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    data_file = output_path / f"hospital_data_{timestamp}.json"
    
    with open(data_file, 'w') as f:
        json.dump({
            'no_fire': no_fire_results,
            'with_fire': fire_results
        }, f, indent=2)
    
    print(f"\n✓ Results saved:")
    print(f"  Data:  {data_file}")
    print(f"  Plots: {plot_file}")
    
    # Key findings
    print("\n💡 KEY FINDINGS:")
    best_nf = min(no_fire_results, key=lambda x: x['time'])
    best_f = max(fire_results, key=lambda x: x['success_score'])
    
    print(f"  No Fire - Fastest: {best_nf['responders']} responders, {best_nf['time']/60:.1f} min")
    print(f"  With Fire - Best: {best_f['responders']} responders, {best_f['rescued']}/100 rescued, {best_f['responder_deaths']} deaths")
    print(f"  Fire Impact: {(1 - best_f['rescued']/best_nf['rescued'])*100:.1f}% fewer rescues")


if __name__ == "__main__":
    main()


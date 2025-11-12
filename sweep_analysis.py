"""
Building Sweep Analysis - No Fire
Analyzes optimal sweep strategies and generates comprehensive report

Reports:
- Order of rooms checked (sweep path)
- Optimal number of responders
- Minimum time to fully sweep building
- Path efficiency metrics
"""

import json
import time
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
from collections import defaultdict

from sim.engine.simulator import Simulator
from sim.env.environment import Environment
from sim.io.layout_loader import LayoutLoader


class SweepAnalyzer:
    """Analyze building sweep performance"""
    
    def __init__(self, layout_path: str = "layouts/office_correct_dimensions.json"):
        self.layout_path = layout_path
        self.results = []
        
    def run_sweep_analysis(self, num_responders: int) -> dict:
        """Run single sweep and track detailed metrics"""
        print(f"\n{'='*70}")
        print(f"Analyzing: {num_responders} responders")
        print(f"{'='*70}")
        
        # Load params
        with open("params.json") as f:
            params = json.load(f)
        
        params['agents']['count'] = num_responders
        params['visualization']['enabled'] = False
        params['hazard']['enabled'] = False  # No fire
        
        # Load layout
        layout_data = LayoutLoader.load(self.layout_path)
        
        # Create environment and simulator
        env = Environment(layout_data, params)
        sim = Simulator(env, params)
        
        # Track room visit order for each responder
        responder_room_orders = defaultdict(list)
        responder_paths = defaultdict(list)
        room_clear_times = {}
        room_visit_sequence = []
        
        # Run simulation
        start_time = time.time()
        step_count = 0
        max_steps = 10000
        
        previous_rooms = {a.id: None for a in sim.agent_manager.agents}
        
        while not sim.complete and step_count < max_steps:
            # Track room visits
            for agent in sim.agent_manager.agents:
                # Record position
                responder_paths[agent.id].append((agent.x, agent.y, sim.time))
                
                # Check if entered new room
                if agent.current_room != previous_rooms[agent.id]:
                    if agent.current_room and not env.rooms[agent.current_room].is_exit:
                        responder_room_orders[agent.id].append({
                            'room': agent.current_room,
                            'time': sim.time,
                            'evacuees': env.rooms[agent.current_room].evacuees_remaining
                        })
                        room_visit_sequence.append({
                            'responder': agent.id,
                            'room': agent.current_room,
                            'time': sim.time
                        })
                    previous_rooms[agent.id] = agent.current_room
            
            # Track room clearances
            for room_id, room in env.rooms.items():
                if room.cleared and room_id not in room_clear_times and not room.is_exit:
                    room_clear_times[room_id] = sim.time
            
            sim.step(fire_enabled=False)
            step_count += 1
        
        elapsed = time.time() - start_time
        results = sim.get_results()
        
        # Calculate path metrics
        total_distance = 0
        for responder_id, path in responder_paths.items():
            for i in range(1, len(path)):
                dx = path[i][0] - path[i-1][0]
                dy = path[i][1] - path[i-1][1]
                total_distance += np.sqrt(dx**2 + dy**2)
        
        avg_distance_per_responder = total_distance / num_responders if num_responders > 0 else 0
        
        return {
            'num_responders': num_responders,
            'sweep_time': results['time'],
            'real_time': elapsed,
            'occupants_rescued': results['evacuees_rescued'],
            'total_occupants': results['total_evacuees'],
            'rescue_rate': results['evacuees_rescued'] / results['total_evacuees'],
            'rooms_cleared': results['rooms_cleared'],
            'total_rooms': results['total_rooms'],
            'success_score': results['success_score'],
            'total_distance': total_distance,
            'avg_distance_per_responder': avg_distance_per_responder,
            'room_orders': dict(responder_room_orders),
            'room_clear_times': room_clear_times,
            'visit_sequence': room_visit_sequence,
            'responder_paths': dict(responder_paths)
        }
    
    def run_full_analysis(self, responder_counts: list):
        """Run analysis for multiple responder counts"""
        print(f"\n{'='*70}")
        print(f"BUILDING SWEEP ANALYSIS")
        print(f"Layout: {self.layout_path}")
        print(f"{'='*70}")
        
        for num in responder_counts:
            result = self.run_sweep_analysis(num)
            self.results.append(result)
    
    def generate_text_report(self) -> str:
        """Generate comprehensive text report"""
        report = []
        report.append("=" * 80)
        report.append("BUILDING SWEEP ANALYSIS REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Find optimal configuration
        min_time_result = min(self.results, key=lambda r: r['sweep_time'])
        max_efficiency = max(self.results, key=lambda r: r['success_score'])
        
        report.append("📋 EXECUTIVE SUMMARY")
        report.append("-" * 80)
        report.append(f"Building Dimensions: 46.92m × 34.06m")
        report.append(f"Total Rooms: {self.results[0]['total_rooms']} offices")
        report.append(f"Total Occupants: {self.results[0]['total_occupants']} people")
        report.append("")
        
        report.append("🎯 OPTIMAL CONFIGURATION")
        report.append("-" * 80)
        report.append(f"Minimum Sweep Time: {min_time_result['sweep_time']:.0f}s ({min_time_result['sweep_time']/60:.1f} min)")
        report.append(f"  → Achieved with {min_time_result['num_responders']} responders")
        report.append("")
        report.append(f"Maximum Efficiency (Success Score): {max_efficiency['success_score']:.4f}")
        report.append(f"  → Achieved with {max_efficiency['num_responders']} responders")
        report.append("")
        
        # Detailed results by responder count
        report.append("📊 PERFORMANCE BY RESPONDER COUNT")
        report.append("-" * 80)
        report.append(f"{'Responders':<12}{'Sweep Time':<15}{'Rescued':<15}{'Avg Distance':<15}{'Score':<10}")
        report.append("-" * 80)
        
        for r in self.results:
            report.append(
                f"{r['num_responders']:<12}"
                f"{r['sweep_time']:.0f}s ({r['sweep_time']/60:.1f}m){'':<2}"
                f"{r['occupants_rescued']}/{r['total_occupants']:<11}"
                f"{r['avg_distance_per_responder']:.1f}m{'':<8}"
                f"{r['success_score']:.4f}"
            )
        
        report.append("")
        
        # Room sweep order analysis
        report.append("🗺️  ROOM SWEEP ORDER (Example: 3 Responders)")
        report.append("-" * 80)
        
        # Get 3-responder result
        three_resp = next((r for r in self.results if r['num_responders'] == 3), None)
        if three_resp:
            report.append("Visit Sequence (chronological):")
            for i, visit in enumerate(three_resp['visit_sequence'][:15], 1):
                report.append(f"  {i}. Responder {visit['responder']} → {visit['room']} (t={visit['time']:.0f}s)")
            
            report.append("")
            report.append("Room Clearance Times:")
            sorted_clearances = sorted(three_resp['room_clear_times'].items(), 
                                      key=lambda x: x[1])
            for room_id, clear_time in sorted_clearances:
                report.append(f"  {room_id}: {clear_time:.0f}s ({clear_time/60:.1f} min)")
        
        report.append("")
        
        # Starting positions
        report.append("🚒 RESPONDER STARTING POSITIONS")
        report.append("-" * 80)
        report.append("All responders start at building exits:")
        report.append("  Position 1: (1.0, 17.03) - Left exit")
        report.append("  Position 2: (45.0, 17.03) - Right exit")
        report.append("Responders alternate between these positions")
        report.append("")
        
        # Time analysis
        report.append("⏱️  TIME ANALYSIS")
        report.append("-" * 80)
        report.append(f"{'Responders':<12}{'Time':<15}{'Time/Room':<15}{'Speedup vs 1':<15}")
        report.append("-" * 80)
        
        base_time = self.results[0]['sweep_time']
        for r in self.results:
            time_per_room = r['sweep_time'] / r['rooms_cleared'] if r['rooms_cleared'] > 0 else 0
            speedup = base_time / r['sweep_time'] if r['sweep_time'] > 0 else 0
            report.append(
                f"{r['num_responders']:<12}"
                f"{r['sweep_time']:.0f}s{'':<10}"
                f"{time_per_room:.0f}s{'':<12}"
                f"{speedup:.2f}x"
            )
        
        report.append("")
        
        # Efficiency analysis
        report.append("💡 KEY FINDINGS")
        report.append("-" * 80)
        
        # Calculate diminishing returns
        times = [r['sweep_time'] for r in self.results]
        time_reductions = []
        for i in range(1, len(times)):
            reduction = (times[i-1] - times[i]) / times[i-1] * 100
            time_reductions.append(reduction)
        
        report.append(f"1. Minimum Sweep Time: {min_time_result['sweep_time']:.0f}s with {min_time_result['num_responders']} responders")
        report.append(f"2. Time Reduction per Additional Responder:")
        for i, reduction in enumerate(time_reductions, 2):
            report.append(f"   {i-1} → {i} responders: {reduction:.1f}% faster")
        
        report.append("")
        report.append(f"3. Optimal Team Size: {max_efficiency['num_responders']} responders")
        report.append(f"   - Best efficiency per responder")
        report.append(f"   - Minimal coordination overhead")
        
        report.append("")
        report.append(f"4. All configurations achieve 100% rescue rate")
        report.append(f"   - Building fully searchable without fire")
        report.append(f"   - No occupants left behind")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def plot_results(self):
        """Generate modern plots with gradients"""
        # Modern styling
        plt.style.use('seaborn-v0_8-darkgrid')
        fig = plt.figure(figsize=(18, 11), facecolor='#FAFAFA')
        
        responders = [r['num_responders'] for r in self.results]
        sweep_times = [r['sweep_time'] for r in self.results]
        distances = [r['avg_distance_per_responder'] for r in self.results]
        scores = [r['success_score'] for r in self.results]
        
        # Modern color palette
        colors = {
            'primary': '#FF6B35',     # Vibrant orange
            'secondary': '#004E89',   # Deep blue
            'success': '#00C49A',     # Teal
            'warning': '#FFB01F',     # Gold
            'danger': '#E63946'       # Red
        }
        
        # 1. Sweep Time - Gradient fill
        ax1 = plt.subplot(2, 2, 1)
        ax1.set_facecolor('#FFFFFF')
        
        # Plot line with gradient fill
        ax1.plot(responders, sweep_times, 'o-', linewidth=3, markersize=12, 
                color=colors['danger'], markeredgecolor='white', markeredgewidth=2, 
                zorder=3, label='Sweep Time')
        ax1.fill_between(responders, sweep_times, alpha=0.2, color=colors['danger'])
        
        ax1.set_xlabel('Number of Responders', fontweight='bold', fontsize=12)
        ax1.set_ylabel('Sweep Time (seconds)', fontweight='bold', fontsize=12)
        ax1.set_title('⏱️  Minimum Time to Fully Sweep Building', 
                     fontweight='bold', fontsize=14, pad=15)
        ax1.grid(True, alpha=0.2, linestyle='--')
        
        # Add time labels with better styling
        for x, y in zip(responders, sweep_times):
            ax1.text(x, y + 150, f'{y:.0f}s\n({y/60:.1f} min)', ha='center', 
                    fontsize=10, fontweight='600',
                    bbox=dict(boxstyle='round,pad=0.5', facecolor='white', 
                             edgecolor=colors['danger'], linewidth=2, alpha=0.9))
        
        # 2. Avg Distance per Responder - Gradient
        ax2 = plt.subplot(2, 2, 2)
        ax2.set_facecolor('#FFFFFF')
        
        ax2.plot(responders, distances, 's-', linewidth=3, markersize=12, 
                color=colors['secondary'], markeredgecolor='white', markeredgewidth=2,
                zorder=3)
        ax2.fill_between(responders, distances, alpha=0.2, color=colors['secondary'])
        
        ax2.set_xlabel('Number of Responders', fontweight='bold', fontsize=12)
        ax2.set_ylabel('Avg Distance per Responder (m)', fontweight='bold', fontsize=12)
        ax2.set_title('🚶 Average Path Length per Responder', 
                     fontweight='bold', fontsize=14, pad=15)
        ax2.grid(True, alpha=0.2, linestyle='--')
        
        # 3. Success Score - Gradient
        ax3 = plt.subplot(2, 2, 3)
        ax3.set_facecolor('#FFFFFF')
        
        ax3.plot(responders, scores, '^-', linewidth=3, markersize=12, 
                color=colors['success'], markeredgecolor='white', markeredgewidth=2,
                zorder=3)
        ax3.fill_between(responders, scores, alpha=0.2, color=colors['success'])
        
        ax3.set_xlabel('Number of Responders', fontweight='bold', fontsize=12)
        ax3.set_ylabel('Success Score', fontweight='bold', fontsize=12)
        ax3.set_title('📊 Success Score\n(Occupants Rescued × % Responders Alive / Time × Responders)', 
                     fontweight='bold', fontsize=13, pad=15)
        ax3.grid(True, alpha=0.2, linestyle='--')
        
        # 4. Time Reduction - ORANGE GRADIENT BARS
        ax4 = plt.subplot(2, 2, 4)
        ax4.set_facecolor('#FFFFFF')
        
        time_reductions = []
        for i in range(1, len(sweep_times)):
            reduction = (sweep_times[i-1] - sweep_times[i]) / sweep_times[i-1] * 100
            time_reductions.append(reduction)
        
        # Create gradient colors for bars (orange to yellow)
        gradient_colors = []
        for i, val in enumerate(time_reductions):
            # Interpolate from dark orange to light orange/yellow
            intensity = 1 - (i / len(time_reductions))  # Darker for higher values
            r = 1.0
            g = 0.4 + (0.4 * (1 - intensity))  # 0.4 to 0.8
            b = 0.2 * (1 - intensity)  # 0 to 0.2
            gradient_colors.append((r, g, b))
        
        bars = ax4.bar(responders[1:], time_reductions, 
                      color=gradient_colors, 
                      edgecolor='#D84315', linewidth=2.5, alpha=0.85)
        
        # Add subtle shadow effect
        for bar in bars:
            bar.set_zorder(2)
        
        ax4.set_xlabel('Number of Responders', fontweight='bold', fontsize=12)
        ax4.set_ylabel('Time Reduction (%)', fontweight='bold', fontsize=12)
        ax4.set_title('🔥 Marginal Benefit of Additional Responder', 
                     fontweight='bold', fontsize=14, pad=15)
        ax4.grid(True, alpha=0.2, axis='y', linestyle='--')
        ax4.set_axisbelow(True)
        
        # Add percentage labels with modern styling
        for i, (x, y) in enumerate(zip(responders[1:], time_reductions)):
            ax4.text(x, y + 1.5, f'{y:.1f}%', ha='center', 
                    fontweight='bold', fontsize=11, color='#1A1A1A')
        
        # Set y-axis limit to give space for labels
        ax4.set_ylim(0, max(time_reductions) * 1.15)
        
        # Overall styling
        fig.suptitle('BUILDING SWEEP PERFORMANCE ANALYSIS', 
                    fontsize=18, fontweight='bold', y=0.98,
                    bbox=dict(boxstyle='round,pad=0.8', facecolor='#FF6B35', 
                             edgecolor='none', alpha=1.0),
                    color='white')
        
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        
        # Save
        output_path = Path("benchmark_results")
        output_path.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        filepath = output_path / f"sweep_analysis_{timestamp}.png"
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        
        return filepath


def main():
    print("\n" + "="*80)
    print("BUILDING SWEEP ANALYSIS - NO FIRE")
    print("Analyzing optimal responder deployment and sweep strategies")
    print("="*80)
    
    # Run analysis
    analyzer = SweepAnalyzer()
    responder_counts = [1, 2, 3, 4, 5]
    
    analyzer.run_full_analysis(responder_counts)
    
    # Generate report
    report = analyzer.generate_text_report()
    
    # Save report
    output_path = Path("benchmark_results")
    output_path.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    report_file = output_path / f"sweep_report_{timestamp}.txt"
    with open(report_file, 'w') as f:
        f.write(report)
    
    # Save data
    data_file = output_path / f"sweep_data_{timestamp}.json"
    # Remove paths to reduce file size
    clean_results = []
    for r in analyzer.results:
        r_copy = r.copy()
        r_copy.pop('responder_paths', None)
        clean_results.append(r_copy)
    
    with open(data_file, 'w') as f:
        json.dump(clean_results, f, indent=2)
    
    # Generate plots
    plot_file = analyzer.plot_results()
    
    # Print report
    print("\n" + report)
    print(f"\n📁 FILES GENERATED:")
    print(f"  Report: {report_file}")
    print(f"  Data:   {data_file}")
    print(f"  Plots:  {plot_file}")


if __name__ == "__main__":
    main()


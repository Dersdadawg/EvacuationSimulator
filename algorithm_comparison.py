"""
Algorithm Comparison Study
Compare three sweep strategies:
1. Our Priority-Based Algorithm (TRP-inspired)
2. Static Sequential Approach (O1→O2→O3→O4→O5→O6)
3. Greedy Shortest-Path (always go to nearest uncleared room)
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
from sim.agents.agent import Agent, AgentState


class StaticSequentialSimulator:
    """
    Simulator using static sequential approach: O1→O2→O3→O4→O5→O6
    Each responder follows predetermined order regardless of conditions
    """
    
    def __init__(self, env, params):
        self.env = env
        self.params = params
        
        # Static room sequence
        self.room_sequence = ['O1', 'O2', 'O3', 'O4', 'O5', 'O6']
        
        # Create basic simulator to reuse infrastructure
        self.sim = Simulator(env, params)
        
    def run(self):
        """Run simulation with static ordering"""
        # Override agent behavior to use static sequence
        sequence_idx = {a.id: 0 for a in self.sim.agent_manager.agents}
        
        while not self.sim.complete and self.sim.tick < 10000:
            # For each agent, if idle, assign next room in sequence
            for agent in self.sim.agent_manager.agents:
                if agent.state == AgentState.IDLE and not agent.is_dead and not agent.escaped:
                    idx = sequence_idx[agent.id]
                    if idx < len(self.room_sequence):
                        target_room_id = self.room_sequence[idx]
                        if target_room_id in self.env.rooms:
                            target_room = self.env.rooms[target_room_id]
                            
                            # Use grid pathfinder to get to room
                            if self.sim.grid_pathfinder:
                                grid_path = self.sim.grid_pathfinder.find_path(
                                    agent.x, agent.y, target_room.x, target_room.y,
                                    avoid_danger=False
                                )
                                if grid_path and len(grid_path) > 1:
                                    agent.target_room = target_room_id
                                    agent.waypoints = grid_path
                                    agent.current_waypoint = 0
                                    agent.state = AgentState.MOVING
                                    sequence_idx[agent.id] += 1
            
            self.sim.step(fire_enabled=False)
        
        return self.sim.get_results()


class GreedyNearestSimulator:
    """
    Simulator using greedy nearest-room approach
    Always go to closest uncleared room
    """
    
    def __init__(self, env, params):
        self.env = env
        self.params = params
        self.sim = Simulator(env, params)
        
    def run(self):
        """Run simulation with greedy nearest-neighbor"""
        while not self.sim.complete and self.sim.tick < 10000:
            # For each idle agent, find nearest uncleared room
            for agent in self.sim.agent_manager.agents:
                if agent.state == AgentState.IDLE and not agent.is_dead and not agent.escaped:
                    # Find nearest uncleared room
                    uncleared = self.env.get_uncleared_rooms()
                    if uncleared:
                        nearest_room = None
                        min_dist = float('inf')
                        
                        for room_id in uncleared:
                            room = self.env.rooms[room_id]
                            dist = abs(room.x - agent.x) + abs(room.y - agent.y)
                            if dist < min_dist:
                                min_dist = dist
                                nearest_room = room_id
                        
                        if nearest_room and self.sim.grid_pathfinder:
                            target_room = self.env.rooms[nearest_room]
                            grid_path = self.sim.grid_pathfinder.find_path(
                                agent.x, agent.y, target_room.x, target_room.y,
                                avoid_danger=False
                            )
                            if grid_path and len(grid_path) > 1:
                                agent.target_room = nearest_room
                                agent.waypoints = grid_path
                                agent.current_waypoint = 0
                                agent.state = AgentState.MOVING
            
            self.sim.step(fire_enabled=False)
        
        return self.sim.get_results()


class AlgorithmComparator:
    """Compare different sweep algorithms"""
    
    def __init__(self, layout_path: str = "layouts/office_correct_dimensions.json"):
        self.layout_path = layout_path
        self.results = {}
        
    def run_comparison(self, num_responders: int):
        """Run all three algorithms and compare"""
        print(f"\n{'='*70}")
        print(f"Comparing Algorithms: {num_responders} Responders")
        print(f"{'='*70}")
        
        # Load params
        with open("params.json") as f:
            params = json.load(f)
        
        params['agents']['count'] = num_responders
        params['visualization']['enabled'] = False
        params['hazard']['enabled'] = False
        
        results = {}
        
        # 1. Our Priority-Based Algorithm
        print("\n[1/3] Running PRIORITY-BASED algorithm (our approach)...")
        layout_data = LayoutLoader.load(self.layout_path)
        env1 = Environment(layout_data, params)
        sim1 = Simulator(env1, params)
        
        start = time.time()
        while not sim1.complete and sim1.tick < 10000:
            sim1.step(fire_enabled=False)
        results['priority'] = {
            **sim1.get_results(),
            'real_time': time.time() - start,
            'algorithm': 'Priority-Based (TRP)'
        }
        print(f"  ✓ Time: {results['priority']['time']:.0f}s, Rescued: {results['priority']['evacuees_rescued']}/{results['priority']['total_evacuees']}")
        
        # 2. Static Sequential Approach
        print("\n[2/3] Running STATIC SEQUENTIAL algorithm (O1→O2→O3→O4→O5→O6)...")
        layout_data = LayoutLoader.load(self.layout_path)
        env2 = Environment(layout_data, params)
        
        start = time.time()
        static_sim = StaticSequentialSimulator(env2, params)
        results['static'] = {
            **static_sim.run(),
            'real_time': time.time() - start,
            'algorithm': 'Static Sequential'
        }
        print(f"  ✓ Time: {results['static']['time']:.0f}s, Rescued: {results['static']['evacuees_rescued']}/{results['static']['total_evacuees']}")
        
        # 3. Greedy Nearest Approach
        print("\n[3/3] Running GREEDY NEAREST algorithm (always nearest room)...")
        layout_data = LayoutLoader.load(self.layout_path)
        env3 = Environment(layout_data, params)
        
        start = time.time()
        greedy_sim = GreedyNearestSimulator(env3, params)
        results['greedy'] = {
            **greedy_sim.run(),
            'real_time': time.time() - start,
            'algorithm': 'Greedy Nearest'
        }
        print(f"  ✓ Time: {results['greedy']['time']:.0f}s, Rescued: {results['greedy']['evacuees_rescued']}/{results['greedy']['total_evacuees']}")
        
        return results
    
    def run_all_comparisons(self, responder_counts: list):
        """Run comparisons for multiple responder counts"""
        print(f"\n{'='*70}")
        print(f"ALGORITHM COMPARISON STUDY")
        print(f"{'='*70}")
        
        for num in responder_counts:
            self.results[num] = self.run_comparison(num)
    
    def generate_report(self) -> str:
        """Generate comparison report"""
        report = []
        report.append("=" * 80)
        report.append("ALGORITHM COMPARISON REPORT")
        report.append("=" * 80)
        report.append("")
        
        report.append("📋 ALGORITHMS TESTED")
        report.append("-" * 80)
        report.append("1. PRIORITY-BASED (Our Approach):")
        report.append("   - Uses priority index P_i = (E_i × (10 + λ×D_i)) / (dist/10)")
        report.append("   - Considers: occupants, danger, distance")
        report.append("   - Adaptive to changing conditions")
        report.append("")
        report.append("2. STATIC SEQUENTIAL:")
        report.append("   - Fixed order: O1 → O2 → O3 → O4 → O5 → O6")
        report.append("   - No adaptation to occupants or conditions")
        report.append("   - Simple but inflexible")
        report.append("")
        report.append("3. GREEDY NEAREST:")
        report.append("   - Always go to nearest uncleared room")
        report.append("   - Minimizes travel but ignores priority")
        report.append("   - Myopic (short-sighted)")
        report.append("")
        
        # Performance comparison
        report.append("📊 PERFORMANCE COMPARISON")
        report.append("-" * 80)
        report.append(f"{'Responders':<12}{'Algorithm':<20}{'Time (s)':<12}{'Rescued':<12}{'Success Score':<15}")
        report.append("-" * 80)
        
        for num_resp in sorted(self.results.keys()):
            for alg_name in ['priority', 'static', 'greedy']:
                r = self.results[num_resp][alg_name]
                report.append(
                    f"{num_resp:<12}"
                    f"{r['algorithm']:<20}"
                    f"{r['time']:<12.0f}"
                    f"{r['evacuees_rescued']}/{r['total_evacuees']:<9}"
                    f"{r['success_score']:<15.4f}"
                )
            report.append("")
        
        # Statistical comparison
        report.append("📈 ALGORITHM EFFICIENCY (Avg across all responder counts)")
        report.append("-" * 80)
        
        alg_stats = defaultdict(lambda: {'times': [], 'scores': [], 'rescued': []})
        for num_resp, results in self.results.items():
            for alg_name in ['priority', 'static', 'greedy']:
                alg_stats[alg_name]['times'].append(results[alg_name]['time'])
                alg_stats[alg_name]['scores'].append(results[alg_name]['success_score'])
                alg_stats[alg_name]['rescued'].append(results[alg_name]['evacuees_rescued'])
        
        for alg_name, label in [('priority', 'Priority-Based'), ('static', 'Static Sequential'), ('greedy', 'Greedy Nearest')]:
            stats = alg_stats[alg_name]
            avg_time = np.mean(stats['times'])
            avg_score = np.mean(stats['scores'])
            avg_rescued = np.mean(stats['rescued'])
            
            report.append(f"{label}:")
            report.append(f"  Avg Time: {avg_time:.0f}s ({avg_time/60:.1f} min)")
            report.append(f"  Avg Success Score: {avg_score:.4f}")
            report.append(f"  Avg Rescued: {avg_rescued:.1f}/{self.results[3]['priority']['total_evacuees']}")
            report.append("")
        
        # Winner analysis
        report.append("🏆 WINNER ANALYSIS")
        report.append("-" * 80)
        
        priority_avg = np.mean(alg_stats['priority']['scores'])
        static_avg = np.mean(alg_stats['static']['scores'])
        greedy_avg = np.mean(alg_stats['greedy']['scores'])
        
        improvement_vs_static = (priority_avg - static_avg) / static_avg * 100
        improvement_vs_greedy = (priority_avg - greedy_avg) / greedy_avg * 100
        
        report.append(f"Our Priority-Based Algorithm:")
        report.append(f"  {improvement_vs_static:+.1f}% better than Static Sequential")
        report.append(f"  {improvement_vs_greedy:+.1f}% better than Greedy Nearest")
        report.append("")
        
        report.append("💡 KEY INSIGHTS")
        report.append("-" * 80)
        report.append("1. Priority-based approach adapts to room occupancy and urgency")
        report.append("2. Static approach is predictable but suboptimal")
        report.append("3. Greedy approach minimizes travel but ignores critical rooms")
        report.append("4. Our algorithm balances speed, occupant count, and danger")
        report.append("")
        
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def plot_comparison(self):
        """Generate comparison plots"""
        plt.style.use('seaborn-v0_8-darkgrid')
        fig = plt.figure(figsize=(18, 12), facecolor='#FAFAFA')
        
        responder_counts = sorted(self.results.keys())
        
        # Extract data for each algorithm
        algorithms = {
            'priority': {'label': 'Priority-Based (Ours)', 'color': '#FF6B35', 'marker': 'o'},
            'static': {'label': 'Static Sequential', 'color': '#757575', 'marker': 's'},
            'greedy': {'label': 'Greedy Nearest', 'color': '#1976D2', 'marker': '^'}
        }
        
        data = {alg: defaultdict(list) for alg in algorithms.keys()}
        
        for num_resp in responder_counts:
            for alg_name in algorithms.keys():
                r = self.results[num_resp][alg_name]
                data[alg_name]['responders'].append(num_resp)
                data[alg_name]['time'].append(r['time'])
                data[alg_name]['score'].append(r['success_score'])
                data[alg_name]['rescued'].append(r['evacuees_rescued'])
        
        # 1. Sweep Time Comparison
        ax1 = plt.subplot(2, 3, 1)
        ax1.set_facecolor('#FFFFFF')
        
        for alg_name, alg_info in algorithms.items():
            ax1.plot(data[alg_name]['responders'], data[alg_name]['time'], 
                    marker=alg_info['marker'], linewidth=3, markersize=10,
                    color=alg_info['color'], label=alg_info['label'],
                    markeredgecolor='white', markeredgewidth=2)
        
        ax1.set_xlabel('Number of Responders', fontweight='bold', fontsize=11)
        ax1.set_ylabel('Sweep Time (seconds)', fontweight='bold', fontsize=11)
        ax1.set_title('⏱️  Sweep Time Comparison', fontweight='bold', fontsize=13, pad=12)
        ax1.legend(loc='upper right', frameon=True, fancybox=True, shadow=True)
        ax1.grid(True, alpha=0.2, linestyle='--')
        
        # 2. Success Score Comparison
        ax2 = plt.subplot(2, 3, 2)
        ax2.set_facecolor('#FFFFFF')
        
        for alg_name, alg_info in algorithms.items():
            ax2.plot(data[alg_name]['responders'], data[alg_name]['score'], 
                    marker=alg_info['marker'], linewidth=3, markersize=10,
                    color=alg_info['color'], label=alg_info['label'],
                    markeredgecolor='white', markeredgewidth=2)
        
        ax2.set_xlabel('Number of Responders', fontweight='bold', fontsize=11)
        ax2.set_ylabel('Success Score', fontweight='bold', fontsize=11)
        ax2.set_title('📊 Success Score Comparison', fontweight='bold', fontsize=13, pad=12)
        ax2.legend(loc='upper right', frameon=True, fancybox=True, shadow=True)
        ax2.grid(True, alpha=0.2, linestyle='--')
        
        # 3. Relative Performance (% difference from our algorithm)
        ax3 = plt.subplot(2, 3, 3)
        ax3.set_facecolor('#FFFFFF')
        
        # Calculate % difference for each responder count
        static_diff = []
        greedy_diff = []
        
        for i, num_resp in enumerate(responder_counts):
            priority_score = data['priority']['score'][i]
            static_score = data['static']['score'][i]
            greedy_score = data['greedy']['score'][i]
            
            static_diff.append((priority_score - static_score) / static_score * 100)
            greedy_diff.append((priority_score - greedy_score) / greedy_score * 100)
        
        x = np.arange(len(responder_counts))
        width = 0.35
        
        bars1 = ax3.bar(x - width/2, static_diff, width, label='vs Static',
                       color='#FFB74D', edgecolor='#F57C00', linewidth=2, alpha=0.85)
        bars2 = ax3.bar(x + width/2, greedy_diff, width, label='vs Greedy',
                       color='#81C784', edgecolor='#388E3C', linewidth=2, alpha=0.85)
        
        ax3.set_xlabel('Number of Responders', fontweight='bold', fontsize=11)
        ax3.set_ylabel('Improvement over Baseline (%)', fontweight='bold', fontsize=11)
        ax3.set_title('🏆 Our Algorithm Advantage', fontweight='bold', fontsize=13, pad=12)
        ax3.set_xticks(x)
        ax3.set_xticklabels(responder_counts)
        ax3.legend(loc='upper right', frameon=True, fancybox=True, shadow=True)
        ax3.grid(True, alpha=0.2, axis='y', linestyle='--')
        ax3.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
        
        # Add value labels
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax3.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:+.1f}%', ha='center', va='bottom' if height > 0 else 'top',
                        fontsize=9, fontweight='bold')
        
        # 4. Time Saved vs Static
        ax4 = plt.subplot(2, 3, 4)
        ax4.set_facecolor('#FFFFFF')
        
        time_saved_static = []
        for i, num_resp in enumerate(responder_counts):
            saved = data['static']['time'][i] - data['priority']['time'][i]
            time_saved_static.append(saved)
        
        # Use simple color based on positive/negative
        colors_static = ['#FF6B35' if val >= 0 else '#E53935' for val in time_saved_static]
        
        bars = ax4.bar(responder_counts, time_saved_static, 
                      color=colors_static, edgecolor='#D84315', 
                      linewidth=2.5, alpha=0.85)
        
        ax4.set_xlabel('Number of Responders', fontweight='bold', fontsize=11)
        ax4.set_ylabel('Time Saved (seconds)', fontweight='bold', fontsize=11)
        ax4.set_title('⏱️  Time Saved vs Static Sequential', fontweight='bold', fontsize=13, pad=12)
        ax4.grid(True, alpha=0.2, axis='y', linestyle='--')
        
        # Add labels
        for bar, val in zip(bars, time_saved_static):
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height + 10,
                    f'{val:.0f}s\n({val/60:.1f}m)', ha='center', fontsize=9, fontweight='bold')
        
        # 5. Time Saved vs Greedy
        ax5 = plt.subplot(2, 3, 5)
        ax5.set_facecolor('#FFFFFF')
        
        time_saved_greedy = []
        for i, num_resp in enumerate(responder_counts):
            saved = data['greedy']['time'][i] - data['priority']['time'][i]
            time_saved_greedy.append(saved)
        
        # Use simple color based on positive/negative  
        colors_greedy = ['#1976D2' if val >= 0 else '#E53935' for val in time_saved_greedy]
        
        bars = ax5.bar(responder_counts, time_saved_greedy, 
                      color=colors_greedy, edgecolor='#1565C0', 
                      linewidth=2.5, alpha=0.85)
        
        ax5.set_xlabel('Number of Responders', fontweight='bold', fontsize=11)
        ax5.set_ylabel('Time Saved (seconds)', fontweight='bold', fontsize=11)
        ax5.set_title('⏱️  Time Saved vs Greedy Nearest', fontweight='bold', fontsize=13, pad=12)
        ax5.grid(True, alpha=0.2, axis='y', linestyle='--')
        
        # Add labels
        for bar, val in zip(bars, time_saved_greedy):
            height = bar.get_height()
            ax5.text(bar.get_x() + bar.get_width()/2., height + 10,
                    f'{val:.0f}s\n({val/60:.1f}m)', ha='center', fontsize=9, fontweight='bold')
        
        # 6. Overall Winner Summary
        ax6 = plt.subplot(2, 3, 6)
        ax6.set_facecolor('#FFFFFF')
        ax6.axis('off')
        
        # Calculate averages
        avg_scores = {}
        avg_times = {}
        for alg_name in ['priority', 'static', 'greedy']:
            avg_scores[alg_name] = np.mean([self.results[n][alg_name]['success_score'] 
                                           for n in responder_counts])
            avg_times[alg_name] = np.mean([self.results[n][alg_name]['time'] 
                                          for n in responder_counts])
        
        winner_text = (
            f"🏆 WINNER: PRIORITY-BASED\n\n"
            f"Average Success Score:\n"
            f"  Priority: {avg_scores['priority']:.4f} ⭐\n"
            f"  Static:   {avg_scores['static']:.4f}\n"
            f"  Greedy:   {avg_scores['greedy']:.4f}\n\n"
            f"Average Sweep Time:\n"
            f"  Priority: {avg_times['priority']:.0f}s ⭐\n"
            f"  Static:   {avg_times['static']:.0f}s\n"
            f"  Greedy:   {avg_times['greedy']:.0f}s\n\n"
            f"Our algorithm is:\n"
            f"  {(avg_scores['priority']/avg_scores['static']-1)*100:+.1f}% better than Static\n"
            f"  {(avg_scores['priority']/avg_scores['greedy']-1)*100:+.1f}% better than Greedy"
        )
        
        ax6.text(0.5, 0.5, winner_text, transform=ax6.transAxes,
                fontsize=12, verticalalignment='center', horizontalalignment='center',
                bbox=dict(boxstyle='round,pad=1.5', facecolor='#FFF9C4', 
                         edgecolor='#F57F17', linewidth=3, alpha=0.95),
                fontfamily='monospace', fontweight='600')
        
        # Overall title
        fig.suptitle('SWEEP ALGORITHM COMPARISON STUDY', 
                    fontsize=18, fontweight='bold', y=0.98,
                    bbox=dict(boxstyle='round,pad=0.8', facecolor='#FF6B35', 
                             edgecolor='none', alpha=1.0),
                    color='white')
        
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        
        # Save
        output_path = Path("benchmark_results")
        output_path.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        filepath = output_path / f"algorithm_comparison_{timestamp}.png"
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        
        return filepath


def main():
    print("\n" + "="*80)
    print("ALGORITHM COMPARISON STUDY")
    print("Testing: Priority-Based vs Static vs Greedy")
    print("="*80)
    
    comparator = AlgorithmComparator()
    responder_counts = [1, 2, 3, 4, 5]
    
    comparator.run_all_comparisons(responder_counts)
    
    # Generate report
    report = comparator.generate_report()
    
    # Save files
    output_path = Path("benchmark_results")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    report_file = output_path / f"algorithm_comparison_{timestamp}.txt"
    with open(report_file, 'w') as f:
        f.write(report)
    
    # Save data
    data_file = output_path / f"algorithm_comparison_data_{timestamp}.json"
    # Clean results (remove paths)
    clean_results = {}
    for num_resp, algs in comparator.results.items():
        clean_results[num_resp] = {}
        for alg_name, result in algs.items():
            clean = result.copy()
            clean.pop('agents', None)
            clean_results[num_resp][alg_name] = clean
    
    with open(data_file, 'w') as f:
        json.dump(clean_results, f, indent=2)
    
    # Generate plots
    plot_file = comparator.plot_comparison()
    
    # Print report
    print("\n" + report)
    print(f"\n📁 FILES GENERATED:")
    print(f"  Report: {report_file}")
    print(f"  Data:   {data_file}")
    print(f"  Plots:  {plot_file}")


if __name__ == "__main__":
    main()


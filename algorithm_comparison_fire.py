"""
Algorithm Comparison Study - WITH FIRE
Compare three sweep strategies under fire conditions:
1. Our Priority-Based Algorithm (considers danger)
2. Static Sequential Approach (fixed order)
3. Greedy Shortest-Path (ignores danger - should be catastrophic)
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
    """Static sequential approach with fire"""
    
    def __init__(self, env, params):
        self.env = env
        self.params = params
        self.room_sequence = ['O1', 'O2', 'O3', 'O4', 'O5', 'O6']
        self.sim = Simulator(env, params)
        
    def run(self):
        """Run simulation with static ordering"""
        sequence_idx = {a.id: 0 for a in self.sim.agent_manager.agents}
        
        while not self.sim.complete and self.sim.tick < 10000:
            for agent in self.sim.agent_manager.agents:
                if agent.state == AgentState.IDLE and not agent.is_dead and not agent.escaped:
                    idx = sequence_idx[agent.id]
                    if idx < len(self.room_sequence):
                        target_room_id = self.room_sequence[idx]
                        if target_room_id in self.env.rooms:
                            target_room = self.env.rooms[target_room_id]
                            
                            if self.sim.grid_pathfinder:
                                # Static doesn't avoid danger - just shortest path
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
            
            self.sim.step(fire_enabled=True)  # FIRE ON!
        
        return self.sim.get_results()


class GreedyNearestSimulator:
    """Greedy nearest-room with fire (should be dangerous!)"""
    
    def __init__(self, env, params):
        self.env = env
        self.params = params
        self.sim = Simulator(env, params)
        
    def run(self):
        """Run simulation with greedy nearest-neighbor"""
        while not self.sim.complete and self.sim.tick < 10000:
            for agent in self.sim.agent_manager.agents:
                if agent.state == AgentState.IDLE and not agent.is_dead and not agent.escaped:
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
                            # Greedy doesn't avoid danger - just shortest path!
                            grid_path = self.sim.grid_pathfinder.find_path(
                                agent.x, agent.y, target_room.x, target_room.y,
                                avoid_danger=False  # DANGEROUS!
                            )
                            if grid_path and len(grid_path) > 1:
                                agent.target_room = nearest_room
                                agent.waypoints = grid_path
                                agent.current_waypoint = 0
                                agent.state = AgentState.MOVING
            
            self.sim.step(fire_enabled=True)  # FIRE ON!
        
        return self.sim.get_results()


class FireAlgorithmComparator:
    """Compare algorithms under fire conditions"""
    
    def __init__(self, layout_path: str = "layouts/office_correct_dimensions.json"):
        self.layout_path = layout_path
        self.results = {}
        
    def run_comparison(self, num_responders: int):
        """Run all three algorithms with fire"""
        print(f"\n{'='*70}")
        print(f"🔥 Comparing Algorithms WITH FIRE: {num_responders} Responders")
        print(f"{'='*70}")
        
        # Load params
        with open("params.json") as f:
            params = json.load(f)
        
        params['agents']['count'] = num_responders
        params['visualization']['enabled'] = False
        params['hazard']['enabled'] = True  # FIRE ON!
        
        results = {}
        
        # 1. Our Priority-Based Algorithm (considers danger)
        print("\n[1/3] Running PRIORITY-BASED algorithm (danger-aware)...")
        layout_data = LayoutLoader.load(self.layout_path)
        env1 = Environment(layout_data, params)
        sim1 = Simulator(env1, params)
        
        start = time.time()
        while not sim1.complete and sim1.tick < 10000:
            sim1.step(fire_enabled=True)
        
        num_alive = sum(1 for a in sim1.agent_manager.agents if not a.is_dead)
        num_escaped = sum(1 for a in sim1.agent_manager.agents if a.escaped)
        
        results['priority'] = {
            **sim1.get_results(),
            'real_time': time.time() - start,
            'algorithm': 'Priority-Based (TRP)',
            'responders_alive': num_alive,
            'responders_escaped': num_escaped,
            'responder_deaths': num_responders - num_alive
        }
        print(f"  ✓ Time: {results['priority']['time']:.0f}s")
        print(f"    Rescued: {results['priority']['evacuees_rescued']}/{results['priority']['total_evacuees']}")
        print(f"    Responders: {num_alive} alive, {num_escaped} escaped, {num_responders - num_alive} died")
        
        # 2. Static Sequential
        print("\n[2/3] Running STATIC SEQUENTIAL algorithm (no danger avoidance)...")
        layout_data = LayoutLoader.load(self.layout_path)
        env2 = Environment(layout_data, params)
        
        start = time.time()
        static_sim = StaticSequentialSimulator(env2, params)
        static_results = static_sim.run()
        
        num_alive = sum(1 for a in static_sim.sim.agent_manager.agents if not a.is_dead)
        num_escaped = sum(1 for a in static_sim.sim.agent_manager.agents if a.escaped)
        
        results['static'] = {
            **static_results,
            'real_time': time.time() - start,
            'algorithm': 'Static Sequential',
            'responders_alive': num_alive,
            'responders_escaped': num_escaped,
            'responder_deaths': num_responders - num_alive
        }
        print(f"  ✓ Time: {results['static']['time']:.0f}s")
        print(f"    Rescued: {results['static']['evacuees_rescued']}/{results['static']['total_evacuees']}")
        print(f"    Responders: {num_alive} alive, {num_escaped} escaped, {num_responders - num_alive} died")
        
        # 3. Greedy Nearest (should be very dangerous!)
        print("\n[3/3] Running GREEDY NEAREST algorithm (DANGER! No safety!)...")
        layout_data = LayoutLoader.load(self.layout_path)
        env3 = Environment(layout_data, params)
        
        start = time.time()
        greedy_sim = GreedyNearestSimulator(env3, params)
        greedy_results = greedy_sim.run()
        
        num_alive = sum(1 for a in greedy_sim.sim.agent_manager.agents if not a.is_dead)
        num_escaped = sum(1 for a in greedy_sim.sim.agent_manager.agents if a.escaped)
        
        results['greedy'] = {
            **greedy_results,
            'real_time': time.time() - start,
            'algorithm': 'Greedy Nearest',
            'responders_alive': num_alive,
            'responders_escaped': num_escaped,
            'responder_deaths': num_responders - num_alive
        }
        print(f"  ✓ Time: {results['greedy']['time']:.0f}s")
        print(f"    Rescued: {results['greedy']['evacuees_rescued']}/{results['greedy']['total_evacuees']}")
        print(f"    Responders: {num_alive} alive, {num_escaped} escaped, {num_responders - num_alive} died")
        
        return results
    
    def run_all_comparisons(self, responder_counts: list):
        """Run comparisons for multiple responder counts"""
        print(f"\n{'='*70}")
        print(f"🔥 ALGORITHM COMPARISON STUDY - WITH FIRE")
        print(f"{'='*70}")
        
        for num in responder_counts:
            self.results[num] = self.run_comparison(num)
    
    def generate_report(self) -> str:
        """Generate comparison report"""
        report = []
        report.append("=" * 80)
        report.append("🔥 ALGORITHM COMPARISON REPORT - WITH FIRE")
        report.append("=" * 80)
        report.append("")
        
        # Performance comparison
        report.append("📊 PERFORMANCE COMPARISON")
        report.append("-" * 80)
        report.append(f"{'Resp':<6}{'Algorithm':<20}{'Time':<10}{'Rescued':<12}{'Deaths':<10}{'Success':<12}")
        report.append("-" * 80)
        
        for num_resp in sorted(self.results.keys()):
            for alg_name in ['priority', 'static', 'greedy']:
                r = self.results[num_resp][alg_name]
                report.append(
                    f"{num_resp:<6}"
                    f"{r['algorithm']:<20}"
                    f"{r['time']:<10.0f}"
                    f"{r['evacuees_rescued']}/{r['total_evacuees']:<9}"
                    f"{r['responder_deaths']}/{num_resp:<8}"
                    f"{r['success_score']:<12.4f}"
                )
            report.append("")
        
        # Statistical comparison
        report.append("📈 ALGORITHM PERFORMANCE (Avg across all responder counts)")
        report.append("-" * 80)
        
        alg_stats = defaultdict(lambda: {'scores': [], 'rescued': [], 'deaths': [], 'alive': []})
        for num_resp, results in self.results.items():
            for alg_name in ['priority', 'static', 'greedy']:
                alg_stats[alg_name]['scores'].append(results[alg_name]['success_score'])
                alg_stats[alg_name]['rescued'].append(results[alg_name]['evacuees_rescued'])
                alg_stats[alg_name]['deaths'].append(results[alg_name]['responder_deaths'])
                alg_stats[alg_name]['alive'].append(results[alg_name]['responders_alive'])
        
        for alg_name, label in [('priority', 'Priority-Based'), ('static', 'Static'), ('greedy', 'Greedy')]:
            stats = alg_stats[alg_name]
            avg_score = np.mean(stats['scores'])
            avg_rescued = np.mean(stats['rescued'])
            avg_deaths = np.mean(stats['deaths'])
            avg_alive = np.mean(stats['alive'])
            
            report.append(f"{label}:")
            report.append(f"  Avg Success Score: {avg_score:.4f}")
            report.append(f"  Avg Occupants Rescued: {avg_rescued:.1f}/17")
            report.append(f"  Avg Responder Deaths: {avg_deaths:.1f}")
            report.append(f"  Avg Responders Alive: {avg_alive:.1f}")
            report.append("")
        
        # Winner analysis
        report.append("🏆 WINNER WITH FIRE")
        report.append("-" * 80)
        
        priority_score = np.mean(alg_stats['priority']['scores'])
        static_score = np.mean(alg_stats['static']['scores'])
        greedy_score = np.mean(alg_stats['greedy']['scores'])
        
        priority_deaths = np.mean(alg_stats['priority']['deaths'])
        static_deaths = np.mean(alg_stats['static']['deaths'])
        greedy_deaths = np.mean(alg_stats['greedy']['deaths'])
        
        report.append(f"Success Score:")
        report.append(f"  Priority: {priority_score:.4f}")
        report.append(f"  Static:   {static_score:.4f}")
        report.append(f"  Greedy:   {greedy_score:.4f}")
        report.append("")
        report.append(f"Responder Deaths (Avg):")
        report.append(f"  Priority: {priority_deaths:.1f}")
        report.append(f"  Static:   {static_deaths:.1f}")
        report.append(f"  Greedy:   {greedy_deaths:.1f}")
        report.append("")
        
        # Determine winner
        best_alg = max([('priority', priority_score), ('static', static_score), ('greedy', greedy_score)],
                      key=lambda x: x[1])
        report.append(f"WINNER: {best_alg[0].upper()}")
        report.append("")
        
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def plot_comparison(self):
        """Generate comparison plots with fire"""
        plt.style.use('seaborn-v0_8-darkgrid')
        fig = plt.figure(figsize=(18, 12), facecolor='#FAFAFA')
        
        responder_counts = sorted(self.results.keys())
        
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
                data[alg_name]['score'].append(r['success_score'])
                data[alg_name]['rescued'].append(r['evacuees_rescued'])
                data[alg_name]['deaths'].append(r['responder_deaths'])
                data[alg_name]['alive'].append(r['responders_alive'])
        
        # 1. Success Score Comparison
        ax1 = plt.subplot(2, 3, 1)
        ax1.set_facecolor('#FFFFFF')
        
        for alg_name, alg_info in algorithms.items():
            ax1.plot(data[alg_name]['responders'], data[alg_name]['score'], 
                    marker=alg_info['marker'], linewidth=3, markersize=10,
                    color=alg_info['color'], label=alg_info['label'],
                    markeredgecolor='white', markeredgewidth=2)
        
        ax1.set_xlabel('Number of Responders', fontweight='bold', fontsize=11)
        ax1.set_ylabel('Success Score', fontweight='bold', fontsize=11)
        ax1.set_title('📊 Success Score (WITH FIRE)', fontweight='bold', fontsize=13, pad=12)
        ax1.legend(loc='best', frameon=True, fancybox=True, shadow=True)
        ax1.grid(True, alpha=0.2, linestyle='--')
        
        # 2. Occupants Rescued
        ax2 = plt.subplot(2, 3, 2)
        ax2.set_facecolor('#FFFFFF')
        
        for alg_name, alg_info in algorithms.items():
            ax2.plot(data[alg_name]['responders'], data[alg_name]['rescued'], 
                    marker=alg_info['marker'], linewidth=3, markersize=10,
                    color=alg_info['color'], label=alg_info['label'],
                    markeredgecolor='white', markeredgewidth=2)
        
        ax2.set_xlabel('Number of Responders', fontweight='bold', fontsize=11)
        ax2.set_ylabel('Occupants Rescued', fontweight='bold', fontsize=11)
        ax2.set_title('🚑 Occupants Rescued (WITH FIRE)', fontweight='bold', fontsize=13, pad=12)
        ax2.legend(loc='best', frameon=True, fancybox=True, shadow=True)
        ax2.grid(True, alpha=0.2, linestyle='--')
        ax2.set_ylim([0, 18])
        
        # 3. Responder Deaths
        ax3 = plt.subplot(2, 3, 3)
        ax3.set_facecolor('#FFFFFF')
        
        for alg_name, alg_info in algorithms.items():
            ax3.plot(data[alg_name]['responders'], data[alg_name]['deaths'], 
                    marker=alg_info['marker'], linewidth=3, markersize=10,
                    color=alg_info['color'], label=alg_info['label'],
                    markeredgecolor='white', markeredgewidth=2)
        
        ax3.set_xlabel('Number of Responders', fontweight='bold', fontsize=11)
        ax3.set_ylabel('Responder Deaths', fontweight='bold', fontsize=11)
        ax3.set_title('💀 Responder Casualties (WITH FIRE)', fontweight='bold', fontsize=13, pad=12)
        ax3.legend(loc='best', frameon=True, fancybox=True, shadow=True)
        ax3.grid(True, alpha=0.2, linestyle='--')
        
        # 4. Responders Alive
        ax4 = plt.subplot(2, 3, 4)
        ax4.set_facecolor('#FFFFFF')
        
        for alg_name, alg_info in algorithms.items():
            ax4.plot(data[alg_name]['responders'], data[alg_name]['alive'], 
                    marker=alg_info['marker'], linewidth=3, markersize=10,
                    color=alg_info['color'], label=alg_info['label'],
                    markeredgecolor='white', markeredgewidth=2)
        
        ax4.set_xlabel('Number of Responders', fontweight='bold', fontsize=11)
        ax4.set_ylabel('Responders Alive', fontweight='bold', fontsize=11)
        ax4.set_title('🚒 Responder Survival (WITH FIRE)', fontweight='bold', fontsize=13, pad=12)
        ax4.legend(loc='best', frameon=True, fancybox=True, shadow=True)
        ax4.grid(True, alpha=0.2, linestyle='--')
        
        # 5. Success Score Advantage
        ax5 = plt.subplot(2, 3, 5)
        ax5.set_facecolor('#FFFFFF')
        
        # Calculate advantage over other algorithms
        vs_static = []
        vs_greedy = []
        
        for i, num_resp in enumerate(responder_counts):
            priority_score = data['priority']['score'][i]
            static_score = data['static']['score'][i]
            greedy_score = data['greedy']['score'][i]
            
            vs_static.append((priority_score - static_score) / static_score * 100 if static_score > 0 else 0)
            vs_greedy.append((priority_score - greedy_score) / greedy_score * 100 if greedy_score > 0 else 0)
        
        x = np.arange(len(responder_counts))
        width = 0.35
        
        bars1 = ax5.bar(x - width/2, vs_static, width, label='vs Static',
                       color='#FFB74D', edgecolor='#F57C00', linewidth=2, alpha=0.85)
        bars2 = ax5.bar(x + width/2, vs_greedy, width, label='vs Greedy',
                       color='#81C784', edgecolor='#388E3C', linewidth=2, alpha=0.85)
        
        ax5.set_xlabel('Number of Responders', fontweight='bold', fontsize=11)
        ax5.set_ylabel('Success Score Advantage (%)', fontweight='bold', fontsize=11)
        ax5.set_title('🏆 Our Algorithm Advantage (WITH FIRE)', fontweight='bold', fontsize=13, pad=12)
        ax5.set_xticks(x)
        ax5.set_xticklabels(responder_counts)
        ax5.legend(loc='best', frameon=True, fancybox=True, shadow=True)
        ax5.grid(True, alpha=0.2, axis='y', linestyle='--')
        ax5.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
        
        # Add value labels
        for bars in [bars1, bars2]:
            for bar in bars:
                height = bar.get_height()
                ax5.text(bar.get_x() + bar.get_width()/2., height,
                        f'{height:+.0f}%', ha='center', va='bottom' if height > 0 else 'top',
                        fontsize=9, fontweight='bold')
        
        # 6. Summary Box
        ax6 = plt.subplot(2, 3, 6)
        ax6.set_facecolor('#FFFFFF')
        ax6.axis('off')
        
        # Calculate averages
        avg_scores = {alg: np.mean([self.results[n][alg]['success_score'] for n in responder_counts])
                     for alg in ['priority', 'static', 'greedy']}
        avg_deaths = {alg: np.mean([self.results[n][alg]['responder_deaths'] for n in responder_counts])
                     for alg in ['priority', 'static', 'greedy']}
        avg_rescued = {alg: np.mean([self.results[n][alg]['evacuees_rescued'] for n in responder_counts])
                      for alg in ['priority', 'static', 'greedy']}
        
        summary_text = (
            f"🔥 FIRE SIMULATION RESULTS\n\n"
            f"Success Score (Avg):\n"
            f"  Priority: {avg_scores['priority']:.4f}\n"
            f"  Static:   {avg_scores['static']:.4f}\n"
            f"  Greedy:   {avg_scores['greedy']:.4f}\n\n"
            f"Occupants Rescued (Avg):\n"
            f"  Priority: {avg_rescued['priority']:.1f}/17\n"
            f"  Static:   {avg_rescued['static']:.1f}/17\n"
            f"  Greedy:   {avg_rescued['greedy']:.1f}/17\n\n"
            f"Responder Deaths (Avg):\n"
            f"  Priority: {avg_deaths['priority']:.1f}\n"
            f"  Static:   {avg_deaths['static']:.1f}\n"
            f"  Greedy:   {avg_deaths['greedy']:.1f}\n\n"
            f"With fire, priority-based\n"
            f"algorithm considers danger!"
        )
        
        ax6.text(0.5, 0.5, summary_text, transform=ax6.transAxes,
                fontsize=11, verticalalignment='center', horizontalalignment='center',
                bbox=dict(boxstyle='round,pad=1.5', facecolor='#FFEBEE', 
                         edgecolor='#E53935', linewidth=3, alpha=0.95),
                fontfamily='monospace', fontweight='600')
        
        # Overall title
        fig.suptitle('🔥 SWEEP ALGORITHM COMPARISON - WITH FIRE', 
                    fontsize=18, fontweight='bold', y=0.98,
                    bbox=dict(boxstyle='round,pad=0.8', facecolor='#E53935', 
                             edgecolor='none', alpha=1.0),
                    color='white')
        
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        
        # Save
        output_path = Path("benchmark_results")
        output_path.mkdir(exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        filepath = output_path / f"algorithm_comparison_fire_{timestamp}.png"
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        plt.close()
        
        return filepath


def main():
    print("\n" + "="*80)
    print("🔥 ALGORITHM COMPARISON STUDY - WITH FIRE")
    print("Testing how algorithms handle dangerous conditions")
    print("="*80)
    
    comparator = FireAlgorithmComparator()
    responder_counts = [1, 2, 3, 4, 5]
    
    comparator.run_all_comparisons(responder_counts)
    
    # Generate report
    report = comparator.generate_report()
    
    # Save files
    output_path = Path("benchmark_results")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    report_file = output_path / f"algorithm_comparison_fire_{timestamp}.txt"
    with open(report_file, 'w') as f:
        f.write(report)
    
    # Save data
    data_file = output_path / f"algorithm_comparison_fire_data_{timestamp}.json"
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


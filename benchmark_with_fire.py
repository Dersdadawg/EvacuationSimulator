"""
Benchmark Script - With Fire Enabled
Run Multiple Simulations with Fire Hazard

Varies:
- Number of responders (1-5)
- Number of evacuees per room (1-4)

Collects:
- Path taken by each agent
- Total time
- Success rate
- Evacuees rescued
- Rooms cleared
- Agent deaths
- Fire impact
"""

import json
import sys
import time
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Import simulation components
from sim.engine.simulator import Simulator
from sim.env.environment import Environment
from sim.io.layout_loader import LayoutLoader


class FireBenchmarkRunner:
    """Run multiple simulations with fire and collect data"""
    
    def __init__(self, layout_path: str, params_path: str = "params.json"):
        self.layout_path = layout_path
        self.params_path = params_path
        self.results = []
        
    def load_params(self) -> dict:
        """Load base parameters"""
        with open(self.params_path) as f:
            return json.load(f)
    
    def modify_layout_evacuees(self, layout_data: dict, evacuees_per_room: int) -> dict:
        """Modify layout to set evacuees per room"""
        modified = layout_data.copy()
        for room in modified.get('rooms', []):
            # Only modify office rooms (not hallways, exits, stairs)
            if room.get('type') == 'office':
                room['evacuee_count'] = evacuees_per_room
        return modified
    
    def run_single_simulation(self, num_agents: int, evacuees_per_room: int) -> Dict[str, Any]:
        """Run a single simulation with fire and return results"""
        print(f"\n{'='*60}")
        print(f"Running: {num_agents} agents, {evacuees_per_room} evacuees/room 🔥")
        print(f"{'='*60}")
        
        # Load base params
        params = self.load_params()
        params['agents']['count'] = num_agents
        params['visualization']['enabled'] = False  # Disable visualization for speed
        params['hazard']['enabled'] = True  # ENABLE FIRE!
        
        # Load and modify layout
        layout_data = LayoutLoader.load(self.layout_path)
        modified_layout = self.modify_layout_evacuees(layout_data, evacuees_per_room)
        
        # Create environment and simulator
        env = Environment(modified_layout, params)
        sim = Simulator(env, params)
        
        # Track agent paths and deaths
        agent_paths = {i: [] for i in range(num_agents)}
        agent_death_times = {}
        
        # Run simulation
        start_time = time.time()
        max_steps = 10000  # Safety limit
        step_count = 0
        
        while not sim.complete and step_count < max_steps:
            # Record agent positions
            for agent in sim.agent_manager.agents:
                if not agent.is_dead:
                    agent_paths[agent.id].append({
                        'time': sim.time,
                        'x': agent.x,
                        'y': agent.y,
                        'state': agent.state.value,
                        'carrying': agent.carrying_evacuee,
                        'room': agent.current_room
                    })
                elif agent.id not in agent_death_times:
                    agent_death_times[agent.id] = sim.time
            
            sim.step(fire_enabled=True)  # Fire enabled!
            step_count += 1
        
        elapsed_time = time.time() - start_time
        
        # Get results
        results = sim.get_results()
        
        # Calculate path lengths
        path_lengths = {}
        for agent_id, path in agent_paths.items():
            total_distance = 0
            for i in range(1, len(path)):
                dx = path[i]['x'] - path[i-1]['x']
                dy = path[i]['y'] - path[i-1]['y']
                total_distance += np.sqrt(dx**2 + dy**2)
            path_lengths[agent_id] = total_distance
        
        # Count deaths
        num_deaths = sum(1 for a in sim.agent_manager.agents if a.is_dead)
        num_alive = num_agents - num_deaths
        
        # Max hazard level reached
        max_hazard = results.get('max_hazard', 0.0)
        
        # Compile results
        result = {
            'num_agents': num_agents,
            'evacuees_per_room': evacuees_per_room,
            'total_evacuees': results['total_evacuees'],
            'evacuees_rescued': results['evacuees_rescued'],
            'evacuees_trapped': results['total_evacuees'] - results['evacuees_rescued'],
            'rescue_rate': results['evacuees_rescued'] / results['total_evacuees'] if results['total_evacuees'] > 0 else 0,
            'simulation_time': results['time'],
            'real_time': elapsed_time,
            'steps': step_count,
            'success_score': results['success_score'],
            'rooms_cleared': results['rooms_cleared'],
            'total_rooms': results['total_rooms'],
            'agent_deaths': num_deaths,
            'agents_alive': num_alive,
            'agent_survival_rate': num_alive / num_agents,
            'max_hazard': max_hazard,
            'path_lengths': path_lengths,
            'avg_path_length': np.mean(list(path_lengths.values())) if path_lengths else 0,
            'total_distance': sum(path_lengths.values())
        }
        
        print(f"✓ Completed in {results['time']:.1f}s (real: {elapsed_time:.2f}s)")
        print(f"  Rescued: {results['evacuees_rescued']}/{results['total_evacuees']} ({result['rescue_rate']*100:.1f}%)")
        print(f"  🚒 Agent Deaths: {num_deaths}/{num_agents}")
        print(f"  🔥 Max Hazard: {max_hazard*100:.1f}%")
        print(f"  Success Score: {results['success_score']:.4f}")
        
        return result
    
    def run_benchmark(self, agent_counts: List[int], evacuee_counts: List[int], 
                     repetitions: int = 3):
        """Run full benchmark suite with fire"""
        print(f"\n{'='*70}")
        print(f"🔥 FIRE BENCHMARK SUITE 🔥")
        print(f"{'='*70}")
        print(f"Agent counts: {agent_counts}")
        print(f"Evacuees per room: {evacuee_counts}")
        print(f"Repetitions: {repetitions}")
        print(f"Total runs: {len(agent_counts) * len(evacuee_counts) * repetitions}")
        
        for num_agents in agent_counts:
            for evacuees_per_room in evacuee_counts:
                for rep in range(repetitions):
                    print(f"\n[Run {rep+1}/{repetitions}]", end=" ")
                    result = self.run_single_simulation(num_agents, evacuees_per_room)
                    result['repetition'] = rep
                    self.results.append(result)
        
        print(f"\n{'='*70}")
        print(f"🔥 FIRE BENCHMARK COMPLETE - {len(self.results)} runs")
        print(f"{'='*70}")
    
    def save_results(self, output_dir: str = "benchmark_results"):
        """Save results to JSON"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = output_path / f"benchmark_fire_{timestamp}.json"
        
        # Convert results to JSON-serializable format
        results_clean = []
        for r in self.results:
            r_copy = r.copy()
            results_clean.append(r_copy)
        
        with open(filepath, 'w') as f:
            json.dump(results_clean, f, indent=2)
        
        print(f"\n✓ Results saved to: {filepath}")
        return filepath
    
    def plot_results(self, output_dir: str = "benchmark_results"):
        """Generate PERFECT fire benchmark plots with modern styling"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Set modern style
        plt.style.use('seaborn-v0_8-darkgrid')
        
        # Convert results to arrays
        data = {
            'num_agents': [],
            'evacuees_per_room': [],
            'simulation_time': [],
            'rescue_rate': [],
            'success_score': [],
            'agent_deaths': [],
            'agent_survival_rate': [],
            'max_hazard': [],
            'evacuees_trapped': []
        }
        
        for r in self.results:
            data['num_agents'].append(r['num_agents'])
            data['evacuees_per_room'].append(r['evacuees_per_room'])
            data['simulation_time'].append(r['simulation_time'])
            data['rescue_rate'].append(r['rescue_rate'])
            data['success_score'].append(r['success_score'])
            data['agent_deaths'].append(r['agent_deaths'])
            data['agent_survival_rate'].append(r['agent_survival_rate'])
            data['max_hazard'].append(r['max_hazard'])
            data['evacuees_trapped'].append(r['evacuees_trapped'])
        
        # Create figure with large, clear subplots
        fig = plt.figure(figsize=(24, 16), facecolor='white')
        fig.suptitle('🔥 FIRE EVACUATION BENCHMARK ANALYSIS 🔥', 
                    fontsize=28, fontweight='bold', y=0.995, color='#D32F2F')
        
        # 1. Rescue Rate vs Number of Agents (WITH FIRE) - TOP PRIORITY
        ax1 = plt.subplot(3, 3, 1)
        self._plot_by_agents(ax1, data, 'rescue_rate', 'Rescue Rate (%)', 
                           '🔥 RESCUE SUCCESS RATE', percentage=True, 
                           color_scheme='fire_success')
        
        # 2. Agent Survival Rate vs Number of Agents - CRITICAL
        ax2 = plt.subplot(3, 3, 2)
        self._plot_by_agents(ax2, data, 'agent_survival_rate', 'Survival Rate (%)', 
                           '🚒 RESPONDER SURVIVAL RATE', percentage=True,
                           color_scheme='agent_safety')
        
        # 3. Success Score vs Number of Agents - KEY METRIC
        ax3 = plt.subplot(3, 3, 3)
        self._plot_by_agents(ax3, data, 'success_score', 'Success Score', 
                           '📊 OVERALL SUCCESS SCORE',
                           color_scheme='success')
        
        # 4. Simulation Time vs Number of Agents
        ax4 = plt.subplot(3, 3, 4)
        self._plot_by_agents(ax4, data, 'simulation_time', 'Time (seconds)', 
                           '⏱️  EVACUATION TIME',
                           color_scheme='time')
        
        # 5. Agent Deaths vs Number of Agents
        ax5 = plt.subplot(3, 3, 5)
        self._plot_by_agents(ax5, data, 'agent_deaths', 'Deaths (count)', 
                           '💀 RESPONDER CASUALTIES',
                           color_scheme='danger')
        
        # 6. Evacuees Trapped vs Number of Agents
        ax6 = plt.subplot(3, 3, 6)
        self._plot_by_agents(ax6, data, 'evacuees_trapped', 'Trapped (count)', 
                           '😢 OCCUPANTS TRAPPED',
                           color_scheme='danger')
        
        # 7. HEATMAP: Rescue Rate
        ax7 = plt.subplot(3, 3, 7)
        self._plot_heatmap(ax7, data, 'rescue_rate', '🎯 RESCUE RATE HEATMAP (%)', 
                          percentage=True, cmap='RdYlGn')
        
        # 8. HEATMAP: Agent Survival
        ax8 = plt.subplot(3, 3, 8)
        self._plot_heatmap(ax8, data, 'agent_survival_rate', '🛡️ RESPONDER SURVIVAL HEATMAP (%)', 
                          percentage=True, cmap='RdYlGn')
        
        # 9. HEATMAP: Success Score
        ax9 = plt.subplot(3, 3, 9)
        self._plot_heatmap(ax9, data, 'success_score', '⭐ SUCCESS SCORE HEATMAP',
                          cmap='plasma')
        
        plt.tight_layout(rect=[0, 0, 1, 0.99])
        
        # Save figure at HIGH RESOLUTION
        filepath = output_path / f"benchmark_fire_plots_{timestamp}.png"
        plt.savefig(filepath, dpi=300, bbox_inches='tight', facecolor='white')
        print(f"✓ PERFECT plots saved to: {filepath}")
        
        # Don't show plot (prevents blocking)
        plt.close()
    
    def _plot_by_agents(self, ax, data, metric, ylabel, title, percentage=False, color_scheme='default'):
        """Plot metric vs number of agents with PERFECT modern styling"""
        unique_evacuees = sorted(set(data['evacuees_per_room']))
        
        # Choose color scheme based on metric
        if color_scheme == 'fire_success':
            # Green to red gradient (green = good, red = bad for rescue)
            colors = ['#2E7D32', '#66BB6A', '#FFA726', '#EF5350']
        elif color_scheme == 'agent_safety':
            # Blue gradient for agent safety
            colors = ['#1565C0', '#42A5F5', '#64B5F6', '#90CAF9']
        elif color_scheme == 'success':
            # Orange gradient for success
            colors = ['#E65100', '#F57C00', '#FF9800', '#FFB74D']
        elif color_scheme == 'time':
            # Purple gradient for time
            colors = ['#4A148C', '#7B1FA2', '#9C27B0', '#BA68C8']
        elif color_scheme == 'danger':
            # Red gradient for danger/deaths
            colors = ['#B71C1C', '#D32F2F', '#E57373', '#EF9A9A']
        else:
            colors = plt.cm.viridis(np.linspace(0, 1, len(unique_evacuees)))
        
        # Ensure we have enough colors
        if len(colors) < len(unique_evacuees):
            colors = plt.cm.viridis(np.linspace(0, 1, len(unique_evacuees)))
        
        for i, evac_count in enumerate(unique_evacuees):
            color = colors[i]
            mask = [e == evac_count for e in data['evacuees_per_room']]
            agents = [data['num_agents'][i] for i in range(len(mask)) if mask[i]]
            values = [data[metric][i] for i in range(len(mask)) if mask[i]]
            
            if percentage:
                values = [v * 100 for v in values]
            
            # Group by agent count and calculate mean/std
            agent_unique = sorted(set(agents))
            means = []
            stds = []
            for a in agent_unique:
                vals = [values[i] for i in range(len(agents)) if agents[i] == a]
                means.append(np.mean(vals))
                stds.append(np.std(vals))
            
            # Plot with thick lines and large markers
            ax.errorbar(agent_unique, means, yerr=stds, marker='o', 
                       label=f'{evac_count} occupants/room', color=color, 
                       linewidth=3.5, markersize=12, capsize=6, capthick=2.5,
                       elinewidth=2.5, alpha=0.9)
        
        # Enhanced styling
        ax.set_xlabel('Number of Responders', fontsize=14, fontweight='bold')
        ax.set_ylabel(ylabel, fontsize=14, fontweight='bold')
        ax.set_title(title, fontsize=16, fontweight='bold', pad=15, color='#1A1A1A')
        ax.legend(fontsize=11, framealpha=0.95, loc='best', edgecolor='black', fancybox=True)
        ax.grid(True, alpha=0.4, linestyle='--', linewidth=1.2)
        ax.tick_params(labelsize=12)
        
        # Set background
        ax.set_facecolor('#F8F8F8')
        
        # Add value labels on points for clarity
        for i, evac_count in enumerate(unique_evacuees):
            mask = [e == evac_count for e in data['evacuees_per_room']]
            agents = [data['num_agents'][j] for j in range(len(mask)) if mask[j]]
            values = [data[metric][j] for j in range(len(mask)) if mask[j]]
            
            if percentage:
                values = [v * 100 for v in values]
            
            agent_unique = sorted(set(agents))
            for a in agent_unique:
                vals = [values[j] for j in range(len(agents)) if agents[j] == a]
                mean_val = np.mean(vals)
                # Only label every other point to avoid clutter
                if a % 2 == 1 or len(agent_unique) <= 3:
                    ax.text(a, mean_val, f'{mean_val:.1f}', 
                           ha='center', va='bottom', fontsize=9, fontweight='bold',
                           bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.7, edgecolor='none'))
    
    def _plot_heatmap(self, ax, data, metric, title, percentage=False, cmap='YlOrRd'):
        """Plot PERFECT heatmap with clear annotations"""
        unique_agents = sorted(set(data['num_agents']))
        unique_evacuees = sorted(set(data['evacuees_per_room']))
        
        # Create matrix
        matrix = np.zeros((len(unique_evacuees), len(unique_agents)))
        
        for i, evac in enumerate(unique_evacuees):
            for j, agent in enumerate(unique_agents):
                mask = [(data['num_agents'][k] == agent and 
                        data['evacuees_per_room'][k] == evac) 
                       for k in range(len(data['num_agents']))]
                values = [data[metric][k] for k in range(len(mask)) if mask[k]]
                if percentage:
                    values = [v * 100 for v in values]
                matrix[i, j] = np.mean(values) if values else 0
        
        # Plot with enhanced styling
        im = ax.imshow(matrix, cmap=cmap, aspect='auto', interpolation='nearest')
        
        # Set ticks and labels
        ax.set_xticks(range(len(unique_agents)))
        ax.set_yticks(range(len(unique_evacuees)))
        ax.set_xticklabels(unique_agents, fontsize=12, fontweight='bold')
        ax.set_yticklabels(unique_evacuees, fontsize=12, fontweight='bold')
        ax.set_xlabel('Number of Responders', fontsize=14, fontweight='bold')
        ax.set_ylabel('Occupants per Room', fontsize=14, fontweight='bold')
        ax.set_title(title, fontsize=16, fontweight='bold', pad=15, color='#1A1A1A')
        
        # Add LARGE, CLEAR colorbar
        cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.ax.tick_params(labelsize=11)
        
        # Add BOLD text annotations with contrasting colors
        for i in range(len(unique_evacuees)):
            for j in range(len(unique_agents)):
                val = matrix[i, j]
                # Choose text color based on value for readability
                text_color = 'white' if val < (matrix.max() * 0.6) else 'black'
                ax.text(j, i, f'{val:.1f}',
                       ha="center", va="center", color=text_color, 
                       fontsize=13, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.4', facecolor='none', 
                                edgecolor=text_color, linewidth=1.5, alpha=0.6))


def main():
    """Main benchmark execution"""
    # Configuration - FAST MODE for perfect graphs in under 2 minutes
    layout_path = "layouts/office_correct_dimensions.json"
    agent_counts = [1, 2, 3, 4, 5]
    evacuee_counts = [1, 2, 3, 4]
    repetitions = 2  # Reduced from 3 for speed
    
    # Run benchmark with fire
    runner = FireBenchmarkRunner(layout_path)
    runner.run_benchmark(agent_counts, evacuee_counts, repetitions)
    
    # Save and plot
    runner.save_results()
    runner.plot_results()


if __name__ == "__main__":
    main()


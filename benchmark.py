"""
Benchmark Script - Run Multiple Simulations and Collect Data

Varies:
- Number of responders (1-5)
- Number of evacuees per room (1-4)

Collects:
- Path taken by each agent
- Total time
- Success rate
- Evacuees rescued
- Rooms cleared
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


class BenchmarkRunner:
    """Run multiple simulations and collect data"""
    
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
        """Run a single simulation and return results"""
        print(f"\n{'='*60}")
        print(f"Running: {num_agents} agents, {evacuees_per_room} evacuees/room")
        print(f"{'='*60}")
        
        # Load base params
        params = self.load_params()
        params['agents']['count'] = num_agents
        params['visualization']['enabled'] = False  # Disable visualization for speed
        
        # Load and modify layout
        layout_data = LayoutLoader.load(self.layout_path)
        modified_layout = self.modify_layout_evacuees(layout_data, evacuees_per_room)
        
        # Create environment and simulator
        env = Environment(modified_layout, params)
        sim = Simulator(env, params)
        
        # Track agent paths
        agent_paths = {i: [] for i in range(num_agents)}
        
        # Run simulation
        start_time = time.time()
        max_steps = 10000  # Safety limit
        step_count = 0
        
        while not sim.complete and step_count < max_steps:
            # Record agent positions
            for agent in sim.agent_manager.agents:
                agent_paths[agent.id].append({
                    'time': sim.time,
                    'x': agent.x,
                    'y': agent.y,
                    'state': agent.state.value,
                    'carrying': agent.carrying_evacuee,
                    'room': agent.current_room
                })
            
            sim.step(fire_enabled=False)  # No fire for benchmark
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
        
        # Compile results
        result = {
            'num_agents': num_agents,
            'evacuees_per_room': evacuees_per_room,
            'total_evacuees': results['total_evacuees'],
            'evacuees_rescued': results['evacuees_rescued'],
            'rescue_rate': results['evacuees_rescued'] / results['total_evacuees'] if results['total_evacuees'] > 0 else 0,
            'simulation_time': results['time'],
            'real_time': elapsed_time,
            'steps': step_count,
            'success_score': results['success_score'],
            'rooms_cleared': results['rooms_cleared'],
            'total_rooms': results['total_rooms'],
            'agent_paths': agent_paths,
            'path_lengths': path_lengths,
            'avg_path_length': np.mean(list(path_lengths.values())),
            'total_distance': sum(path_lengths.values())
        }
        
        print(f"✓ Completed in {results['time']:.1f}s (real: {elapsed_time:.2f}s)")
        print(f"  Rescued: {results['evacuees_rescued']}/{results['total_evacuees']} ({result['rescue_rate']*100:.1f}%)")
        print(f"  Success Score: {results['success_score']:.4f}")
        print(f"  Avg Path Length: {result['avg_path_length']:.1f}m")
        
        return result
    
    def run_benchmark(self, agent_counts: List[int], evacuee_counts: List[int], 
                     repetitions: int = 3):
        """Run full benchmark suite"""
        print(f"\n{'='*70}")
        print(f"BENCHMARK SUITE")
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
        print(f"BENCHMARK COMPLETE - {len(self.results)} runs")
        print(f"{'='*70}")
    
    def save_results(self, output_dir: str = "benchmark_results"):
        """Save results to JSON"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = output_path / f"benchmark_{timestamp}.json"
        
        # Convert results to JSON-serializable format (remove agent_paths for size)
        results_clean = []
        for r in self.results:
            r_copy = r.copy()
            r_copy.pop('agent_paths', None)  # Too large for JSON
            results_clean.append(r_copy)
        
        with open(filepath, 'w') as f:
            json.dump(results_clean, f, indent=2)
        
        print(f"\n✓ Results saved to: {filepath}")
        return filepath
    
    def plot_results(self, output_dir: str = "benchmark_results"):
        """Generate plots from results"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Convert results to arrays
        data = {
            'num_agents': [],
            'evacuees_per_room': [],
            'simulation_time': [],
            'rescue_rate': [],
            'success_score': [],
            'avg_path_length': [],
            'total_distance': []
        }
        
        for r in self.results:
            data['num_agents'].append(r['num_agents'])
            data['evacuees_per_room'].append(r['evacuees_per_room'])
            data['simulation_time'].append(r['simulation_time'])
            data['rescue_rate'].append(r['rescue_rate'])
            data['success_score'].append(r['success_score'])
            data['avg_path_length'].append(r['avg_path_length'])
            data['total_distance'].append(r['total_distance'])
        
        # Create figure with multiple subplots
        fig = plt.figure(figsize=(18, 12))
        
        # 1. Simulation Time vs Number of Agents
        ax1 = plt.subplot(2, 3, 1)
        self._plot_by_agents(ax1, data, 'simulation_time', 'Simulation Time (s)', 
                           'Simulation Time vs Number of Agents')
        
        # 2. Rescue Rate vs Number of Agents
        ax2 = plt.subplot(2, 3, 2)
        self._plot_by_agents(ax2, data, 'rescue_rate', 'Rescue Rate (%)', 
                           'Rescue Rate vs Number of Agents', percentage=True)
        
        # 3. Success Score vs Number of Agents
        ax3 = plt.subplot(2, 3, 3)
        self._plot_by_agents(ax3, data, 'success_score', 'Success Score', 
                           'Success Score vs Number of Agents')
        
        # 4. Average Path Length vs Number of Agents
        ax4 = plt.subplot(2, 3, 4)
        self._plot_by_agents(ax4, data, 'avg_path_length', 'Avg Path Length (m)', 
                           'Avg Path Length vs Number of Agents')
        
        # 5. Simulation Time vs Evacuees per Room
        ax5 = plt.subplot(2, 3, 5)
        self._plot_by_evacuees(ax5, data, 'simulation_time', 'Simulation Time (s)', 
                              'Simulation Time vs Evacuees/Room')
        
        # 6. Total Distance vs Configuration
        ax6 = plt.subplot(2, 3, 6)
        self._plot_heatmap(ax6, data)
        
        plt.tight_layout()
        
        # Save figure
        filepath = output_path / f"benchmark_plots_{timestamp}.png"
        plt.savefig(filepath, dpi=150, bbox_inches='tight')
        print(f"✓ Plots saved to: {filepath}")
        
        # Don't show plot (prevents blocking)
        plt.close()
    
    def _plot_by_agents(self, ax, data, metric, ylabel, title, percentage=False):
        """Plot metric vs number of agents, grouped by evacuees"""
        unique_evacuees = sorted(set(data['evacuees_per_room']))
        colors = plt.cm.viridis(np.linspace(0, 1, len(unique_evacuees)))
        
        for evac_count, color in zip(unique_evacuees, colors):
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
            
            ax.errorbar(agent_unique, means, yerr=stds, marker='o', 
                       label=f'{evac_count} evacuees/room', color=color, 
                       linewidth=2, markersize=8, capsize=5)
        
        ax.set_xlabel('Number of Agents', fontweight='bold')
        ax.set_ylabel(ylabel, fontweight='bold')
        ax.set_title(title, fontweight='bold', fontsize=12)
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_by_evacuees(self, ax, data, metric, ylabel, title):
        """Plot metric vs evacuees per room, grouped by agents"""
        unique_agents = sorted(set(data['num_agents']))
        colors = plt.cm.plasma(np.linspace(0, 1, len(unique_agents)))
        
        for agent_count, color in zip(unique_agents, colors):
            mask = [a == agent_count for a in data['num_agents']]
            evacuees = [data['evacuees_per_room'][i] for i in range(len(mask)) if mask[i]]
            values = [data[metric][i] for i in range(len(mask)) if mask[i]]
            
            # Group by evacuee count and calculate mean/std
            evac_unique = sorted(set(evacuees))
            means = []
            stds = []
            for e in evac_unique:
                vals = [values[i] for i in range(len(evacuees)) if evacuees[i] == e]
                means.append(np.mean(vals))
                stds.append(np.std(vals))
            
            ax.errorbar(evac_unique, means, yerr=stds, marker='s', 
                       label=f'{agent_count} agents', color=color, 
                       linewidth=2, markersize=8, capsize=5)
        
        ax.set_xlabel('Evacuees per Room', fontweight='bold')
        ax.set_ylabel(ylabel, fontweight='bold')
        ax.set_title(title, fontweight='bold', fontsize=12)
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_heatmap(self, ax, data):
        """Plot heatmap of total distance traveled"""
        unique_agents = sorted(set(data['num_agents']))
        unique_evacuees = sorted(set(data['evacuees_per_room']))
        
        # Create matrix
        matrix = np.zeros((len(unique_evacuees), len(unique_agents)))
        
        for i, evac in enumerate(unique_evacuees):
            for j, agent in enumerate(unique_agents):
                mask = [(data['num_agents'][k] == agent and 
                        data['evacuees_per_room'][k] == evac) 
                       for k in range(len(data['num_agents']))]
                values = [data['total_distance'][k] for k in range(len(mask)) if mask[k]]
                matrix[i, j] = np.mean(values) if values else 0
        
        im = ax.imshow(matrix, cmap='YlOrRd', aspect='auto')
        ax.set_xticks(range(len(unique_agents)))
        ax.set_yticks(range(len(unique_evacuees)))
        ax.set_xticklabels(unique_agents)
        ax.set_yticklabels(unique_evacuees)
        ax.set_xlabel('Number of Agents', fontweight='bold')
        ax.set_ylabel('Evacuees per Room', fontweight='bold')
        ax.set_title('Total Distance Traveled (m)', fontweight='bold', fontsize=12)
        
        # Add colorbar
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('Distance (m)', rotation=270, labelpad=20)
        
        # Add text annotations
        for i in range(len(unique_evacuees)):
            for j in range(len(unique_agents)):
                text = ax.text(j, i, f'{matrix[i, j]:.0f}',
                             ha="center", va="center", color="black", fontsize=10)


def main():
    """Main benchmark execution"""
    # Configuration
    layout_path = "layouts/office_correct_dimensions.json"
    agent_counts = [1, 2, 3, 4, 5]
    evacuee_counts = [1, 2, 3, 4]
    repetitions = 3
    
    # Run benchmark
    runner = BenchmarkRunner(layout_path)
    runner.run_benchmark(agent_counts, evacuee_counts, repetitions)
    
    # Save and plot
    runner.save_results()
    runner.plot_results()


if __name__ == "__main__":
    main()


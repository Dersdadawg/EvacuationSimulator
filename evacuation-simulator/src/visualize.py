"""
Visualize module: Matplotlib-based visualization for debugging
"""

import matplotlib.pyplot as plt
import matplotlib.patches as patches
import matplotlib.animation as animation
import numpy as np
from typing import List, Dict
from src.environment import CellState


class Visualizer:
    """Matplotlib visualizer for simulation"""
    
    # Color scheme
    COLORS = {
        CellState.WALL: '#000000',       # Black
        CellState.SAFE: '#FFFFFF',       # White
        CellState.EXIT: '#00FF00',       # Green
        CellState.DANGER: '#FF0000',     # Red
        'responder': '#0000FF',          # Blue
        'evacuee': '#FFFF00',            # Yellow
        'evacuee_rescued': '#FFA500',    # Orange
        'evacuee_evacuated': '#00FF00',  # Green
    }
    
    def __init__(self, figsize=(12, 10)):
        self.fig, self.ax = plt.subplots(figsize=figsize)
        self.cell_size = 1.0
    
    def draw_frame(self, frame_data: Dict, show_paths: bool = False):
        """
        Draw a single frame
        
        Args:
            frame_data: Frame dictionary with grid, agents, etc.
            show_paths: Whether to show agent path trails
        """
        self.ax.clear()
        
        grid = np.array(frame_data['grid'])
        height, width = grid.shape
        
        # Draw grid cells
        for y in range(height):
            for x in range(width):
                cell_state = CellState(grid[y, x])
                color = self.COLORS.get(cell_state, '#CCCCCC')
                
                rect = patches.Rectangle(
                    (x, height - y - 1), 1, 1,
                    facecolor=color,
                    edgecolor='#DDDDDD',
                    linewidth=0.5
                )
                self.ax.add_patch(rect)
        
        # Draw evacuees
        for evacuee in frame_data['evacuees']:
            if evacuee['evacuated']:
                color = self.COLORS['evacuee_evacuated']
                alpha = 0.3
            elif evacuee['rescued']:
                color = self.COLORS['evacuee_rescued']
                alpha = 0.8
            else:
                color = self.COLORS['evacuee']
                alpha = 1.0
            
            if evacuee['active'] or evacuee['evacuated']:
                circle = patches.Circle(
                    (evacuee['x'] + 0.5, height - evacuee['y'] - 0.5),
                    0.3,
                    facecolor=color,
                    alpha=alpha,
                    edgecolor='black',
                    linewidth=1
                )
                self.ax.add_patch(circle)
        
        # Draw responders
        for responder in frame_data['responders']:
            if responder['active']:
                square = patches.Rectangle(
                    (responder['x'] + 0.2, height - responder['y'] - 0.8),
                    0.6, 0.6,
                    facecolor=self.COLORS['responder'],
                    edgecolor='white',
                    linewidth=2
                )
                self.ax.add_patch(square)
                
                # Show rescue count
                self.ax.text(
                    responder['x'] + 0.5,
                    height - responder['y'] - 0.5,
                    str(responder['rescued_count']),
                    ha='center',
                    va='center',
                    color='white',
                    fontsize=8,
                    fontweight='bold'
                )
        
        # Set axis properties
        self.ax.set_xlim(0, width)
        self.ax.set_ylim(0, height)
        self.ax.set_aspect('equal')
        self.ax.set_title(f"Timestep: {frame_data['timestep']}", fontsize=14, fontweight='bold')
        self.ax.set_xlabel('X')
        self.ax.set_ylabel('Y')
        
        # Add legend
        legend_elements = [
            patches.Patch(facecolor=self.COLORS[CellState.WALL], label='Wall'),
            patches.Patch(facecolor=self.COLORS[CellState.EXIT], label='Exit'),
            patches.Patch(facecolor=self.COLORS[CellState.DANGER], label='Danger'),
            patches.Patch(facecolor=self.COLORS['responder'], label='Responder'),
            patches.Patch(facecolor=self.COLORS['evacuee'], label='Evacuee'),
            patches.Patch(facecolor=self.COLORS['evacuee_rescued'], label='Rescued'),
        ]
        self.ax.legend(handles=legend_elements, loc='upper right', fontsize=9)
        
        plt.tight_layout()
    
    def show_frame(self, frame_data: Dict):
        """Display a single frame"""
        self.draw_frame(frame_data)
        plt.show()
    
    def animate_simulation(self, history: List[Dict], interval: int = 100, 
                          save_path: str = None):
        """
        Create animation from simulation history
        
        Args:
            history: List of frame dictionaries
            interval: Milliseconds between frames
            save_path: If provided, save animation to this path (e.g., 'output.mp4')
        """
        def update(frame_idx):
            self.draw_frame(history[frame_idx])
            return self.ax.patches
        
        anim = animation.FuncAnimation(
            self.fig,
            update,
            frames=len(history),
            interval=interval,
            blit=False,
            repeat=True
        )
        
        if save_path:
            print(f"Saving animation to {save_path}...")
            anim.save(save_path, writer='pillow', fps=10)
            print(f"Animation saved!")
        else:
            plt.show()
        
        return anim
    
    def plot_metrics(self, history: List[Dict], metrics: Dict):
        """
        Plot metrics over time
        
        Args:
            history: List of frame dictionaries
            metrics: Final metrics dictionary
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        timesteps = [frame['timestep'] for frame in history]
        
        # Plot 1: Active vs Evacuated count
        active_counts = []
        evacuated_counts = []
        
        for frame in history:
            active = sum(1 for e in frame['evacuees'] if e['active'] and not e['evacuated'])
            evacuated = sum(1 for e in frame['evacuees'] if e['evacuated'])
            active_counts.append(active)
            evacuated_counts.append(evacuated)
        
        axes[0, 0].plot(timesteps, active_counts, label='Active Evacuees', color='orange')
        axes[0, 0].plot(timesteps, evacuated_counts, label='Evacuated', color='green')
        axes[0, 0].set_xlabel('Timestep')
        axes[0, 0].set_ylabel('Count')
        axes[0, 0].set_title('Evacuee Status Over Time')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # Plot 2: Danger cell count (hazard spread)
        danger_counts = [len(frame['danger_cells']) for frame in history]
        axes[0, 1].plot(timesteps, danger_counts, color='red', linewidth=2)
        axes[0, 1].set_xlabel('Timestep')
        axes[0, 1].set_ylabel('Danger Cells')
        axes[0, 1].set_title('Hazard Spread Over Time')
        axes[0, 1].grid(True, alpha=0.3)
        
        # Plot 3: Rescues over time
        rescue_counts = []
        for frame in history:
            total_rescued = sum(r['rescued_count'] for r in frame['responders'])
            rescue_counts.append(total_rescued)
        
        axes[1, 0].plot(timesteps, rescue_counts, color='blue', linewidth=2)
        axes[1, 0].set_xlabel('Timestep')
        axes[1, 0].set_ylabel('Total Rescues')
        axes[1, 0].set_title('Cumulative Rescues by Responders')
        axes[1, 0].grid(True, alpha=0.3)
        
        # Plot 4: Final metrics bar chart
        metric_names = ['Evacuated', 'Rescued', 'Stuck']
        metric_values = [
            metrics.get('evacuated_count', 0),
            metrics.get('rescued_count', 0),
            metrics.get('stuck_count', 0)
        ]
        colors = ['green', 'orange', 'red']
        
        axes[1, 1].bar(metric_names, metric_values, color=colors, alpha=0.7)
        axes[1, 1].set_ylabel('Count')
        axes[1, 1].set_title('Final Outcome Summary')
        axes[1, 1].grid(True, alpha=0.3, axis='y')
        
        # Add text annotations
        for i, v in enumerate(metric_values):
            axes[1, 1].text(i, v + 0.5, str(v), ha='center', fontweight='bold')
        
        plt.tight_layout()
        plt.show()


def quick_visualize(history: List[Dict], metrics: Dict, show_animation: bool = True,
                   show_metrics: bool = True):
    """
    Quick visualization of simulation results
    
    Args:
        history: Simulation history
        metrics: Simulation metrics
        show_animation: Whether to show animation
        show_metrics: Whether to show metrics plots
    """
    viz = Visualizer()
    
    if show_animation and history:
        print("Creating animation...")
        viz.animate_simulation(history, interval=50)
    
    if show_metrics:
        print("Plotting metrics...")
        viz.plot_metrics(history, metrics)


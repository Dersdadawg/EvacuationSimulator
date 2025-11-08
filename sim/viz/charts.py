"""Chart generation for simulation analysis"""

import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from pathlib import Path
from typing import List
import pandas as pd

from ..engine.simulator import SimulationEvent, EventType


class ChartGenerator:
    """Generates summary charts from simulation data"""
    
    def __init__(self, output_dir: str):
        """
        Initialize chart generator
        
        Args:
            output_dir: Directory to save charts
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def generate_summary_charts(self, events: List[SimulationEvent], 
                               results: dict, filename: str = "summary.png"):
        """
        Generate comprehensive summary chart
        
        Args:
            events: List of simulation events
            results: Results dictionary
            filename: Output filename
        """
        # Create figure with subplots
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        fig.suptitle('Simulation Summary', fontsize=16, fontweight='bold')
        
        # Convert events to DataFrame
        df = self._events_to_dataframe(events)
        
        # 1. Cumulative rooms cleared over time
        ax1 = axes[0, 0]
        cleared_events = df[df['event_type'] == 'room_cleared']
        if not cleared_events.empty:
            cleared_times = cleared_events['time'].values
            cleared_counts = range(1, len(cleared_times) + 1)
            ax1.plot(cleared_times, cleared_counts, 'g-', linewidth=2, label='Rooms Cleared')
            ax1.axhline(y=results['total_rooms'], color='gray', linestyle='--', 
                       label='Total Rooms')
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Cumulative Rooms Cleared')
        ax1.set_title('Room Clearance Progress')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # 2. Cumulative evacuees rescued over time
        ax2 = axes[0, 1]
        rescued_events = df[df['event_type'] == 'evacuee_rescued']
        if not rescued_events.empty:
            rescued_times = rescued_events['time'].values
            rescued_counts = range(1, len(rescued_times) + 1)
            ax2.plot(rescued_times, rescued_counts, 'r-', linewidth=2, label='Rescued')
            ax2.axhline(y=results['total_evacuees'], color='gray', linestyle='--',
                       label='Total Evacuees')
        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Cumulative Evacuees Rescued')
        ax2.set_title('Rescue Progress')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. Agent activity timeline
        ax3 = axes[1, 0]
        agent_events = df[df['agent_id'].notna()]
        if not agent_events.empty:
            for agent_id in agent_events['agent_id'].unique():
                agent_df = agent_events[agent_events['agent_id'] == agent_id]
                event_types = agent_df['event_type'].values
                times = agent_df['time'].values
                
                # Count events by type over time bins
                bins = range(0, int(max(times)) + 10, 10)
                hist, _ = pd.cut(times, bins=bins, retbins=True)
                
            # Simplified: show event counts per agent
            event_counts = agent_events.groupby('agent_id').size()
            ax3.bar(event_counts.index, event_counts.values, color='steelblue')
            ax3.set_xlabel('Agent ID')
            ax3.set_ylabel('Total Events')
            ax3.set_title('Agent Activity')
            ax3.grid(True, alpha=0.3, axis='y')
        
        # 4. Performance metrics
        ax4 = axes[1, 1]
        metrics = {
            'Rescue %': results['percent_rescued'],
            'Clear %': results['percent_cleared'],
            'Success\nScore': results['success_score'] * 100
        }
        
        colors = ['#ff6b6b', '#4ecdc4', '#45b7d1']
        bars = ax4.bar(metrics.keys(), metrics.values(), color=colors, alpha=0.7)
        ax4.set_ylabel('Percentage / Score')
        ax4.set_title('Final Metrics')
        ax4.set_ylim(0, 105)
        ax4.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}', ha='center', va='bottom')
        
        plt.tight_layout()
        
        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"Summary charts saved to {output_path}")
    
    def generate_hazard_heatmap(self, env, filename: str = "hazard_final.png"):
        """
        Generate final hazard distribution heatmap
        
        Args:
            env: Environment with final hazard state
            filename: Output filename
        """
        fig, axes = plt.subplots(1, len(env.floors), figsize=(6 * len(env.floors), 5))
        
        if len(env.floors) == 1:
            axes = [axes]
        
        fig.suptitle('Final Hazard Distribution by Floor', fontsize=14, fontweight='bold')
        
        for idx, (floor, room_ids) in enumerate(sorted(env.floors.items())):
            ax = axes[idx]
            
            # Get room positions and hazards
            rooms = [env.rooms[rid] for rid in room_ids]
            
            for room in rooms:
                x1, y1 = room.x1, room.y1
                w, h = room.width, room.height
                
                # Color by hazard level
                color = plt.cm.YlOrRd(room.hazard)
                rect = plt.Rectangle((x1, y1), w, h, facecolor=color, 
                                   edgecolor='black', linewidth=0.5)
                ax.add_patch(rect)
                
                # Add label
                if w > 10 and h > 10:
                    ax.text(room.x, room.y, f"{room.hazard:.2f}", 
                           ha='center', va='center', fontsize=8)
            
            ax.set_aspect('equal')
            ax.set_title(f'Floor {floor + 1}')
            ax.set_xlabel('X (m)')
            ax.set_ylabel('Y (m)')
            ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        output_path = self.output_dir / filename
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()
        
        print(f"Hazard heatmap saved to {output_path}")
    
    def _events_to_dataframe(self, events: List[SimulationEvent]) -> pd.DataFrame:
        """Convert events list to pandas DataFrame"""
        data = []
        for event in events:
            row = {
                'tick': event.tick,
                'time': event.time,
                'event_type': event.event_type.value,
                'agent_id': event.agent_id,
                'room_id': event.room_id
            }
            row.update(event.data)
            data.append(row)
        
        return pd.DataFrame(data)


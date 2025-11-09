"""Simulation logger for CSV exports"""

import csv
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from ..engine.simulator import SimulationEvent


class SimulationLogger:
    """Logs simulation data to CSV files"""
    
    def __init__(self, output_dir: str = None):
        """
        Initialize logger
        
        Args:
            output_dir: Output directory (auto-generated if None)
        """
        if output_dir is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_dir = f"outputs/run_{timestamp}"
        
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.events: List[SimulationEvent] = []
    
    def log_event(self, event: SimulationEvent):
        """Add event to log"""
        self.events.append(event)
    
    def save_results(self, results: Dict[str, Any]):
        """
        Save summary results to CSV
        
        Args:
            results: Results dictionary from simulator
        """
        results_file = self.output_dir / 'results.csv'
        
        # Flatten results for CSV
        row = {
            'timestamp': datetime.now().isoformat(),
            'time_elapsed': results['time'],
            'ticks': results['ticks'],
            'total_evacuees': results['total_evacuees'],
            'evacuees_rescued': results['evacuees_rescued'],
            'percent_rescued': results['percent_rescued'],
            'total_rooms': results['total_rooms'],
            'rooms_cleared': results['rooms_cleared'],
            'percent_cleared': results['percent_cleared'],
            'success_score': results['success_score'],
            'avg_hazard_exposure': results['avg_hazard_exposure'],
            'max_hazard': results['max_hazard']
        }
        
        # Write header if new file
        file_exists = results_file.exists()
        
        with open(results_file, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=row.keys())
            if not file_exists:
                writer.writeheader()
            writer.writerow(row)
        
        print(f"Results saved to {results_file}")
    
    def save_timeline(self):
        """Save event timeline to CSV"""
        timeline_file = self.output_dir / 'timeline.csv'
        
        with open(timeline_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['tick', 'time', 'event_type', 'agent_id', 
                           'room_id', 'data'])
            
            for event in self.events:
                writer.writerow([
                    event.tick,
                    f"{event.time:.1f}",
                    event.event_type.value,
                    event.agent_id if event.agent_id is not None else '',
                    event.room_id if event.room_id else '',
                    str(event.data)
                ])
        
        print(f"Timeline saved to {timeline_file}")
    
    def save_agent_stats(self, agent_stats: List[Dict[str, Any]]):
        """
        Save per-agent statistics
        
        Args:
            agent_stats: List of agent stat dictionaries
        """
        stats_file = self.output_dir / 'agent_stats.csv'
        
        if not agent_stats:
            return
        
        df = pd.DataFrame(agent_stats)
        df.to_csv(stats_file, index=False)
        
        print(f"Agent stats saved to {stats_file}")
    
    def create_timeline_dataframe(self) -> pd.DataFrame:
        """
        Create pandas DataFrame from event timeline
        
        Returns:
            Timeline DataFrame
        """
        data = []
        for event in self.events:
            data.append({
                'tick': event.tick,
                'time': event.time,
                'event_type': event.event_type.value,
                'agent_id': event.agent_id,
                'room_id': event.room_id,
                **event.data
            })
        
        return pd.DataFrame(data)
    
    def get_output_path(self, filename: str) -> Path:
        """Get full path for output file"""
        return self.output_dir / filename
    
    def print_summary(self, results: Dict[str, Any]):
        """Print results summary to console"""
        print("\n" + "="*60)
        print("SIMULATION RESULTS")
        print("="*60)
        print(f"Time Elapsed:        {results['time']:.1f} seconds ({results['ticks']} ticks)")
        print(f"Evacuees Rescued:    {results['evacuees_rescued']}/{results['total_evacuees']} "
              f"({results['percent_rescued']:.1f}%)")
        print(f"Rooms Cleared:       {results['rooms_cleared']}/{results['total_rooms']} "
              f"({results['percent_cleared']:.1f}%)")
        
        # SUCCESS RATE - Prominently displayed
        print("\n" + "-"*60)
        print("SUCCESS RATE CALCULATION")
        print("-"*60)
        rescued = results['evacuees_rescued']
        avg_priority = results.get('avg_priority', 100.0)
        time = results['time']
        responders = results.get('num_responders', 2)
        success_score = results['success_score']
        
        print(f"Formula: SR = (Rescued × Avg_Priority) / (Time × Responders)")
        print(f"         SR = ({rescued} × {avg_priority:.2f}) / ({time:.1f} × {responders})")
        print(f"         SR = {rescued * avg_priority:.2f} / {time * responders:.2f}")
        print(f"\n>>> SUCCESS RATE: {success_score:.4f} <<<")
        print("-"*60)
        
        print(f"\nAvg Hazard Exposure: {results['avg_hazard_exposure']:.2f}")
        print(f"Max Hazard Level:    {results['max_hazard']:.2f}")
        print("\nPer-Agent Stats:")
        print("-" * 60)
        
        for agent_stat in results['agents']:
            print(f"  Agent {agent_stat['agent_id']}: "
                  f"Cleared {agent_stat['rooms_cleared']} rooms, "
                  f"Rescued {agent_stat['evacuees_rescued']} evacuees, "
                  f"Traveled {agent_stat['distance_traveled']:.1f}m")
        
        print("="*60 + "\n")


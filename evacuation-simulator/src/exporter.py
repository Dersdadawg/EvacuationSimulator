"""
Exporter module: Export simulation data to JSON/CSV for Blender
"""

import json
import csv
import os
from typing import Dict, List
from pathlib import Path


class Exporter:
    """Exports simulation data to files"""
    
    def __init__(self, output_dir: str = "outputs"):
        self.output_dir = Path(output_dir)
        self.frames_dir = self.output_dir / "frames"
        self.metrics_dir = self.output_dir / "metrics"
        
        # Create directories
        self.frames_dir.mkdir(parents=True, exist_ok=True)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
    
    def export_frames_json(self, history: List[Dict], scenario_name: str = "simulation"):
        """
        Export all frames as individual JSON files
        
        Args:
            history: List of frame dictionaries from simulation
            scenario_name: Name for this simulation run
        """
        scenario_dir = self.frames_dir / scenario_name
        scenario_dir.mkdir(exist_ok=True)
        
        print(f"Exporting {len(history)} frames to {scenario_dir}")
        
        for frame in history:
            timestep = frame['timestep']
            filename = scenario_dir / f"frame_{timestep:05d}.json"
            
            # Convert numpy arrays to lists for JSON serialization
            export_data = {
                'frame': timestep,
                'grid': frame['grid'].tolist(),
                'responders': frame['responders'],
                'evacuees': frame['evacuees'],
                'danger_cells': frame['danger_cells'],
            }
            
            with open(filename, 'w') as f:
                json.dump(export_data, f, indent=2)
        
        # Also create a metadata file
        metadata = {
            'scenario_name': scenario_name,
            'total_frames': len(history),
            'grid_width': frame['grid'].shape[1] if history else 0,
            'grid_height': frame['grid'].shape[0] if history else 0,
        }
        
        with open(scenario_dir / "metadata.json", 'w') as f:
            json.dump(metadata, f, indent=2)
        
        print(f"Export complete: {len(history)} frames")
    
    def export_single_json(self, history: List[Dict], scenario_name: str = "simulation"):
        """
        Export all frames as a single JSON file (more compact)
        
        Args:
            history: List of frame dictionaries from simulation
            scenario_name: Name for this simulation run
        """
        filename = self.frames_dir / f"{scenario_name}.json"
        
        print(f"Exporting {len(history)} frames to {filename}")
        
        # Convert numpy arrays to lists
        export_history = []
        for frame in history:
            export_data = {
                'frame': frame['timestep'],
                'grid': frame['grid'].tolist(),
                'responders': frame['responders'],
                'evacuees': frame['evacuees'],
                'danger_cells': frame['danger_cells'],
            }
            export_history.append(export_data)
        
        with open(filename, 'w') as f:
            json.dump(export_history, f, indent=2)
        
        print(f"Export complete: {filename}")
    
    def export_metrics_csv(self, metrics: Dict, scenario_name: str = "simulation"):
        """
        Export simulation metrics to CSV
        
        Args:
            metrics: Metrics dictionary from simulation
            scenario_name: Name for this simulation run
        """
        filename = self.metrics_dir / f"{scenario_name}_metrics.csv"
        
        with open(filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Metric', 'Value'])
            for key, value in metrics.items():
                writer.writerow([key, value])
        
        print(f"Metrics exported to {filename}")
    
    def export_agent_paths_csv(self, history: List[Dict], scenario_name: str = "simulation"):
        """
        Export agent movement paths to CSV for analysis
        
        Args:
            history: List of frame dictionaries from simulation
            scenario_name: Name for this simulation run
        """
        # Export responder paths
        responder_file = self.metrics_dir / f"{scenario_name}_responder_paths.csv"
        with open(responder_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestep', 'ResponderID', 'X', 'Y', 'Active', 'RescuedCount'])
            
            for frame in history:
                for responder in frame['responders']:
                    writer.writerow([
                        frame['timestep'],
                        responder['id'],
                        responder['x'],
                        responder['y'],
                        responder['active'],
                        responder['rescued_count'],
                    ])
        
        # Export evacuee paths
        evacuee_file = self.metrics_dir / f"{scenario_name}_evacuee_paths.csv"
        with open(evacuee_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['Timestep', 'EvacueeID', 'X', 'Y', 'Active', 'Evacuated', 'Rescued', 'Stuck'])
            
            for frame in history:
                for evacuee in frame['evacuees']:
                    writer.writerow([
                        frame['timestep'],
                        evacuee['id'],
                        evacuee['x'],
                        evacuee['y'],
                        evacuee['active'],
                        evacuee['evacuated'],
                        evacuee['rescued'],
                        evacuee['stuck'],
                    ])
        
        print(f"Agent paths exported to {self.metrics_dir}")
    
    def export_all(self, history: List[Dict], metrics: Dict, scenario_name: str = "simulation",
                   use_single_json: bool = True):
        """
        Export all data (frames + metrics + paths)
        
        Args:
            history: List of frame dictionaries from simulation
            metrics: Metrics dictionary from simulation
            scenario_name: Name for this simulation run
            use_single_json: If True, export single JSON file; if False, individual frame files
        """
        if use_single_json:
            self.export_single_json(history, scenario_name)
        else:
            self.export_frames_json(history, scenario_name)
        
        self.export_metrics_csv(metrics, scenario_name)
        self.export_agent_paths_csv(history, scenario_name)
        
        print(f"\nAll data exported for scenario: {scenario_name}")


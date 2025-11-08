"""Layout loader for building definitions"""

import json
from pathlib import Path
from typing import Dict, Any


class LayoutLoader:
    """Loads building layouts from JSON files"""
    
    @staticmethod
    def load(filepath: str) -> Dict[str, Any]:
        """
        Load layout from JSON file
        
        Args:
            filepath: Path to layout JSON file
        
        Returns:
            Layout dictionary
        """
        path = Path(filepath)
        
        if not path.exists():
            raise FileNotFoundError(f"Layout file not found: {filepath}")
        
        with open(path, 'r') as f:
            layout = json.load(f)
        
        # Validate required fields
        if 'rooms' not in layout:
            raise ValueError("Layout must contain 'rooms' field")
        
        return layout
    
    @staticmethod
    def save(layout: Dict[str, Any], filepath: str):
        """
        Save layout to JSON file
        
        Args:
            layout: Layout dictionary
            filepath: Output path
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            json.dump(layout, f, indent=2)
    
    @staticmethod
    def create_simple_layout(num_rooms: int = 6, floor: int = 0) -> Dict[str, Any]:
        """
        Create a simple grid layout for testing
        
        Args:
            num_rooms: Number of rooms to create
            floor: Floor number
        
        Returns:
            Layout dictionary
        """
        import math
        
        # Arrange rooms in grid
        cols = int(math.ceil(math.sqrt(num_rooms)))
        spacing_x = 30
        spacing_y = 30
        
        rooms = []
        connections = []
        
        # Create rooms in grid
        for i in range(num_rooms):
            row = i // cols
            col = i % cols
            
            room_id = f"R{floor}{i:02d}"
            x = col * spacing_x
            y = row * spacing_y
            
            rooms.append({
                'id': room_id,
                'floor': floor,
                'x': x,
                'y': y,
                'width': 20,
                'height': 20,
                'area': 400,
                'evacuees': 0 if i == 0 else (1 if i % 3 == 0 else 0),
                'is_exit': i == 0,
                'is_stair': False
            })
            
            # Connect to previous room (horizontal)
            if col > 0:
                prev_id = f"R{floor}{i-1:02d}"
                connections.append({
                    'from': prev_id,
                    'to': room_id,
                    'distance': spacing_x
                })
            
            # Connect to room above (vertical)
            if row > 0:
                above_id = f"R{floor}{i-cols:02d}"
                connections.append({
                    'from': above_id,
                    'to': room_id,
                    'distance': spacing_y
                })
        
        # Agent starts at exit
        agent_starts = [{'x': 0, 'y': 0, 'floor': floor}]
        
        return {
            'name': f'Simple {num_rooms}-room layout',
            'rooms': rooms,
            'connections': connections,
            'agent_starts': agent_starts
        }


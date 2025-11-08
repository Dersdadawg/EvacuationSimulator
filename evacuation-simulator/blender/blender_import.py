"""
Blender Import Script: Load and animate evacuation simulation data
Run this script inside Blender's Scripting workspace

Instructions:
1. Open Blender
2. Go to Scripting workspace
3. Open this file or paste its contents
4. Update DATA_PATH to point to your exported JSON file
5. Run script (Alt+P or click Run button)
"""

import bpy
import json
import os
from pathlib import Path


# ===== CONFIGURATION =====
# Update this path to your exported simulation data
DATA_PATH = "../outputs/frames/fire_scenario.json"
CELL_SIZE = 1.0
FRAME_RATE = 10  # Frames per second


# ===== COLORS =====
COLORS = {
    'wall': (0.0, 0.0, 0.0, 1.0),      # Black
    'safe': (0.9, 0.9, 0.9, 1.0),      # Light gray
    'exit': (0.0, 1.0, 0.0, 1.0),      # Green
    'danger': (1.0, 0.0, 0.0, 0.7),    # Red (semi-transparent)
    'responder': (0.0, 0.0, 1.0, 1.0), # Blue
    'evacuee': (1.0, 1.0, 0.0, 1.0),   # Yellow
}


def clear_scene():
    """Remove all objects from scene"""
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete()


def create_material(name, color):
    """Create a material with given color"""
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    
    # Get the material output node
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    if bsdf:
        bsdf.inputs['Base Color'].default_value = color
        bsdf.inputs['Metallic'].default_value = 0.0
        bsdf.inputs['Roughness'].default_value = 0.5
    
    return mat


def create_cell_mesh(x, y, z, size, material):
    """Create a cube mesh for a grid cell"""
    bpy.ops.mesh.primitive_cube_add(
        size=size,
        location=(x * size, y * size, z)
    )
    obj = bpy.context.active_object
    obj.data.materials.append(material)
    return obj


def create_agent_mesh(name, x, y, z, size, material, shape='CUBE'):
    """Create a mesh for an agent (responder or evacuee)"""
    if shape == 'SPHERE':
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=size * 0.4,
            location=(x * size + size/2, y * size + size/2, z + size/2)
        )
    else:
        bpy.ops.mesh.primitive_cube_add(
            size=size * 0.6,
            location=(x * size + size/2, y * size + size/2, z + size/2)
        )
    
    obj = bpy.context.active_object
    obj.name = name
    obj.data.materials.append(material)
    return obj


def load_and_animate(json_path):
    """Load simulation data and create animation"""
    print(f"Loading data from {json_path}")
    
    with open(json_path, 'r') as f:
        frames = json.load(f)
    
    if not frames:
        print("No frames found in data!")
        return
    
    print(f"Loaded {len(frames)} frames")
    
    # Clear existing scene
    clear_scene()
    
    # Create materials
    materials = {
        key: create_material(key, color)
        for key, color in COLORS.items()
    }
    
    # Get grid dimensions from first frame
    first_grid = frames[0]['grid']
    height = len(first_grid)
    width = len(first_grid[0])
    
    print(f"Grid size: {width}x{height}")
    
    # Create static grid (walls, exits, etc.)
    grid_objects = {}
    for y in range(height):
        for x in range(width):
            cell_value = first_grid[y][x]
            
            # Only create objects for walls and exits (static elements)
            if cell_value == 0:  # Wall
                obj = create_cell_mesh(x, y, 0, CELL_SIZE, materials['wall'])
                obj.name = f"wall_{x}_{y}"
            elif cell_value == 2:  # Exit
                obj = create_cell_mesh(x, y, 0, CELL_SIZE, materials['exit'])
                obj.name = f"exit_{x}_{y}"
    
    # Create agent objects (will be animated)
    responder_objects = {}
    evacuee_objects = {}
    
    # Identify all unique agents from first frame
    for resp in frames[0]['responders']:
        obj = create_agent_mesh(
            f"responder_{resp['id']}",
            resp['x'], resp['y'], 0,
            CELL_SIZE,
            materials['responder'],
            shape='CUBE'
        )
        responder_objects[resp['id']] = obj
    
    for evac in frames[0]['evacuees']:
        obj = create_agent_mesh(
            f"evacuee_{evac['id']}",
            evac['x'], evac['y'], 0,
            CELL_SIZE,
            materials['evacuee'],
            shape='SPHERE'
        )
        evacuee_objects[evac['id']] = obj
    
    # Set up animation
    bpy.context.scene.frame_start = 0
    bpy.context.scene.frame_end = len(frames) - 1
    bpy.context.scene.render.fps = FRAME_RATE
    
    # Animate agents
    for frame_idx, frame in enumerate(frames):
        # Animate responders
        for resp in frame['responders']:
            rid = resp['id']
            if rid in responder_objects:
                obj = responder_objects[rid]
                
                # Set location
                obj.location = (
                    resp['x'] * CELL_SIZE + CELL_SIZE/2,
                    resp['y'] * CELL_SIZE + CELL_SIZE/2,
                    CELL_SIZE/2
                )
                obj.keyframe_insert(data_path="location", frame=frame_idx)
                
                # Hide if not active
                obj.hide_viewport = not resp['active']
                obj.hide_render = not resp['active']
                obj.keyframe_insert(data_path="hide_viewport", frame=frame_idx)
                obj.keyframe_insert(data_path="hide_render", frame=frame_idx)
        
        # Animate evacuees
        for evac in frame['evacuees']:
            eid = evac['id']
            if eid in evacuee_objects:
                obj = evacuee_objects[eid]
                
                # Set location
                obj.location = (
                    evac['x'] * CELL_SIZE + CELL_SIZE/2,
                    evac['y'] * CELL_SIZE + CELL_SIZE/2,
                    CELL_SIZE/2
                )
                obj.keyframe_insert(data_path="location", frame=frame_idx)
                
                # Hide if evacuated
                should_hide = evac['evacuated'] or not evac['active']
                obj.hide_viewport = should_hide
                obj.hide_render = should_hide
                obj.keyframe_insert(data_path="hide_viewport", frame=frame_idx)
                obj.keyframe_insert(data_path="hide_render", frame=frame_idx)
    
    # Set up camera
    bpy.ops.object.camera_add(location=(width/2 * CELL_SIZE, height/2 * CELL_SIZE, max(width, height) * 1.5))
    camera = bpy.context.active_object
    camera.rotation_euler = (0, 0, 0)  # Top-down view
    bpy.context.scene.camera = camera
    
    # Add light
    bpy.ops.object.light_add(type='SUN', location=(width/2 * CELL_SIZE, height/2 * CELL_SIZE, 50))
    light = bpy.context.active_object
    light.data.energy = 2.0
    
    print("Animation setup complete!")
    print(f"Total frames: {len(frames)}")
    print("Press SPACEBAR to play animation or go to Render > Render Animation")


# ===== MAIN EXECUTION =====
if __name__ == "__main__":
    # Get the directory of this script
    script_dir = Path(__file__).parent
    data_file = script_dir / Path(DATA_PATH)
    
    if data_file.exists():
        load_and_animate(str(data_file))
    else:
        print(f"ERROR: Data file not found: {data_file}")
        print(f"Please update DATA_PATH in the script to point to your exported JSON file")


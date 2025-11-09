"""Renders walls as grid cells with door openings"""

import matplotlib.patches as patches


class WallRenderer:
    """Renders walls as individual 0.5m grid cells with blank cells for doors"""
    
    def __init__(self, ax, layout, current_floor=0, grid_resolution=0.5):
        self.ax = ax
        self.layout = layout
        self.current_floor = current_floor
        self.grid_res = grid_resolution
        self.wall_patches = []
    
    def draw_walls(self):
        """Draw walls as grid cells with door gaps"""
        # Clear previous walls
        for patch in self.wall_patches:
            patch.remove()
        self.wall_patches = []
        
        # Get rooms on current floor
        rooms = {}
        for room_data in self.layout.get('rooms', []):
            if room_data.get('floor', 0) == self.current_floor:
                rooms[room_data['id']] = room_data
        
        wall_color = '#37474F'  # Dark blue-gray
        door_width_cells = 3  # 1.5m door = 3 cells of 0.5m
        
        # Draw walls for each office (not hallway or exits)
        for room_id, room_data in rooms.items():
            room_type = room_data.get('type', 'office')
            if room_type == 'hallway' or room_data.get('is_exit'):
                continue
            
            x_center = room_data['x']
            y_center = room_data['y']
            w = room_data['width']
            h = room_data['height']
            
            x1, y1 = x_center - w/2, y_center - h/2
            x2, y2 = x_center + w/2, y_center + h/2
            
            # Determine door location (which wall faces hallway)
            door_on_top = False
            door_on_bottom = False
            
            for conn in self.layout.get('connections', []):
                if room_id in [conn['from'], conn['to']]:
                    other = conn['to'] if conn['from'] == room_id else conn['from']
                    other_room = rooms.get(other)
                    if other_room and other_room.get('type') == 'hallway':
                        hallway_y = other_room['y']
                        if hallway_y < y_center:
                            door_on_top = True
                        else:
                            door_on_bottom = True
            
            # Draw TOP WALL as grid cells
            if not door_on_top:
                # Full wall
                self._draw_wall_line(x1, y1, x2, y1, wall_color, horizontal=True)
            else:
                # Wall with door gap in center
                door_start = x_center - (door_width_cells * self.grid_res / 2)
                door_end = x_center + (door_width_cells * self.grid_res / 2)
                self._draw_wall_line(x1, y1, door_start, y1, wall_color, horizontal=True)
                self._draw_wall_line(door_end, y1, x2, y1, wall_color, horizontal=True)
            
            # Draw BOTTOM WALL as grid cells
            if not door_on_bottom:
                # Full wall
                self._draw_wall_line(x1, y2, x2, y2, wall_color, horizontal=True)
            else:
                # Wall with door gap in center
                door_start = x_center - (door_width_cells * self.grid_res / 2)
                door_end = x_center + (door_width_cells * self.grid_res / 2)
                self._draw_wall_line(x1, y2, door_start, y2, wall_color, horizontal=True)
                self._draw_wall_line(door_end, y2, x2, y2, wall_color, horizontal=True)
            
            # Draw LEFT WALL as grid cells (always full)
            self._draw_wall_line(x1, y1, x1, y2, wall_color, horizontal=False)
            
            # Draw RIGHT WALL as grid cells (always full)
            self._draw_wall_line(x2, y1, x2, y2, wall_color, horizontal=False)
    
    def _draw_wall_line(self, start_x, start_y, end_x, end_y, color, horizontal=True):
        """Draw a line of wall cells on the grid"""
        if horizontal:
            # Draw horizontal wall
            x = start_x
            while x < end_x:
                rect = patches.Rectangle(
                    (x, start_y - self.grid_res/2),
                    self.grid_res,
                    self.grid_res,
                    facecolor=color,
                    edgecolor='none',
                    alpha=0.9,
                    zorder=20
                )
                self.wall_patches.append(rect)
                self.ax.add_patch(rect)
                x += self.grid_res
        else:
            # Draw vertical wall
            y = start_y
            while y < end_y:
                rect = patches.Rectangle(
                    (start_x - self.grid_res/2, y),
                    self.grid_res,
                    self.grid_res,
                    facecolor=color,
                    edgecolor='none',
                    alpha=0.9,
                    zorder=20
                )
                self.wall_patches.append(rect)
                self.ax.add_patch(rect)
                y += self.grid_res


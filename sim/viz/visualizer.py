"""Main visualizer class coordinating pygame UI"""

import pygame
from typing import Optional
from pathlib import Path

from .renderer import Renderer
from ..engine.simulator import Simulator, SimulationEvent, EventType


class Visualizer:
    """Main visualization controller"""
    
    def __init__(self, simulator: Simulator, params: dict):
        """
        Initialize visualizer
        
        Args:
            simulator: Simulator instance
            params: Visualization parameters
        """
        self.sim = simulator
        self.params = params
        
        width = params.get('window_width', 1600)
        height = params.get('window_height', 900)
        self.fps_target = params.get('fps_target', 30)
        
        self.renderer = Renderer(width, height)
        self.clock = pygame.time.Clock()
        
        # Playback state
        self.paused = True
        self.speed = 1.0
        self.speed_options = [0.5, 1.0, 2.0, 4.0]
        self.speed_index = 1
        
        # Frame capture for video
        self.recording = params.get('save_video', False)
        self.frames = []
        
        # Register for events
        simulator.add_event_callback(self._handle_simulation_event)
    
    def _handle_simulation_event(self, event: SimulationEvent):
        """Handle simulation events for visualization"""
        # Add annotations for key events
        if event.event_type == EventType.ROOM_CLEARED:
            self.renderer.add_annotation("✓", event.room_id, event.tick, 
                                        duration=60, color=(0, 150, 0))
        
        elif event.event_type == EventType.EVACUEE_FOUND:
            count = event.data.get('count', 1)
            self.renderer.add_annotation(f"Found {count}!", event.room_id, 
                                        event.tick, duration=90, color=(200, 0, 0))
        
        elif event.event_type == EventType.EVACUEE_RESCUED:
            self.renderer.add_annotation("Rescued!", event.room_id, 
                                        event.tick, duration=60, color=(0, 100, 200))
    
    def run(self):
        """Run visualization with interactive controls"""
        running = True
        
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    
                    elif event.key == pygame.K_SPACE:
                        self.paused = not self.paused
                    
                    elif event.key == pygame.K_RIGHT:
                        # Step forward
                        if not self.sim.complete:
                            self.sim.step()
                    
                    elif event.key == pygame.K_EQUALS or event.key == pygame.K_PLUS:
                        # Increase speed
                        self.speed_index = min(self.speed_index + 1, 
                                              len(self.speed_options) - 1)
                        self.speed = self.speed_options[self.speed_index]
                    
                    elif event.key == pygame.K_MINUS:
                        # Decrease speed
                        self.speed_index = max(self.speed_index - 1, 0)
                        self.speed = self.speed_options[self.speed_index]
                    
                    elif event.key == pygame.K_UP:
                        # Next floor
                        max_floor = max(self.sim.env.floors.keys())
                        self.renderer.current_floor = min(
                            self.renderer.current_floor + 1, max_floor)
                    
                    elif event.key == pygame.K_DOWN:
                        # Previous floor
                        self.renderer.current_floor = max(
                            self.renderer.current_floor - 1, 0)
                    
                    elif event.key >= pygame.K_1 and event.key <= pygame.K_9:
                        # Direct floor selection
                        floor = event.key - pygame.K_1
                        if floor in self.sim.env.floors:
                            self.renderer.current_floor = floor
                    
                    elif event.key == pygame.K_h:
                        # Toggle hazard
                        self.renderer.show_hazard = not self.renderer.show_hazard
                    
                    elif event.key == pygame.K_t:
                        # Toggle trails
                        self.renderer.show_trails = not self.renderer.show_trails
                    
                    elif event.key == pygame.K_e:
                        # Toggle evacuees
                        self.renderer.show_evacuees = not self.renderer.show_evacuees
            
            # Update simulation if not paused
            if not self.paused and not self.sim.complete:
                # Run multiple steps for speed > 1
                steps = int(self.speed)
                for _ in range(steps):
                    if not self.sim.complete:
                        self.sim.step()
            
            # Render
            self.renderer.clear()
            self.renderer.render_map(self.sim.env, self.sim.agent_manager, self.sim.tick)
            self.renderer.render_controls(self.paused, self.speed, 
                                         self.sim.tick, self.sim.time)
            
            results = self.sim.get_results()
            self.renderer.render_info_panel(self.sim.env, self.sim.agent_manager, 
                                           results, self.sim.tick)
            
            self.renderer.flip()
            
            # Capture frame if recording
            if self.recording and self.sim.tick % 2 == 0:  # Every other frame
                self.frames.append(self.renderer.capture_frame())
            
            # Check if simulation complete
            if self.sim.complete:
                self.paused = True
            
            # Frame rate limit
            self.clock.tick(self.fps_target)
        
        pygame.quit()
        
        # Save video if recorded
        if self.recording and self.frames:
            self._save_video()
    
    def _save_video(self):
        """Save captured frames as video"""
        print(f"Saving video with {len(self.frames)} frames...")
        
        try:
            import subprocess
            from PIL import Image
            import tempfile
            
            # Save frames as images
            temp_dir = Path(tempfile.mkdtemp())
            
            for i, surface in enumerate(self.frames):
                # Convert pygame surface to PIL Image
                frame_data = pygame.surfarray.array3d(surface)
                frame_data = frame_data.swapaxes(0, 1)  # Pygame uses (width, height)
                img = Image.fromarray(frame_data)
                img.save(temp_dir / f"frame_{i:06d}.png")
            
            # Use ffmpeg to create video
            output_path = "outputs/run.mp4"
            Path("outputs").mkdir(exist_ok=True)
            
            cmd = [
                'ffmpeg', '-y',
                '-framerate', str(self.params.get('video_fps', 30)),
                '-i', str(temp_dir / 'frame_%06d.png'),
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                output_path
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"Video saved to {output_path}")
            
            # Clean up temp files
            for f in temp_dir.glob("*.png"):
                f.unlink()
            temp_dir.rmdir()
            
        except Exception as e:
            print(f"Warning: Could not save video: {e}")
            print("Frames captured but ffmpeg may not be available.")
    
    def run_headless(self, output_path: Optional[str] = None):
        """
        Run simulation without interactive display (faster)
        
        Args:
            output_path: Path to save final frame screenshot
        """
        while not self.sim.complete:
            self.sim.step()
        
        if output_path:
            # Render final state
            self.renderer.clear()
            self.renderer.render_map(self.sim.env, self.sim.agent_manager, self.sim.tick)
            results = self.sim.get_results()
            self.renderer.render_info_panel(self.sim.env, self.sim.agent_manager,
                                           results, self.sim.tick)
            
            pygame.image.save(self.renderer.screen, output_path)
            print(f"Final state saved to {output_path}")
        
        pygame.quit()


"""
Mini Doom-style raycaster for Waveshare 128x128 LCD.
Simple Wolfenstein 3D-style rendering directly to PIL.
Press KEY1, KEY2, or KEY3 to exit and return to menu.
"""

import math
import time

# Map: 1 = wall, 0 = empty
MAP = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,1,1,1,0,0,0,0,0,1,1,1,0,0,1],
    [1,0,1,0,0,0,0,0,0,0,0,0,1,0,0,1],
    [1,0,1,0,0,0,0,0,0,0,0,0,1,0,0,1],
    [1,0,0,0,0,0,1,1,1,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,1,0,1,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,1,0,1,0,0,0,0,0,0,1],
    [1,0,1,0,0,0,0,0,0,0,0,0,1,0,0,1],
    [1,0,1,0,0,0,0,0,0,0,0,0,1,0,0,1],
    [1,0,1,1,1,0,0,0,0,0,1,1,1,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,1,1,1,0,1,1,1,0,0,0,0,1],
    [1,0,0,0,1,0,0,0,0,0,1,0,0,0,0,1],
    [1,0,0,0,1,1,1,1,1,1,1,0,0,0,0,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
]

MAP_WIDTH = len(MAP[0])
MAP_HEIGHT = len(MAP)

# Wall colors based on direction (N/S vs E/W)
WALL_COLOR_NS = (180, 60, 60)   # Red-ish for N/S walls
WALL_COLOR_EW = (120, 40, 40)   # Darker for E/W walls
CEILING_COLOR = (40, 40, 60)
FLOOR_COLOR = (60, 60, 40)


class RaycasterGame:
    def __init__(self):
        # Player position and direction
        self.player_x = 2.5
        self.player_y = 2.5
        self.player_angle = 0.0  # Radians
        
        # Field of view
        self.fov = math.pi / 3  # 60 degrees
        
        # Rendering resolution (will be scaled to display)
        self.render_width = 64
        self.render_height = 48
        
        # Movement speed
        self.move_speed = 0.15
        self.rot_speed = 0.12
    
    def move_forward(self):
        new_x = self.player_x + math.cos(self.player_angle) * self.move_speed
        new_y = self.player_y + math.sin(self.player_angle) * self.move_speed
        # Collision detection
        if MAP[int(self.player_y)][int(new_x)] == 0:
            self.player_x = new_x
        if MAP[int(new_y)][int(self.player_x)] == 0:
            self.player_y = new_y
    
    def move_backward(self):
        new_x = self.player_x - math.cos(self.player_angle) * self.move_speed
        new_y = self.player_y - math.sin(self.player_angle) * self.move_speed
        if MAP[int(self.player_y)][int(new_x)] == 0:
            self.player_x = new_x
        if MAP[int(new_y)][int(self.player_x)] == 0:
            self.player_y = new_y
    
    def strafe_left(self):
        strafe_angle = self.player_angle - math.pi / 2
        new_x = self.player_x + math.cos(strafe_angle) * self.move_speed
        new_y = self.player_y + math.sin(strafe_angle) * self.move_speed
        if MAP[int(self.player_y)][int(new_x)] == 0:
            self.player_x = new_x
        if MAP[int(new_y)][int(self.player_x)] == 0:
            self.player_y = new_y
    
    def strafe_right(self):
        strafe_angle = self.player_angle + math.pi / 2
        new_x = self.player_x + math.cos(strafe_angle) * self.move_speed
        new_y = self.player_y + math.sin(strafe_angle) * self.move_speed
        if MAP[int(self.player_y)][int(new_x)] == 0:
            self.player_x = new_x
        if MAP[int(new_y)][int(self.player_x)] == 0:
            self.player_y = new_y
    
    def turn_left(self):
        self.player_angle -= self.rot_speed
    
    def turn_right(self):
        self.player_angle += self.rot_speed
    
    def cast_ray(self, ray_angle):
        """Cast a single ray and return distance to wall and wall side."""
        # Normalize angle
        ray_angle = ray_angle % (2 * math.pi)
        
        # Ray direction
        ray_dir_x = math.cos(ray_angle)
        ray_dir_y = math.sin(ray_angle)
        
        # Current map position
        map_x = int(self.player_x)
        map_y = int(self.player_y)
        
        # Length of ray from one x/y side to next
        delta_dist_x = abs(1 / ray_dir_x) if ray_dir_x != 0 else 1e30
        delta_dist_y = abs(1 / ray_dir_y) if ray_dir_y != 0 else 1e30
        
        # Step direction and initial side distance
        if ray_dir_x < 0:
            step_x = -1
            side_dist_x = (self.player_x - map_x) * delta_dist_x
        else:
            step_x = 1
            side_dist_x = (map_x + 1.0 - self.player_x) * delta_dist_x
        
        if ray_dir_y < 0:
            step_y = -1
            side_dist_y = (self.player_y - map_y) * delta_dist_y
        else:
            step_y = 1
            side_dist_y = (map_y + 1.0 - self.player_y) * delta_dist_y
        
        # DDA algorithm
        hit = False
        side = 0  # 0 = N/S wall, 1 = E/W wall
        max_depth = 20
        
        for _ in range(max_depth):
            if side_dist_x < side_dist_y:
                side_dist_x += delta_dist_x
                map_x += step_x
                side = 0
            else:
                side_dist_y += delta_dist_y
                map_y += step_y
                side = 1
            
            if 0 <= map_x < MAP_WIDTH and 0 <= map_y < MAP_HEIGHT:
                if MAP[map_y][map_x] > 0:
                    hit = True
                    break
        
        if not hit:
            return max_depth, side
        
        # Calculate perpendicular distance (avoids fisheye)
        if side == 0:
            perp_dist = (map_x - self.player_x + (1 - step_x) / 2) / ray_dir_x if ray_dir_x != 0 else max_depth
        else:
            perp_dist = (map_y - self.player_y + (1 - step_y) / 2) / ray_dir_y if ray_dir_y != 0 else max_depth
        
        return abs(perp_dist), side
    
    def render_frame(self):
        """Render a frame and return pixel data as list of (x, y, color) tuples."""
        pixels = []
        
        for x in range(self.render_width):
            # Calculate ray angle for this column
            ray_angle = self.player_angle - self.fov / 2 + (x / self.render_width) * self.fov
            
            # Cast ray
            distance, side = self.cast_ray(ray_angle)
            
            # Calculate wall height
            if distance > 0:
                wall_height = int(self.render_height / distance)
            else:
                wall_height = self.render_height
            
            wall_height = min(wall_height, self.render_height)
            
            # Calculate wall top/bottom
            wall_top = (self.render_height - wall_height) // 2
            wall_bottom = wall_top + wall_height
            
            # Draw column
            for y in range(self.render_height):
                if y < wall_top:
                    color = CEILING_COLOR
                elif y < wall_bottom:
                    # Shade based on distance
                    shade = max(0.3, 1.0 - distance / 10)
                    if side == 0:
                        base = WALL_COLOR_NS
                    else:
                        base = WALL_COLOR_EW
                    color = (int(base[0] * shade), int(base[1] * shade), int(base[2] * shade))
                else:
                    color = FLOOR_COLOR
                
                pixels.append((x, y, color))
        
        return pixels


class DoomWaveshare:
    """Doom-style raycaster that renders to Waveshare 128x128 display."""
    
    def __init__(self, display, input_handler):
        self.display = display
        self.input_handler = input_handler
        self.running = False
        self.game = RaycasterGame()
        
        # Scale factors (render 64x48, display at 128x96 centered)
        self.scale_x = 2
        self.scale_y = 2
        self.offset_x = 0
        self.offset_y = 10
    
    def start(self):
        """Start the game loop."""
        self.running = True
        
        while self.running:
            # Handle input
            action = self.input_handler.get_input()
            
            # Check for exit keys
            if action in ('key1', 'key2', 'key3'):
                self.running = False
                return action
            
            # Movement controls
            if action == 'up':
                self.game.move_forward()
            elif action == 'down':
                self.game.move_backward()
            elif action == 'left':
                self.game.turn_left()
            elif action == 'right':
                self.game.turn_right()
            elif action == 'select':
                # Strafe mode: could toggle or use differently
                pass
            
            # Render
            self.render()
            time.sleep(0.03)  # ~30 FPS target
        
        return None
    
    def render(self):
        """Render the game to the display."""
        self.display.clear((0, 0, 0))
        draw = self.display.draw
        
        # Get rendered frame from raycaster
        pixels = self.game.render_frame()
        
        # Draw scaled pixels to display
        for x, y, color in pixels:
            # Scale up
            sx = self.offset_x + x * self.scale_x
            sy = self.offset_y + y * self.scale_y
            # Draw scaled pixel as rectangle
            draw.rectangle(
                (sx, sy, sx + self.scale_x - 1, sy + self.scale_y - 1),
                fill=color
            )
        
        # Draw "DOOM" title at top
        draw.text((2, 0), "MINI DOOM", font=self.display.font_tiny, fill=(255, 100, 100))
        
        # Draw minimap in corner
        self._draw_minimap()
        
        # Draw controls hint at bottom
        draw.text((2, 118), "^v Move <> Turn", font=self.display.font_tiny, fill=(100, 100, 100))
        
        # Push to display
        self.display._render()
    
    def _draw_minimap(self):
        """Draw a tiny minimap in the corner."""
        draw = self.display.draw
        map_x = 100
        map_y = 2
        cell_size = 1
        
        # Draw map cells around player
        view_range = 8
        px, py = int(self.game.player_x), int(self.game.player_y)
        
        for dy in range(-view_range // 2, view_range // 2):
            for dx in range(-view_range // 2, view_range // 2):
                mx, my = px + dx, py + dy
                if 0 <= mx < MAP_WIDTH and 0 <= my < MAP_HEIGHT:
                    if MAP[my][mx] == 1:
                        color = (100, 100, 100)
                    else:
                        color = (30, 30, 30)
                    sx = map_x + (dx + view_range // 2) * cell_size
                    sy = map_y + (dy + view_range // 2) * cell_size
                    draw.rectangle((sx, sy, sx + cell_size - 1, sy + cell_size - 1), fill=color)
        
        # Draw player position
        player_sx = map_x + view_range // 2 * cell_size
        player_sy = map_y + view_range // 2 * cell_size
        draw.rectangle((player_sx, player_sy, player_sx + cell_size, player_sy + cell_size), fill=(0, 255, 0))


def run_doom(display, input_handler):
    """
    Run the Doom-style raycaster on the Waveshare display.
    Returns the exit key pressed ('key1', 'key2', 'key3') or None.
    """
    game = DoomWaveshare(display, input_handler)
    return game.start()

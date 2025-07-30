import random
import pygame
import secp256k1 as ice
import os

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 600
BALL_RADIUS = 20  # Increased for better image visibility
INITIAL_BALL_COUNT = 72
TARGET_ADDRESS = '12VVRNPi4SJqUTsp6FmqDqY5sGosDtysn4'
MUSIC_VOLUME = 0.3  # 30% volume

# Colors
RED = (255, 255, 255)
RED = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
SHADOW_COLOR = (50, 50, 50, 100)

# Initialize screen and font
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Interactive Ball Game - Bitcoin Address Search")
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)


class ImageLoader:
    """Handles loading and caching of images"""
    
    def __init__(self):
        self.background = None
        self.ball_image = None
        self.default_ball_color = RED
        
    def load_background(self, filepath):
        """Load and scale background image"""
        try:
            if os.path.exists(filepath):
                # Load and convert the image for proper display
                temp_image = pygame.image.load(filepath)
                self.background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
                # Scale and blit to ensure proper format
                scaled_image = pygame.transform.scale(temp_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
                self.background.blit(scaled_image, (0, 0))
                self.background = self.background.convert()
                print(f"Background image loaded successfully: {filepath}")
            else:
                print(f"Background image not found: {filepath}")
                self.create_default_background()
        except Exception as e:
            print(f"Error loading background image: {e}")
            self.create_default_background()
    
    def create_default_background(self):
        """Create a gradient background if no image is loaded"""
        self.background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        for y in range(SCREEN_HEIGHT):
            color_value = int(50 + (y / SCREEN_HEIGHT) * 100)
            pygame.draw.line(self.background, (color_value, color_value, color_value + 20), 
                           (0, y), (SCREEN_WIDTH, y))
        print("Created default gradient background")
    
    def load_ball_image(self, filepath):
        """Load a single ball image for all balls"""
        try:
            if os.path.exists(filepath):
                self.ball_image = pygame.image.load(filepath).convert_alpha()
                # Scale image to fit ball size
                self.ball_image = pygame.transform.scale(self.ball_image, (BALL_RADIUS * 2, BALL_RADIUS * 2))
                print(f"Ball image loaded successfully: {filepath}")
            else:
                print(f"Ball image not found: {filepath}")
                self.create_default_ball_image()
        except Exception as e:
            print(f"Error loading ball image: {e}")
            self.create_default_ball_image()
    
    def create_default_ball_image(self):
        """Create a default ball image"""
        surface = pygame.Surface((BALL_RADIUS * 2, BALL_RADIUS * 2), pygame.SRCALPHA)
        # Draw main ball
        pygame.draw.circle(surface, RED, (BALL_RADIUS, BALL_RADIUS), BALL_RADIUS)
        # Add border
        pygame.draw.circle(surface, RED, (BALL_RADIUS, BALL_RADIUS), BALL_RADIUS, 2)
        # Add highlight for 3D effect
        pygame.draw.circle(surface, (255, 255, 255, 100), 
                         (BALL_RADIUS - BALL_RADIUS//3, BALL_RADIUS - BALL_RADIUS//3), 
                         BALL_RADIUS//3)
        self.ball_image = surface
        print("Created default ball image")


class Ball:
    """Represents a bouncing ball with physics properties"""
    
    def __init__(self, x, y, radius, velocity_range, image=None):
        self.x = x
        self.y = y
        self.radius = radius
        self.dx = random.uniform(velocity_range[0], velocity_range[1])
        self.dy = random.uniform(velocity_range[0], velocity_range[1])
        self.gravity = 0
        self.friction = 1
        self.image = image
        self.rotation = 0
        self.rotation_speed = random.uniform(-5, 5)
        
    def get_speed_hex(self):
        """Generate hex character based on ball speed"""
        speed = int((self.dx ** 2 + self.dy ** 2) ** 0.5)
        return hex(speed % 16)[2:]
    
    def get_speed_binary(self):
        """Generate binary character based on ball position"""
        speed = int((self.x ** 2 + self.y ** 2) ** 0.5)
        return str(speed % 2)
    
    def update(self):
        """Update ball position and handle wall collisions"""
        # Apply physics
        self.dy += self.gravity
        self.x += self.dx * self.friction
        self.y += self.dy * self.friction
        
        # Update rotation based on movement
        self.rotation += self.rotation_speed
        
        # Wall collisions
        if self.x - self.radius <= 0 or self.x + self.radius >= SCREEN_WIDTH:
            self.dx *= -1
            self.rotation_speed *= -1  # Reverse rotation on collision
            self.x = max(self.radius, min(SCREEN_WIDTH - self.radius, self.x))
            
        if self.y - self.radius <= 0 or self.y + self.radius >= SCREEN_HEIGHT:
            self.dy *= -1
            self.rotation_speed *= -1  # Reverse rotation on collision
            self.y = max(self.radius, min(SCREEN_HEIGHT - self.radius, self.y))
    
    def check_collision(self, other):
        """Check and resolve collision with another ball"""
        dx = self.x - other.x
        dy = self.y - other.y
        distance = (dx ** 2 + dy ** 2) ** 0.5
        
        if distance < self.radius + other.radius:
            # Calculate overlap
            overlap = 0.5 * (self.radius + other.radius - distance + 1)
            distance = max(distance, 1)  # Prevent division by zero
            
            # Normalize collision vector
            nx = dx / distance
            ny = dy / distance
            
            # Separate balls
            self.x += overlap * nx
            self.y += overlap * ny
            other.x -= overlap * nx
            other.y -= overlap * ny
            
            # Calculate relative velocity
            dvx = self.dx - other.dx
            dvy = self.dy - other.dy
            
            # Calculate impulse
            impulse = 2 * (dvx * nx + dvy * ny) / 2
            
            # Apply impulse
            self.dx -= impulse * nx
            self.dy -= impulse * ny
            other.dx += impulse * nx
            other.dy += impulse * ny
    
    def handle_click(self, mouse_x, mouse_y, power_multiplier=50):
        """Apply force to ball when clicked"""
        dx = mouse_x - self.x
        dy = mouse_y - self.y
        distance = (dx ** 2 + dy ** 2) ** 0.5
        
        if distance <= self.radius:
            # Apply force away from click point
            if distance > 0:
                self.dx = -(dx / distance) * power_multiplier
                self.dy = -(dy / distance) * power_multiplier
            return True
        return False
    
    def draw(self, surface):
        """Draw the ball with its image on the surface"""
        
        # Draw shadow
        shadow_offset = 3
        shadow_surface = pygame.Surface((self.radius * 2 + 10, self.radius * 2 + 10), pygame.SRCALPHA)
        pygame.draw.circle(shadow_surface, (0, 0, 0, 50), 
                         (self.radius + 5, self.radius + 5), 
                         self.radius)
        surface.blit(shadow_surface, 
                    (int(self.x - self.radius - 5 + shadow_offset), 
                     int(self.y - self.radius - 5 + shadow_offset)))
        
        if self.image:
            # Rotate and draw the image
            rotated_image = pygame.transform.rotate(self.image, self.rotation)
            rect = rotated_image.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(rotated_image, rect)
        else:
            # Fallback to colored circle if no image
            pygame.draw.circle(surface, RED, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(surface, RED, (int(self.x), int(self.y)), self.radius, 2)


class HexManipulator:
    """Handles hex string manipulations"""
    
    @staticmethod
    def shift_hex_digits(hex_string):
        """Shift each hex digit by 1 (0->1, 1->2, ..., f->0)"""
        translation = str.maketrans("0123456789abcdef", "123456789abcdef0")
        return hex_string.translate(translation)
    
    @staticmethod
    def rotate_left(string, n):
        """Rotate string left by n positions"""
        n = n % len(string)
        return string[n:] + string[:n]
    
    @staticmethod
    def invert_binary(binary_string):
        """Invert binary string (0->1, 1->0)"""
        return ''.join('1' if c == '0' else '0' for c in binary_string)


class BallGame:
    """Main game class"""
    
    def __init__(self):
        self.clock = pygame.time.Clock()
        self.running = True
        self.score = 0
        self.iteration = 0
        self.found = False
        self.velocity_range = [-1, 1]
        self.balls = []
        self.hex_manipulator = HexManipulator()
        self.music_playing = True
        self.music_loaded = False
        
        # Initialize image loader
        self.image_loader = ImageLoader()
        
        # Load images
        self.load_images()
        
        # Try to load background music
        self.load_music()
        
        # Create initial balls
        self.reset_balls()
    
    def load_images(self):
        """Load background and ball images"""
        # Get current directory
        current_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else os.getcwd()
        
        # Load background image - try multiple extensions
        background_loaded = False
        for ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            background_path = os.path.join(current_dir, f'background{ext}')
            if os.path.exists(background_path):
                self.image_loader.load_background(background_path)
                background_loaded = True
                break
        
        if not background_loaded:
            print(f"No background image found in {current_dir}")
            print("Looking for: background.jpg, background.png, etc.")
            self.image_loader.create_default_background()
        
        # Load ball image - try multiple extensions
        ball_loaded = False
        for ext in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
            ball_path = os.path.join(current_dir, f'ball{ext}')
            if os.path.exists(ball_path):
                self.image_loader.load_ball_image(ball_path)
                ball_loaded = True
                break
        
        if not ball_loaded:
            print(f"No ball image found in {current_dir}")
            print("Looking for: ball.png, ball.jpg, etc.")
            self.image_loader.create_default_ball_image()
        
    def load_music(self):
        """Load background music file"""
        try:
            # Try to load music file - change filename to your MP3 file
            pygame.mixer.music.load("background.mp3")
            pygame.mixer.music.set_volume(MUSIC_VOLUME)
            pygame.mixer.music.play(-1)  # -1 means loop forever
            self.music_loaded = True
            print("Music loaded successfully!")
        except pygame.error as e:
            print(f"Could not load music file: {e}")
            print("Game will continue without music.")
            self.music_loaded = False
            self.music_playing = False
    
    def toggle_music(self):
        """Toggle music on/off"""
        if not self.music_loaded:
            return
            
        if self.music_playing:
            pygame.mixer.music.pause()
            self.music_playing = False
        else:
            pygame.mixer.music.unpause()
            self.music_playing = True
    
    def reset_balls(self):
        """Create new set of balls with updated velocity range"""
        self.balls = []
        for _ in range(INITIAL_BALL_COUNT):
            ball = Ball(
                x=random.randint(50, SCREEN_WIDTH - 50),
                y=random.randint(50, SCREEN_HEIGHT - 50),
                radius=BALL_RADIUS,
                velocity_range=self.velocity_range,
                image=self.image_loader.ball_image  # Use the same image for all balls
            )
            self.balls.append(ball)
    
    def update_velocity_range(self):
        """Expand velocity range"""
        self.velocity_range[0] -= 1
        self.velocity_range[1] += 1
    
    def handle_events(self):
        """Process pygame events"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos
                for ball in self.balls:
                    if ball.handle_click(mouse_x, mouse_y):
                        self.score += 1
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # Toggle music with spacebar
                    self.toggle_music()
                elif event.key == pygame.K_UP and self.music_loaded:
                    # Increase volume with UP arrow
                    current_volume = pygame.mixer.music.get_volume()
                    new_volume = min(1.0, current_volume + 0.1)
                    pygame.mixer.music.set_volume(new_volume)
                elif event.key == pygame.K_DOWN and self.music_loaded:
                    # Decrease volume with DOWN arrow
                    current_volume = pygame.mixer.music.get_volume()
                    new_volume = max(0.0, current_volume - 0.1)
                    pygame.mixer.music.set_volume(new_volume)
    
    def update_physics(self):
        """Update ball positions and handle collisions"""
        # Update each ball
        for ball in self.balls:
            ball.update()
        
        # Check collisions between balls
        for i, ball in enumerate(self.balls):
            for other in self.balls[i + 1:]:
                ball.check_collision(other)
    
    def search_bitcoin_address(self):
        """Generate binary string from balls and search for target address"""
        # Generate binary string from ball positions
        binary_string = ''.join(ball.get_speed_binary() for ball in self.balls)
        
        # Try different transformations
        for invert in range(2):
            for reverse in range(2):
                for shift in range(len(binary_string)):
                    # Convert binary to integer then to hex
                    try:
                        decimal_value = int(binary_string, 2)
                        hex_string = hex(decimal_value)[2:].zfill(len(self.balls) // 4)
                        
                        # Try different hex transformations
                        for hex_shift in range(16):
                            # Create private key
                            private_key = int('1' + hex_string, 16)
                            
                            # Generate Bitcoin address
                            address = ice.privatekey_to_address(0, True, private_key)
                            
                            # Log first attempt of each iteration
                            if shift == 0 and reverse == 0 and invert == 0 and hex_shift == 0:
                                print(f"{self.iteration} - {hex(private_key)[2:]} - {address}")
                            
                            # Check if we found the target
                            if address == TARGET_ADDRESS:
                                self.found = True
                                self.log_found_address(private_key, binary_string, address)
                                return
                            
                            # Transform hex string
                            hex_string = self.hex_manipulator.shift_hex_digits(hex_string)
                    
                    except ValueError:
                        pass
                    
                    # Rotate binary string
                    binary_string = self.hex_manipulator.rotate_left(binary_string, 1)
                
                # Reverse binary string
                binary_string = binary_string[::-1]
            
            # Invert binary string
            binary_string = self.hex_manipulator.invert_binary(binary_string)
    
    def log_found_address(self, private_key, binary_string, address):
        """Log the found address to file and console"""
        result = f"{hex(private_key)[2:]} - {binary_string} -> {address}"
        print(result)
        print("FOUND!")
        
        with open('found.txt', 'a') as file:
            file.write(result + '\n')
    
    def draw(self):
        """Draw all game elements"""
        #screen.fill(RED)
        if self.image_loader.background:
            screen.blit(self.image_loader.background, (0, 0))
        else:
            screen.fill(RED)
        # Draw balls
        for ball in self.balls:
            ball.draw(screen)
        
        # Draw UI
        score_text = font.render(f"Score: {self.score}", True, YELLOW)
        screen.blit(score_text, (1050, 10))
        score_text = font.render(f"Searching for: {TARGET_ADDRESS}", True, YELLOW)
        screen.blit(score_text, (10, 10))
        #iteration_text = small_font.render(f"Iteration: {self.iteration}", True, RED)
        #screen.blit(iteration_text, (10, 50))
        
        #velocity_text = small_font.render(
        #    f"Velocity Range: [{self.velocity_range[0]}, {self.velocity_range[1]}]", 
        #    True, RED
        #)
        #screen.blit(velocity_text, (10, 80))
        '''
        # Draw music status
        if self.music_loaded:
            music_status = "ON" if self.music_playing else "OFF"
            music_color = GREEN if self.music_playing else RED
            music_text = small_font.render(f"Music: {music_status} (SPACE to toggle)", True, music_color)
            screen.blit(music_text, (10, 110))
            
            # Show volume
            volume = int(pygame.mixer.music.get_volume() * 100)
            volume_text = small_font.render(f"Volume: {volume}% (↑/↓ to adjust)", True, RED)
            screen.blit(volume_text, (10, 140))
        '''
        # Draw instructions
        #instructions = [
        #    "Click on balls to launch them!",
        #    f"Searching for: {TARGET_ADDRESS[:20]}...",
        #    "SPACE: Toggle Music | ↑/↓: Volume"
        #]
        #for i, instruction in enumerate(instructions):
        #    inst_text = small_font.render(instruction, True, RED)
        #    screen.blit(inst_text, (SCREEN_WIDTH - 400, 10 + i * 30))
        
        pygame.display.flip()
    
    def run(self):
        """Main game loop"""
        while self.running and not self.found:
            # Reset balls every 1000 iterations
            if self.iteration % 1000 == 0 and self.iteration > 0:
                self.update_velocity_range()
                self.reset_balls()
            
            # Handle events
            self.handle_events()
            
            # Update physics
            self.update_physics()
            
            # Search for Bitcoin address
            self.search_bitcoin_address()
            
            # Draw everything
            self.draw()
            
            # Control frame rate
            self.clock.tick(60)
            
            # Increment iteration counter
            self.iteration += 1
        
        # Stop music before quitting
        if self.music_loaded:
            pygame.mixer.music.stop()
        
        pygame.quit()
        
        if self.found:
            print("Target address found! Check 'found.txt' for details.")
        else:
            print("Game ended without finding target address.")


def main():
    """Entry point"""
    game = BallGame()
    game.run()


if __name__ == "__main__":
    main()
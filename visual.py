import random
import pygame
import secp256k1 as ice

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 600
BALL_RADIUS = 10
INITIAL_BALL_COUNT = 72
TARGET_ADDRESS = '12VVRNPi4SJqUTsp6FmqDqY5sGosDtysn4'

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Initialize screen and font
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Interactive Ball Game - Bitcoin Address Search")
font = pygame.font.Font(None, 36)
small_font = pygame.font.Font(None, 24)


class Ball:
    """Represents a bouncing ball with physics properties"""
    
    def __init__(self, x, y, radius, velocity_range):
        self.x = x
        self.y = y
        self.radius = radius
        self.dx = random.uniform(velocity_range[0], velocity_range[1])
        self.dy = random.uniform(velocity_range[0], velocity_range[1])
        self.gravity = 0
        self.friction = 1
        
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
        
        # Wall collisions
        if self.x - self.radius <= 0 or self.x + self.radius >= SCREEN_WIDTH:
            self.dx *= -1
            self.x = max(self.radius, min(SCREEN_WIDTH - self.radius, self.x))
            
        if self.y - self.radius <= 0 or self.y + self.radius >= SCREEN_HEIGHT:
            self.dy *= -1
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
        """Draw the ball on the surface"""
        pygame.draw.circle(surface, RED, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, BLACK, (int(self.x), int(self.y)), self.radius, 1)


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
        self.reset_balls()
        
    def reset_balls(self):
        """Create new set of balls with updated velocity range"""
        self.balls = []
        for _ in range(INITIAL_BALL_COUNT):
            ball = Ball(
                x=random.randint(50, SCREEN_WIDTH - 50),
                y=random.randint(50, SCREEN_HEIGHT - 50),
                radius=BALL_RADIUS,
                velocity_range=self.velocity_range
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
        screen.fill(WHITE)
        
        # Draw balls
        for ball in self.balls:
            ball.draw(screen)
        
        # Draw UI
        score_text = font.render(f"Score: {self.score}", True, BLACK)
        screen.blit(score_text, (10, 10))
        
        iteration_text = small_font.render(f"Iteration: {self.iteration}", True, BLACK)
        screen.blit(iteration_text, (10, 50))
        
        velocity_text = small_font.render(
            f"Velocity Range: [{self.velocity_range[0]}, {self.velocity_range[1]}]", 
            True, BLACK
        )
        screen.blit(velocity_text, (10, 80))
        
        # Draw instructions
        instructions = [
            "Click on balls to launch them!",
            f"Searching for: {TARGET_ADDRESS[:20]}..."
        ]
        for i, instruction in enumerate(instructions):
            inst_text = small_font.render(instruction, True, BLUE)
            screen.blit(inst_text, (SCREEN_WIDTH - 400, 10 + i * 30))
        
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
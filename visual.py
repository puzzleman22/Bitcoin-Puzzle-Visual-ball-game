import random
import string
import pygame
import secp256k1 as ice

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 600

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Font
FONT = pygame.font.Font(None, 36)

# Screen setup
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Interactive Game with Hex String")
def increase_hex_string3(hex_string):
    # Precompute a translation table for all hex digits
    translation_table = str.maketrans("0123456789abcdef", "123456789abcdef0")
    return hex_string.translate(translation_table)
def shift_string_left(s, n):
    n = n % len(s)
    return s[n:] + s[:n]
def inverse_binary_string(binary_string):
    # Ensure the input is valid
    if not all(char in '01' for char in binary_string):
        raise ValueError("Input string must contain only '0' and '1'")
    
    # Invert the binary string
    return ''.join('1' if char == '0' else '0' for char in binary_string)

class Ball:
    def __init__(self, x, y, radius, random_instance, min2, max2):
        self.x = x
        self.y = y
        self.radius = radius
        self.direction = 1
        self.gravity = 0
        self.friction = 1
        self.random_instance = random_instance
        self.hex2 = random.randint(0, 15)
        self.dx = self.random_instance.randint(min2, max2)
        self.dy = self.random_instance.randint(min2, max2)
    def generate_hex_string(self):
        
        speed = int((self.x ** 2 + self.y ** 2) ** 0.5)
        
        return hex(speed % 16)[2:]
    def bin2(self):
        
        speed = int((self.x ** 2 + self.y ** 2) ** 0.5)
        return hex(speed % 2)[2:]
    def move(self):
        self.dy += self.gravity
        self.x += self.dx
        self.y += self.dy
        self.dx *= self.friction
        self.dy *= self.friction
        if self.x - self.radius <= 0 or self.x + self.radius >= SCREEN_WIDTH:
            self.dx *= -1
            
        if self.y - self.radius <= 0 or self.y + self.radius >= SCREEN_HEIGHT:
            self.dy *= -1
            
            
            
        self.x = max(self.radius, min(SCREEN_WIDTH - self.radius, self.x))
        self.y = max(self.radius, min(SCREEN_HEIGHT - self.radius, self.y))

        

    def collide_with(self, other):
        distance = ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
        if distance < self.radius + other.radius:
            overlap = 0.5 * (self.radius + other.radius - distance + 1)
            if distance <= 0:
                distance = 1
            nx = (other.x - self.x) / distance
            ny = (other.y - self.y) / distance

            self.x -= overlap * nx
            self.y -= overlap * ny
            other.x += overlap * nx
            other.y += overlap * ny

            p = 2 * (self.dx * nx + self.dy * ny - other.dx * nx - other.dy * ny) / 2
            self.dx -= p * nx
            self.dy -= p * ny
            other.dx += p * nx
            other.dy += p * ny
    def draw(self):
        pygame.draw.circle(screen, RED, (int(self.x), int(self.y)), self.radius)

    def handle_click(self, mouse_x, mouse_y):
        distance = ((mouse_x - self.x) ** 2 + (mouse_y - self.y) ** 2) ** 0.5
        if distance <= self.radius:
            direction_x = self.x - mouse_x
            direction_y = self.y - mouse_y
            magnitude = (direction_x ** 2 + direction_y ** 2) ** 0.5
            self.dx = (direction_x / magnitude) * self.random_instance.uniform(10, 100)
            self.dy = (direction_y / magnitude) * self.random_instance.uniform(10, 100)
            return True
        return False

def interactive_game():
    clock = pygame.time.Clock()
    running = True
    score = 0
    c = 0
    size = 72
    target = '12VVRNPi4SJqUTsp6FmqDqY5sGosDtysn4'
    found = False 
    min2 = -1
    max2 = 1
    while running:
    
        if c % 1000 == 0:
            balls = []
            min2 += -1
            max2 += 1
            for i in range(size):
                random_instance = random.Random()
                ball = Ball(
                    x=random.randint(50, SCREEN_WIDTH - 50),
                    y=random.randint(50, SCREEN_HEIGHT - 50),
                    radius=10,
                    random_instance=random_instance,
                    min2=min2,
                    max2=max2
                )
                balls.append(ball)
    
        screen.fill(WHITE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = event.pos
                for ball in balls:
                    if ball.handle_click(mouse_x, mouse_y):
                        score += 1

        for i, ball in enumerate(balls):
            for other in balls[i + 1:]:
                ball.collide_with(other)

        for ball in balls:
            ball.move()
            ball.draw()

        #hex2 = ''.join(ball.generate_hex_string() for ball in balls)
        bin2 = ''.join(ball.bin2() for ball in balls)
        for inv in range(2):
            for z in range(2):
                for y in range(size):
                    pp = int(bin2, 2)
                    hex2 = hex(pp)[2:].zfill(size // 4)
                    for x in range(16):
                        p = int('1' + hex2, 16)
                        addr = ice.privatekey_to_address(0, True, p)
                        if x == 0 and y == 0 and z == 0 and inv == 0:
                            print(str(c) + ' - ' + hex(p)[2:] + ' - ' + addr)
                        if addr == target: 
                            print(hex(p)[2:] + ' - ' + bin2 + ' -> ' + addr)
                            print('found')
                            found = True 
                            with open('found.txt', 'a') as file:
                                file.write(hex(p)[2:] + ' -> ' + addr)
                            break
                        hex2 = increase_hex_string3(hex2)
                    bin2 = shift_string_left(bin2, 1)
                bin2 = bin2[::-1]
            bin2 = inverse_binary_string(bin2)
        score_text = FONT.render(f"Score: {score}", True, BLACK)
        screen.blit(score_text, (10, 10))

        pygame.display.flip()
        clock.tick(60)
        if found:
            break
            
        c += 1
    pygame.quit()

if __name__ == "__main__":
    interactive_game()

import pygame
import math

pygame.init()

# Screen setup
screen_width, screen_height = 800, 600
screen = pygame.display.set_mode((screen_width, screen_height))
clock = pygame.time.Clock()
fps = 60

# Colors
white = (255, 255, 255)
black = (0, 0, 0)
red = (255, 0, 0)

# Square properties
square_size = 100
square_x, square_y = 0, 0
fall_speed = 5
landed = False
split = False

# Triangle properties
triangle1_x, triangle1_y = 0, 0
triangle2_x, triangle2_y = 0, 0
triangle_speed = 7
triangle_fly_off = False

running = True
while running:
    clock.tick(fps)
    screen.fill(white)
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    if not landed:
        square_y += fall_speed
        if square_y + square_size >= screen_height // 2:
            landed = True
            split = True
            triangle1_x, triangle1_y = square_x, square_y
            triangle2_x, triangle2_y = square_x, square_y
    
    if landed and not split:
        pygame.draw.rect(screen, red, (square_x, square_y, square_size, square_size))
    
    if split:
        triangle1 = [(triangle1_x, triangle1_y), (triangle1_x + square_size, triangle1_y), (triangle1_x, triangle1_y + square_size)]
        triangle2 = [(triangle2_x + square_size, triangle2_y), (triangle2_x, triangle2_y + square_size), (triangle2_x + square_size, triangle2_y + square_size)]
        
        pygame.draw.polygon(screen, red, triangle1)
        pygame.draw.polygon(screen, red, triangle2)
        
        if not triangle_fly_off:
            triangle2_y += fall_speed
            if triangle2_y + square_size >= screen_height:
                triangle_fly_off = True
        else:
            triangle1_x += triangle_speed
            triangle1_y -= triangle_speed
            if triangle1_x > screen_width or triangle1_y < 0:
                split = False
    
    pygame.display.update()

pygame.quit()

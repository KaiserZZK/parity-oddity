import random
import pygame
import pickle
from os import path


pygame.init()

clock = pygame.time.Clock()
fps = 60

#game window
tile_size = 50
cols = 20
margin = 100
screen_width, screen_height = 1000, 800 # same as main game
# screen_width = tile_size * cols
# screen_height = (tile_size * cols) + margin

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Level Editor')


#load images
bg_img = pygame.image.load("assets/img/Background/Gray.png")
bg_tile_height = bg_img.get_height()
bg_tile_width = bg_img.get_width()

dirt_imgs = [pygame.image.load(f'assets/img/Terrain/dirt_{i}.png') for i in range(1,7)]
grass_img = pygame.image.load('assets/img/Terrain/grass.png')
blob_img = pygame.image.load('assets/img/Enemy/blob.png')
platform_x_img = pygame.image.load('assets/img/Terrain/platform_x.png')
platform_y_img = pygame.image.load('assets/img/Terrain/platform_y.png')
lava_imgs = [pygame.image.load(f'assets/img/Enemy/dark_nuggets_{i}.png') for i in range(1,7)]
coin_img = pygame.image.load('assets/img/Item/blue_nuggets.png')
exit_img = pygame.image.load('assets/img/Terrain/exit.png')
save_img = pygame.image.load('assets/img/Button/save_btn.png')
load_img = pygame.image.load('assets/img/Button/load_btn.png')


#define game variables
clicked = False
level = 1

#define colours
white = (255, 255, 255)
green = (144, 201, 120)

font = pygame.font.SysFont('Futura', 24)

#function for outputting text onto the screen
def draw_text(text, font, text_col, x, y):
	img = font.render(text, True, text_col)
	screen.blit(img, (x, y))

def draw_grid(scale):
	for c in range(cols+1):
		#vertical lines
		pygame.draw.line(screen, white, (c * tile_size * scale, 0), (c * tile_size * scale, screen_height - margin))
		#horizontal lines
		pygame.draw.line(screen, white, (0, c * tile_size * scale), (screen_width, c * tile_size * scale))

def tile_variant(row, col):
    return (hash((row, col)) % 6) + 1

def draw_world(map_height, map_width, scale_factor, dx, dy):
	map_rows = map_height // tile_size
	map_cols = map_width // tile_size 
	for row in range(map_rows):
		for col in range(map_cols):
			if world_data[row][col] > 0:
				if world_data[row][col] == 1:
					#dirt blocks
					i = tile_variant(row, col)
					img = pygame.transform.scale(dirt_imgs[i-1], (tile_size * scale_factor, tile_size * scale_factor))
					screen.blit(img, (col * tile_size * scale_factor + dx, row * tile_size * scale_factor + dy))
				if world_data[row][col] == 2:
					#grass blocks
					img = pygame.transform.scale(grass_img, (tile_size * scale_factor, tile_size * scale_factor))
					screen.blit(img, (col * tile_size * scale_factor + dx, row * tile_size * scale_factor + dy))
				if world_data[row][col] == 3:
					#enemy blocks
					img = pygame.transform.scale(blob_img, (tile_size * scale_factor, int(tile_size * 0.75) * scale_factor))
					screen.blit(img, (col * tile_size * scale_factor + dx, (row * tile_size + (tile_size * 0.25)) * scale_factor + dy))
				if world_data[row][col] == 4:
					#horizontally moving platform
					img = pygame.transform.scale(platform_x_img, (tile_size, tile_size // 2))
					screen.blit(img, (col * tile_size, row * tile_size))
				if world_data[row][col] == 5:
					#vertically moving platform
					img = pygame.transform.scale(platform_y_img, (tile_size, tile_size // 2))
					screen.blit(img, (col * tile_size, row * tile_size))
				if world_data[row][col] == 6:
					#lava
					i = tile_variant(row, col)
					img = pygame.transform.scale(lava_imgs[i-1], (tile_size * scale_factor, (tile_size // 2) * scale_factor))
					screen.blit(img, (col * tile_size * scale_factor + dx, (row * tile_size + (tile_size // 2)) * scale_factor + dy))
				if world_data[row][col] == 7:
					#coin
					img = pygame.transform.scale(coin_img, ((tile_size // 2) * scale_factor, (tile_size // 2) * scale_factor))
					screen.blit(img, ((col * tile_size + (tile_size // 4)) * scale_factor + dx, (row * tile_size + (tile_size // 4)) * scale_factor + dy))
				if world_data[row][col] == 8:
					#exit
					img = pygame.transform.scale(exit_img, (tile_size * scale_factor, int(tile_size * 1.5) * scale_factor))
					screen.blit(img, ((col * tile_size) * scale_factor + dx, (row * tile_size - (tile_size // 2)) * scale_factor + dy))



class Button():
	def __init__(self, x, y, image):
		self.image = image
		self.rect = self.image.get_rect()
		self.rect.topleft = (x, y)
		self.clicked = False

	def draw(self):
		action = False

		#get mouse position
		pos = pygame.mouse.get_pos()

		#check mouseover and clicked conditions
		if self.rect.collidepoint(pos):
			if pygame.mouse.get_pressed()[0] == 1 and self.clicked == False:
				action = True
				self.clicked = True

		if pygame.mouse.get_pressed()[0] == 0:
			self.clicked = False

		#draw button
		screen.blit(self.image, (self.rect.x, self.rect.y))

		return action

#create load and save buttons
save_button = Button(screen_width // 2 - 150, screen_height - 80, save_img)
load_button = Button(screen_width // 2 + 50, screen_height - 80, load_img)

# decouple map and screen sizes
map_height, map_width = 400, 300 # screen_height, screen_width 
input_rect = pygame.Rect(200, 200, 140, 32)
text = "" 

#create empty tile list
world_data = []
for row in range(map_height // tile_size):
	r = [0] * (map_width // tile_size )
	world_data.append(r)

def expand_world_data(world_data, lx, rx, ly, ry):
	lx //= tile_size
	rx //= tile_size 
	ly //= tile_size 
	ry //= tile_size 
	# Pad height
	world_data = [[0]*len(world_data[0])]*ly + world_data + [[0]*len(world_data[0])]*ry
	# Pad width 
	for i in range(len(world_data)):
		world_data[i] = [0]*lx + world_data[i] + [0]*rx
	return world_data

def shrink_world_data(world_data, lx, rx, ly, ry):
	lx //= tile_size
	rx //= tile_size 
	ly //= tile_size 
	ry //= tile_size 
	# Pad height 
	if ry < 0:
		world_data = world_data[abs(ly):ry]
	else: 
		world_data = world_data[abs(ly):]
	# Pad width 
	for i in range(len(world_data)):
		if rx < 0:
			world_data[i] = world_data[i][abs(lx):rx]
		else:
			world_data[i] = world_data[i][abs(lx):]
	return world_data

scale_factor = 1.0
offset_x, offset_y = 0, 0
offset_delta = 20

#main game loop
run = True
while run:

	clock.tick(fps)

	#draw background
	screen.fill(green)
	for y in range(0, map_height, bg_tile_height):
		for x in range(0, map_width, bg_tile_width): 
			bg_img = pygame.transform.scale(bg_img, (bg_tile_width * scale_factor, bg_tile_height * scale_factor))
			screen.blit(bg_img, (x * scale_factor + offset_x, y * scale_factor + offset_y))

	#load and save level
	if save_button.draw():
		#save level data
		pickle_out = open(f'level{level}_data', 'wb')
		pickle.dump(world_data, pickle_out)
		pickle_out.close()
	if load_button.draw():
		#load in level data
		if path.exists(f'level{level}_data'):
			pickle_in = open(f'level{level}_data', 'rb')
			world_data = pickle.load(pickle_in)
			map_height = len(world_data) * tile_size
			map_width = len(world_data[0]) * tile_size

	#show the grid and draw the level tiles
	draw_grid(scale_factor)
	draw_world(map_height=map_height, map_width=map_width, scale_factor=scale_factor, dx=offset_x, dy=offset_y)


	#text showing current level
	draw_text(f'Current modification data input {text}', font, white, tile_size, screen_height - 80)
	draw_text(f'Height {map_height} Width {map_width} tile size {tile_size}', font, white, tile_size, screen_height - 60)
	draw_text('{level} Press UP or DOWN to change level', font, white, tile_size, screen_height - 40)

	#event handler
	for event in pygame.event.get():
		#quit game
		if event.type == pygame.QUIT:
			run = False
		#mouseclicks to change tiles
		if event.type == pygame.MOUSEBUTTONDOWN and clicked == False:
			clicked = True 
			pos = pygame.mouse.get_pos()
			x = int((pos[0] - offset_x) // (tile_size * scale_factor)) 
			y = int((pos[1] + offset_y) // (tile_size * scale_factor)) 
			#check that the coordinates are within the tile area
			if x < (map_width//tile_size) and y < (map_height//tile_size):
				#update tile value
				if pygame.mouse.get_pressed()[0] == 1:
					world_data[y][x] += 1
					if world_data[y][x] > 8:
						world_data[y][x] = 0
				elif pygame.mouse.get_pressed()[2] == 1:
					world_data[y][x] -= 1
					if world_data[y][x] < 0:
						world_data[y][x] = 8
		if event.type == pygame.MOUSEBUTTONUP:
			clicked = False
		#up and down key presses to change level number
		if event.type == pygame.KEYDOWN:
			# Originally used for level increment; we change it to panning instead
			if event.key == pygame.K_UP:
				offset_y += offset_delta * scale_factor
			elif event.key == pygame.K_DOWN:
				offset_y -= offset_delta * scale_factor
			elif event.key == pygame.K_LEFT:
				offset_x += offset_delta * scale_factor
			elif event.key == pygame.K_RIGHT:
				offset_x -= offset_delta * scale_factor
			elif event.key == pygame.K_RETURN:
				lx, rx, ly, ry = text.split(",")
				lx, rx, ly, ry = int(lx), int(rx), int(ly), int(ry)
				if lx<0 or rx<0 or ly<0 or ry<0:
					world_data = shrink_world_data(world_data, lx, rx, ly, ry)
				else:
					world_data = expand_world_data(world_data , lx, rx, ly, ry)
				map_height = len(world_data) * tile_size
				map_width = len(world_data[0]) * tile_size
				text = ""
	
			elif event.key == pygame.K_BACKSPACE:
				text =  text[:-1]
			else:
				text += event.unicode 
	
		elif event.type == pygame.MOUSEBUTTONDOWN:
			if event.button == 4:  # Scrolling up
				scale_factor += 0.1
			elif event.button == 5:  # Scrolling down
				scale_factor -= 0.1
	
		pygame.display.flip()

	#update game display window
	pygame.display.update()

pygame.quit()
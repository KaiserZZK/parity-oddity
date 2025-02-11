import pygame 
import math 
from pygame.locals import * 
from pygame import mixer
import pickle 
from os import path

pygame.mixer.pre_init(44100, -16, 2, 512)
mixer.init()
pygame.init()

clock = pygame.time.Clock()
fps = 60

screen_width = 1000
screen_height = 800

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Untitled Gem Platformer')

# Define font
font = pygame.font.SysFont('Bauhaus 93', 70)
font_score = pygame.font.SysFont('Bauhaus 93', 30)


# Define game vairables 
tile_size = 50
game_over = 0
main_menu = False # disable main menu 
level = 1
max_levels = 7
score = 0

# Define colors
white = (255, 255, 255)
blue = (0, 0, 255)


# Load visual assets
bg_img = pygame.image.load("assets/img/Background/Blue.png")
bg_tile_height = bg_img.get_height()
bg_tile_width = bg_img.get_width()

restart_img = pygame.image.load('assets/img/Button/restart_btn.png')
start_img = pygame.image.load('assets/img/Button/start_btn.png')
exit_img = pygame.image.load('assets/img/Button/exit_btn.png')

# Load audio assets
pygame.mixer.music.load('assets/aud/music.wav')
pygame.mixer.music.play(-1, 0.0, 5000)
coin_fx = pygame.mixer.Sound('assets/aud/coin.wav')
coin_fx.set_volume(0.5)
jump_fx = pygame.mixer.Sound('assets/aud/jump.wav')
jump_fx.set_volume(0.5)
game_over_fx = pygame.mixer.Sound('assets/aud/game_over.wav')
game_over_fx.set_volume(0.5)

def draw_text(text, font, text_col, x, y):
	img = font.render(text, True, text_col)
	screen.blit(img, (x, y))

#function to reset level
def reset_level(level):
	player.reset(100, screen_height - 130)
	blob_group.empty()
	trap_group.empty()
	exit_group.empty()

	#load in level data and create world
	if path.exists(f'level{level}_data'):
		pickle_in = open(f'level{level}_data', 'rb')
		world_data = pickle.load(pickle_in)
	world = World(world_data)

	return world

class Button():
	def __init__(self, x, y, image):
		self.image = image
		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y
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
		screen.blit(self.image, self.rect)

		return action

def tile_variant(row, col):
	return (hash((row, col)) % 6) + 1

class World():
	def __init__(self, data):
		self.tile_list = []

		#load images
		dirt_imgs = [pygame.image.load(f'assets/img/Terrain/dirt_{i}.png') for i in range(1,7)]
		grass_img = pygame.image.load('assets/img/Terrain/grass.png')

		row_count = 0
		for row in data:
			col_count = 0
			for tile in row:
				if tile == 1:
					img = pygame.transform.scale(dirt_imgs[tile_variant(row_count,col_count)-1], (tile_size, tile_size))
					img_rect = img.get_rect()
					img_rect.x = col_count * tile_size
					img_rect.y = row_count * tile_size
					tile = (img, img_rect)
					self.tile_list.append(tile)
				if tile == 2:
					img = pygame.transform.scale(grass_img, (tile_size, tile_size))
					img_rect = img.get_rect()
					img_rect.x = col_count * tile_size
					img_rect.y = row_count * tile_size
					tile = (img, img_rect)
					self.tile_list.append(tile)
				if tile == 3:
					blob = Enemy(col_count * tile_size, row_count * tile_size + 15)
					blob_group.add(blob)        
				if tile == 6:
					trap = Trap(col_count * tile_size, row_count * tile_size + (tile_size // 2))
					trap_group.add(trap)
				if tile == 7:
					coin = Coin(col_count * tile_size + (tile_size // 2), row_count * tile_size + (tile_size // 2))
					coin_group.add(coin)
				if tile == 8:
					exit = Exit(col_count * tile_size, row_count * tile_size - (tile_size // 2))
					exit_group.add(exit)
				col_count += 1
			row_count += 1

	def draw(self, offset_x):
		for tile in self.tile_list:
			screen.blit(tile[0], (tile[1].x - offset_x, tile[1].y))

class Enemy(pygame.sprite.Sprite):
	def __init__(self, x, y):
		pygame.sprite.Sprite.__init__(self)
		self.image = pygame.image.load('assets/img/Enemy/blob.png')
		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y
		self.move_direction = 1
		self.move_counter = 0

	def update(self):
		self.rect.x += self.move_direction
		self.move_counter += 1
		if abs(self.move_counter) > 50:
			self.move_direction *= -1
			self.move_counter *= -1

# @zkzh bugged--these objects won't move w. offset cuz they lack a draw method 

# @zkzh offset is also bugged--if you go too far left, camera wont follow you back 
class Trap(pygame.sprite.Sprite):
	def __init__(self, x, y):
		pygame.sprite.Sprite.__init__(self)
		imgs = [pygame.image.load(f'assets/img/Enemy/dark_nuggets_{i}.png') for i in range(1,7)]
		self.image = pygame.transform.scale(imgs[tile_variant(x,y)-1], (tile_size, tile_size // 2))
		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y
  
class Coin(pygame.sprite.Sprite):
	def __init__(self, x, y):
		pygame.sprite.Sprite.__init__(self)
		img = pygame.image.load('assets/img/Item/blue_nuggets.png')
		self.image = pygame.transform.scale(img, (tile_size // 2, tile_size // 2))
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
  
class Exit(pygame.sprite.Sprite):
	def __init__(self, x, y):
		pygame.sprite.Sprite.__init__(self)
		img = pygame.image.load('assets/img/Terrain/exit.png')
		self.image = pygame.transform.scale(img, (tile_size, int(tile_size * 1.5)))
		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y

class Player():
	def __init__(self, x, y):
		self.reset(x, y) 
  

	def crash_land(self):
		self.vel_x = 100
		dx = 0
		dy = 0  

		#add gravity
		self.vel_y += 1
		
		dy += self.vel_y

		#check for collision
		self.in_air = True
		for tile in world.tile_list:
			#check for collision in x direction
			if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
				dx = 0
			#check for collision in y direction
			if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
				print("boom!")
				self.image = None 
				return True  

		#update player coordinates
		self.rect.x += dx
		self.rect.y += dy

		#draw player onto screen
		screen.blit(self.image, (self.rect.x - offset_x, self.rect.y))
		return False 


	def update(self, game_over, offset_x):
		dx = 0
		dy = 0
		walk_cooldown = 5

		jump = False 
		double_jump = False 
		# @zkzh handld mirroring for speical sprites (actually just flying)
		if game_over == 0:
			#get keypresses
			key = pygame.key.get_pressed()
			if key[pygame.K_SPACE] and self.jumped == False and (self.in_air == False or (self.in_air and self.jump_count < 2)):
				if (self.in_air and self.jump_count < 2):
					double_jump = True 
				else: 
					jump = True 
				jump_fx.play()
				self.vel_y = -15
				self.jumped = True
				self.jump_count += 1
			if key[pygame.K_SPACE] == False:
				self.jumped = False
			if key[pygame.K_LEFT]:
				self.vel_x = -1
				dx -= 5
				self.counter += 1
				self.direction = -1
			if key[pygame.K_RIGHT]:
				self.vel_x = 1
				dx += 5
				self.counter += 1
				self.direction = 1
			if key[pygame.K_LEFT] == False and key[pygame.K_RIGHT] == False:
				self.counter = 0
				self.index = 0
				if self.direction == 1:
					self.image = self.images_right[self.index]
				if self.direction == -1:
					self.image = self.images_left[self.index]


			#handle animation
			if double_jump:
				double_jump_img = pygame.image.load(f'assets/img/Player/double_jump.png')
				self.image = pygame.transform.scale(double_jump_img, (80, 80)) 
				double_jump = False 
			elif jump:
				jump_img = pygame.image.load(f'assets/img/Player/regular_jump.png')
				self.image = pygame.transform.scale(jump_img, (80, 80))
				jump = False 
			else:
				if self.counter > walk_cooldown:
					self.counter = 0	
					self.index += 1
					if self.index >= len(self.images_right):
						self.index = 0
				if self.direction == 1:
					if self.in_air:
						self.image = self.fly_images_right[self.index]
					else:
						self.image = self.images_right[self.index]
				if self.direction == -1:
					if self.in_air:
						self.image = self.fly_images_left[self.index]
					else:
						self.image = self.images_left[self.index]


			#add gravity
			self.vel_y += 1
			if (key[pygame.K_RIGHT] or key[pygame.K_LEFT]) and self.jump_count >= 2:
				# glide
				if self.vel_y > .5:
					self.vel_y = .5
			else:
				if self.vel_y > 10:
					self.vel_y = 10
			dy += self.vel_y

			#check for collision
			self.in_air = True
			for tile in world.tile_list:
				#check for collision in x direction
				if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
					dx = 0
				#check for collision in y direction
				if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
					#check if below the ground i.e. jumping
					if self.vel_y < 0:
						dy = tile[1].bottom - self.rect.top
						self.vel_y = 0
					#check if above the ground i.e. falling
					elif self.vel_y >= 0:
						dy = tile[1].top - self.rect.bottom
						self.vel_y = 0
						self.in_air = False
					if self.jump_count > 0:
						print("landed...")
					self.jump_count = 0 
					
		
				#check for collision with enemies
				if pygame.sprite.spritecollide(self, blob_group, False):
					game_over = -1
					game_over_fx.play()

				# @zkzh this part is now effectively changed; implement drag behavior
				# #check for collision with trap
				# if pygame.sprite.spritecollide(self, trap_group, False):
				# 	game_over = -1
				# 	game_over_fx.play()
	 
				#check for collision with exit
				if pygame.sprite.spritecollide(self, exit_group, False):
					game_over = 1

			#update player coordinates
			self.rect.x += dx
			self.rect.y += dy

		elif game_over == -1:
			self.image = self.dead_image
			draw_text('GAME OVER!', font, blue, (screen_width // 2) - 200, screen_height // 2)
			if self.rect.y > 200:
				self.rect.y -= 5

		#draw player onto screen
		screen.blit(self.image, (self.rect.x - offset_x, self.rect.y))
  
		return game_over 

	def reset(self, x, y):
		self.images_right = []
		self.images_left = []
		self.fly_images_right = []
		self.fly_images_left = []
		self.index = 0
		self.counter = 0
		for num in range(1, 4):
			img_right = pygame.image.load(f'assets/img/Player/stein_red_new_{num}.png')
			img_right = pygame.transform.scale(img_right, (80, 80))
			img_left = pygame.transform.flip(img_right, True, False)
			self.images_right.append(img_right)
			self.images_left.append(img_left)
			fly_img_right = pygame.image.load(f'assets/img/Player/fly_{num}.png')
			fly_img_right = pygame.transform.scale(fly_img_right, (80, 80))
			fly_img_left = pygame.transform.flip(fly_img_right, True, False)
			self.fly_images_right.append(fly_img_right)
			self.fly_images_left.append(fly_img_left)
		self.dead_image = pygame.image.load('assets/img/Player/ghost.png')
		self.image = self.images_right[self.index]
		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y
		self.width = self.image.get_width()
		self.height = self.image.get_height()
		self.vel_x = 0 
		self.vel_y = 0
		self.jumped = False
		self.direction = 0
		self.in_air = True
		self.jump_count = 0

# Main game loop   
player = Player(100, screen_height - 800)
sqr = Player(1, screen_height - 800)
landed = False 
blob_group = pygame.sprite.Group()
trap_group = pygame.sprite.Group()
coin_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()

#create dummy coin for showing the score
score_coin = Coin(tile_size // 2, tile_size // 2)
coin_group.add(score_coin)

#load in level data and create world
if path.exists(f'level{level}_data'):
	pickle_in = open(f'level{level}_data', 'rb')
	world_data = pickle.load(pickle_in)

world = World(world_data)

restart_button = Button(screen_width // 2 - 50, screen_height // 2 + 100, restart_img)
start_button = Button(screen_width // 2 - 350, screen_height // 2, start_img)
exit_button = Button(screen_width // 2 + 150, screen_height // 2, exit_img)

offset_x = 0 
scroll_area_width = 200

run = True 

while run:
	
	clock.tick(fps)
	
	for y in range(0, screen_height, bg_tile_height):
		for x in range(0, screen_width, bg_tile_width): 
			screen.blit(bg_img, (x, y))
	
	if main_menu == True:
		if exit_button.draw():
			run = False
		if start_button.draw():
			main_menu = False
	else:
		world.draw(offset_x*5)

		if not landed: 
			landed = sqr.crash_land()

		if game_over == 0:
			blob_group.update()
   			#check if a coin has been collected
			if pygame.sprite.spritecollide(player, coin_group, True):
				score += 1
				coin_fx.play()
			draw_text('X ' + str(score), font_score, white, tile_size - 10, 10)
		
		blob_group.draw(screen)
		trap_group.draw(screen)
		coin_group.draw(screen)
		exit_group.draw(screen)

		game_over = player.update(game_over,  offset_x*5)
  
		# if (player.rect.right - offset_x >= screen_width)
		if ((player.rect.right - offset_x >= screen_width - scroll_area_width) and player.vel_x > 0) or (
				(player.rect.left - offset_x <= scroll_area_width) and player.vel_x < 0):
			# print("scroll should kick in")
			offset_x += player.vel_x
  
		# Lose condition met
		if game_over == -1:
			if restart_button.draw():
				world_data = []
				world = reset_level(level)
				game_over = 0

		# Level advance condition met  
		if game_over == 1:
			#reset game and go to next level
			level += 1
			if level <= max_levels:
				#reset level
				world_data = []
				world = reset_level(level)
				game_over = 0
			else:
				draw_text('YOU WIN!', font, blue, (screen_width // 2) - 140, screen_height // 2)
				if restart_button.draw():
					level = 1
					#reset level
					world_data = []
					world = reset_level(level)
					game_over = 0

	
	for event in pygame.event.get():
		if event.type == pygame.QUIT:
			run = False
			
	pygame.display.update() 
			

pygame.quit()
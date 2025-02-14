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
final_map_height = 2000
final_map_width = 2800

screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('%')

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
# @zkzh add some, if not all gathered new SFXs
# pygame.mixer.music.play(-1, 0.0, 5000) # disabled for now; annoying af
coin_fx = pygame.mixer.Sound('assets/aud/blue_nugget.wav')
coin_fx.set_volume(0.5)
jump_fx = pygame.mixer.Sound('assets/aud/jump.wav')
jump_fx.set_volume(0.5)
game_over_fx = pygame.mixer.Sound('assets/aud/game_over.wav')
game_over_fx.set_volume(0.5) 

# Some global vars that track more complex player actions; for instructions display 
global glide_ever_used
glide_ever_used = False 
global ever_changed
ever_changed = False 
global ever_detransformed
ever_detransformed = False 
change_1_viewed = False 
change_2_viewed = False 

def draw_text(text, font, text_col, x, y):
	img = font.render(text, True, text_col)
	screen.blit(img, (x, y))

#function to reset level
def reset_level(level):
	player.reset(100, screen_height - 130)
	blob_group.empty()
	dark_nugget_group.empty()
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
		blue_id = 1
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
					kid_spawn_points.append([col_count * tile_size, row_count * tile_size, True])
				if tile == 3:
					blob = BlueNPC(blue_id, col_count * tile_size, row_count * tile_size)
					blob_group.add(blob)
					blue_id += 1
				if tile == 6:
					dark_nugget = DarkNugget(col_count * tile_size, row_count * tile_size + (tile_size // 2))
					dark_nugget_group.add(dark_nugget)
				if tile == 7:
					coin = Coin(col_count * tile_size + (tile_size // 2), row_count * tile_size + (tile_size // 2))
					coin_group.add(coin)
				if tile == 8:
					kid_spawn_points.append([col_count * tile_size, row_count * tile_size, False])
				col_count += 1
			row_count += 1

	def draw(self, offset_x, offset_y):
		for tile in self.tile_list:
			screen.blit(tile[0], (tile[1].x - offset_x, tile[1].y - offset_y))

class BlueNPC(pygame.sprite.Sprite):
	def __init__(self, i, x, y):
		pygame.sprite.Sprite.__init__(self)
		# blue_sprite = pygame.image.load('assets/img/Enemy/blob.png')
		self.body_sprite = pygame.image.load(f'assets/img/NPC/normal_body_{i}.png')
		self.eyes_sprite = pygame.image.load(f'assets/img/NPC/normal_eyes_{i}.png')

		self.hidden_body_sprite = pygame.image.load(f'assets/img/NPC/normal_body_{i}_hidden.png')
		self.hidden_eyes_sprite = pygame.image.load(f'assets/img/NPC/normal_eyes_{i}_hidden.png')

		self.x_scale, self.y_scale = 2, 5
		self.hidden = False 
		self.cropped_height = 10 # @zkzh change this based on drawn NPC assets
		self.body_image, self.eyes_image = self.use_normal_sprites() 

		self.rect = self.body_image.get_rect()		
		self.rect.y = y - (self.scaled_body_height - tile_size) # make sure bottom is on floor
		self.rect.x = x
  
		self.hide_offset = 0 
  
		self.eye_gaze_offset_x, self.eye_gaze_offset_y = 0, 0
		self.move_direction = 1
		self.move_counter = 0
  
	def use_normal_sprites(self):
		self.scaled_body_width, self.scaled_body_height = self.body_sprite.get_width() * self.x_scale, self.body_sprite.get_height() * self.y_scale
		body_image = pygame.transform.scale(
			self.body_sprite, 
			(
				self.scaled_body_width,
				self.scaled_body_height
			)
		)
		scaled_eyes_width, scaled_eyes_height = self.eyes_sprite.get_width() * self.x_scale, self.eyes_sprite.get_height() * self.y_scale
		eyes_image = pygame.transform.scale(
			self.eyes_sprite, 
			(
				scaled_eyes_width,
				scaled_eyes_height
			)
		)
  
		return body_image, eyes_image
  
	def use_hidden_sprites(self):
		self.scaled_body_width, self.scaled_body_height = self.hidden_body_sprite.get_width() * self.x_scale, self.hidden_body_sprite.get_height() * self.y_scale
		body_image = pygame.transform.scale(
			self.hidden_body_sprite, 
			(
				self.scaled_body_width,
				self.scaled_body_height
			)
		)
		scaled_eyes_width, scaled_eyes_height = self.hidden_eyes_sprite.get_width() * self.x_scale, self.hidden_eyes_sprite.get_height() * self.y_scale
		eyes_image = pygame.transform.scale(
			self.hidden_eyes_sprite, 
			(
				scaled_eyes_width,
				scaled_eyes_height 
			)
		)

		return body_image, eyes_image

	def draw(self, offset_x, offset_y): 
		if self.hidden:
			self.body_image, self.eyes_image = self.use_hidden_sprites()
			
			screen.blit(self.body_image, (self.rect.x - offset_x, self.rect.y - offset_y + self.cropped_height * self.y_scale))
			screen.blit(
				self.eyes_image, 
				(
					self.rect.x - offset_x + self.eye_gaze_offset_x, 
					self.rect.y - offset_y + self.eye_gaze_offset_y + self.cropped_height * self.y_scale
				)
			)
		else:
			self.body_image, self.eyes_image = self.use_normal_sprites()
			
			screen.blit(self.body_image, (self.rect.x - offset_x, self.rect.y - offset_y))
			screen.blit(
				self.eyes_image, 
				(
					self.rect.x - offset_x + self.eye_gaze_offset_x, 
					self.rect.y - offset_y + self.eye_gaze_offset_y
				)
			)
  
	def update(self):
		player_proximity_x = player.rect.x - self.rect.x
		player_proximity_y = player.rect.y - self.rect.y
  
		self.eye_gaze_offset_x = player_proximity_x * .02
		self.eye_gaze_offset_y = player_proximity_y * .02
		hide_threshold_x, hide_threshold_y = 200, 100
		if abs(player_proximity_x) < hide_threshold_x and not self.hidden:
			self.hidden = True
			
			# @zkzh fancy this hide/unhide animation is tricky; screw it we use still image 
		elif abs(player_proximity_x) >= hide_threshold_x and self.hidden:
			self.hidden = False 
				# self.body_image, self.eyes_image = self.use_normal_sprites()
			# self.body_image, self.eyes_image = self.use_normal_sprites()
				# self.hide_offset = 0
				# while self.hide_offset < self.scaled_body_height:
				# 	self.hide_offset += .05
				# 	self.draw(0, self.hide_offset)
				# self.hide_offset = 0 
				# self.rect.y -= self.scaled_body_height

class Kid(pygame.sprite.Sprite):
	def __init__(self, x, y, follow_from_left):
		pygame.sprite.Sprite.__init__(self)
		# blue_sprite = pygame.image.load('assets/img/Enemy/blob.png')
		self.body_sprite = pygame.image.load(f'assets/img/NPC/kid_body.png')
		self.eyes_sprite = pygame.image.load(f'assets/img/NPC/kid_eyes.png')

		self.hidden_body_sprite = pygame.image.load(f'assets/img/NPC/kid_body_hidden.png')
		self.hidden_eyes_sprite = pygame.image.load(f'assets/img/NPC/kid_eyes_hidden.png')
  
		self.spawn_x = x
		self.follow_from_left = follow_from_left

		self.x_scale, self.y_scale = 2, 5
		self.hidden = False 
		self.follow_offset = 100 
		self.cropped_height = 10 # @zkzh change this based on drawn assets
		self.body_image, self.eyes_image = self.use_normal_sprites() 

		self.rect = self.body_image.get_rect()		
		self.rect.y = y - (self.scaled_body_height - tile_size) # make sure bottom is on floor
		self.rect.x = x
  
		self.hide_offset = 0 
  
		self.eye_gaze_offset_x, self.eye_gaze_offset_y = 0, 0
		self.move_direction = 1
		self.move_counter = 0
  
	def use_normal_sprites(self):
		self.scaled_body_width, self.scaled_body_height = self.body_sprite.get_width() * self.x_scale, self.body_sprite.get_height() * self.y_scale
		body_image = pygame.transform.scale(
			self.body_sprite, 
			(
				self.scaled_body_width,
				self.scaled_body_height
			)
		)
		scaled_eyes_width, scaled_eyes_height = self.eyes_sprite.get_width() * self.x_scale, self.eyes_sprite.get_height() * self.y_scale
		eyes_image = pygame.transform.scale(
			self.eyes_sprite, 
			(
				scaled_eyes_width,
				scaled_eyes_height
			)
		)
  
		return body_image, eyes_image
  
	def use_hidden_sprites(self):
		self.scaled_body_width, self.scaled_body_height = self.hidden_body_sprite.get_width() * self.x_scale, self.hidden_body_sprite.get_height() * self.y_scale
		body_image = pygame.transform.scale(
			self.hidden_body_sprite, 
			(
				self.scaled_body_width,
				self.scaled_body_height
			)
		)
		scaled_eyes_width, scaled_eyes_height = self.hidden_eyes_sprite.get_width() * self.x_scale, self.hidden_eyes_sprite.get_height() * self.y_scale
		eyes_image = pygame.transform.scale(
			self.hidden_eyes_sprite, 
			(
				scaled_eyes_width,
				scaled_eyes_height 
			)
		)

		return body_image, eyes_image

	def draw(self, offset_x, offset_y): 
		if self.hidden:
			self.body_image, self.eyes_image = self.use_hidden_sprites()
			
			screen.blit(self.body_image, (self.rect.x - offset_x, self.rect.y - offset_y + self.cropped_height * self.y_scale))
			screen.blit(
				self.eyes_image, 
				(
					self.rect.x - offset_x + self.eye_gaze_offset_x, 
					self.rect.y - offset_y + self.eye_gaze_offset_y + self.cropped_height * self.y_scale
				)
			)
		else:
			self.body_image, self.eyes_image = self.use_normal_sprites()
			
			screen.blit(self.body_image, (self.rect.x - offset_x, self.rect.y - offset_y))
			screen.blit(
				self.eyes_image, 
				(
					self.rect.x - offset_x + self.eye_gaze_offset_x, 
					self.rect.y - offset_y + self.eye_gaze_offset_y
				)
			)
   
	def walked_past(self, x):
		if self.follow_from_left: 
			# @zkzh change value as needed
			return (x - self.rect.x) >= 100
		else:
			return (self.rect.x - x) <= 100
  
	def update(self):
		player_proximity_x = player.rect.x - self.rect.x
		player_proximity_y = player.rect.y - self.rect.y
  
		self.eye_gaze_offset_x = player_proximity_x * .02
		self.eye_gaze_offset_y = player_proximity_y * .02
		hide_threshold_x, hide_threshold_y = 200, 100
		if abs(player_proximity_x) < hide_threshold_x and not self.hidden:
			self.hidden = True
			
			# @zkzh fancy this hide/unhide animation is tricky; screw it we use still image 
		elif abs(player_proximity_x) >= hide_threshold_x and self.hidden:
			self.hidden = False 
				# self.body_image, self.eyes_image = self.use_normal_sprites()
			# self.body_image, self.eyes_image = self.use_normal_sprites()
				# self.hide_offset = 0
				# while self.hide_offset < self.scaled_body_height:
				# 	self.hide_offset += .05
				# 	self.draw(0, self.hide_offset)
				# self.hide_offset = 0 
				# self.rect.y -= self.scaled_body_height


class DarkNugget(pygame.sprite.Sprite):
	def __init__(self, x, y):
		pygame.sprite.Sprite.__init__(self)
		imgs = [pygame.image.load(f'assets/img/Enemy/dark_nuggets_{i}.png') for i in range(1,7)]
		self.image = pygame.transform.scale(imgs[tile_variant(x,y)-1], (tile_size, tile_size // 2))
		self.rect = self.image.get_rect()
		self.rect.x = x
		self.rect.y = y
		self.dragging = False  # Flag to track if dragging
	
	def draw(self, offset_x, offset_y):
		screen.blit(self.image, (self.rect.x - offset_x, self.rect.y - offset_y))
  
	def drag(self):
		pos = pygame.mouse.get_pos()
		mouse_pressed = pygame.mouse.get_pressed()[0]  # Left mouse button

		if self.rect.collidepoint((pos[0]+offset_x, pos[1]+offset_y)):  # Check if mouse is over object
			if mouse_pressed and not self.dragging:
				self.dragging = True  # Start dragging
		
		if self.dragging:
			if mouse_pressed:
				self.rect.x, self.rect.y = pos[0]+offset_x, pos[1]+offset_y  # Update position
			else:
				self.dragging = False  # Stop dragging when mouse released
  
class Coin(pygame.sprite.Sprite):
	def __init__(self, x, y):
		pygame.sprite.Sprite.__init__(self)
		img = pygame.image.load('assets/img/Item/blue_nuggets.png')
		self.image = pygame.transform.scale(img, (tile_size // 2, tile_size // 2))
		self.rect = self.image.get_rect()
		self.rect.center = (x, y)
  
	def draw(self, offset_x, offset_y):
		screen.blit(self.image, (self.rect.x - offset_x, self.rect.y - offset_y))
		
  
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
  
	def telekinesis(self):
		global ever_changed
		ever_changed = True 
		piece = pygame.image.load(f'assets/img/Player/frozen.png')
		self.image = pygame.transform.scale(piece, (80, 80))
		screen.blit(self.image, (self.rect.x - offset_x, self.rect.y - offset_y))
		for nugget in dark_nugget_group:
			nugget.drag()
  
	def bye(self, vy, curr_rot):
		piece = pygame.image.load(f'assets/img/Player/rip.png')
		scaled = pygame.transform.scale(piece, (80, 80))
		self.image = pygame.transform.rotate(scaled, curr_rot)
  
		screen.blit(self.image, (self.rect.x - offset_x, self.rect.y - offset_y))
		self.rect.x += vy
		self.rect.y -= (vy - 0.2)
		return vy, curr_rot + 5
			
  
	def slide(self, speed):
		initial_sqr = pygame.image.load(f'assets/img/Player/oomfie.png')
		self.image = pygame.transform.scale(initial_sqr, (80, 80))
		screen.blit(self.image, (self.rect.x - offset_x, self.rect.y - offset_y))
		friction = 0.95
		speed *= friction
		while self.rect.x < 422:
			self.rect.x += speed
			return (speed, False)
		
		return (speed, True)
  

	def crash_land(self, fall_speed):
		initial_sqr = pygame.image.load(f'assets/img/Player/beginning_s.png')
		self.image = pygame.transform.scale(initial_sqr, (80, 80))
		self.vel_x = 100
		dx = 0
		dy = 0  

		#add gravity
		fall_speed += .005
		self.vel_y += fall_speed
		
		dy += self.vel_y

		#check for collision
		self.in_air = True
		for tile in world.tile_list:
			#check for collision in x direction
			if tile[1].colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
				dx = 0
			#check for collision in y direction
			if tile[1].colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
				self.image = None
				return (True, fall_speed)  

		#update player coordinates
		self.rect.x += dx
		self.rect.y += dy

		#draw player onto screen
		screen.blit(self.image, (self.rect.x - offset_x, self.rect.y - offset_y))
		return (False, fall_speed)


	def update(self, game_over, offset_x, offset_y):
		dx = 0
		dy = 0
		walk_cooldown = 5

		jump = False 
		double_jump = False 
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
				global glide_ever_used
				glide_ever_used = True 
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
					# if self.jump_count > 0:
					# 	print("landed...")
					self.jump_count = 0 
					
			for dark_nugget in dark_nugget_group:
				#check for collision in x direction
				nugget_rect = dark_nugget.rect
				if nugget_rect.colliderect(self.rect.x + dx, self.rect.y, self.width, self.height):
					dx = 0
				#check for collision in y direction
				if nugget_rect.colliderect(self.rect.x, self.rect.y + dy, self.width, self.height):
					#check if below the ground i.e. jumping
					if self.vel_y < 0:
						dy = nugget_rect.bottom - self.rect.top
						self.vel_y = 0
					#check if above the ground i.e. falling
					elif self.vel_y >= 0:
						dy = nugget_rect.top - self.rect.bottom
						self.vel_y = 0
						self.in_air = False
					# if self.jump_count > 0:
					# 	print("landed...")
					self.jump_count = 0 



			#update player coordinates
			self.rect.x += dx
			self.rect.y += dy

		elif game_over == -1:
			self.image = self.dead_image
			draw_text('GAME OVER!', font, blue, (screen_width // 2) - 200, screen_height // 2)
			if self.rect.y > 200:
				self.rect.y -= 5

		#draw player onto screen
		screen.blit(self.image, (self.rect.x - offset_x, self.rect.y - offset_y))
  
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
			fly_img_right = pygame.image.load(f'assets/img/Player/fly_new_{num}.png')
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
player = Player(51, 465) # spawn with sliding after fall; may change depending on map changes
sqr = Player(51, screen_height - 800)
flown_off = Player(51, 470)
blob_group = pygame.sprite.Group()
kid_clones = pygame.sprite.Group()
dark_nugget_group = pygame.sprite.Group()
coin_group = pygame.sprite.Group()
exit_group = pygame.sprite.Group()  

# Dev functions
text = "" 

frozen = False 

# Beginning sequence
landed = False 
fall_speed = 0
sliding_ended = False 
start_sliding_speed = 20
fly_vertical_speed = 8
fly_spin = 0 

# Instructions
teach_box_size = (300, 200)
instruction_lr_viewed = False 
instructuin_jump_viewed = False 
progressive_boxes_position = ()

# Kid
kid_spawn_points = []
kid_spawn_threshold = 100
current_clone = None 

#load in level data and create world
if path.exists(f'level{level}_data'):
	pickle_in = open(f'level{level}_data', 'rb')
	world_data = pickle.load(pickle_in)

world = World(world_data)

offset_x, offset_y = 0, 0 
scroll_area_width, scroll_area_height = 200, 160

run = True 

while run:
	# @zkzh REMOVE
	# print("Debugging: current positions at", player.rect.x, player.rect.y)
	
	clock.tick(fps)
	
	for y in range(0, screen_height, bg_tile_height):
		for x in range(0, screen_width, bg_tile_width): 
			screen.blit(bg_img, (x, y))
	
	world.draw(offset_x, offset_y)

	if not landed: 
		landed, fall_speed = sqr.crash_land(fall_speed)
	elif not sliding_ended:
		fly_vertical_speed, fly_spin = flown_off.bye(fly_vertical_speed, fly_spin)
		start_sliding_speed, sliding_ended = player.slide(start_sliding_speed)
	else:
		if not instruction_lr_viewed:
			instruction = pygame.image.load('assets/img/Tutorial/left_right.png')
			instruction = pygame.transform.scale(instruction, teach_box_size)
			screen.blit(instruction, (player.rect.x, player.rect.y-200))
		elif not instructuin_jump_viewed and player.rect.x >= 840:
			instruction = pygame.image.load('assets/img/Tutorial/jump.png')
			instruction = pygame.transform.scale(instruction, teach_box_size)
			screen.blit(instruction, (player.rect.x - offset_x - 200, player.rect.y - offset_y - 200))
		elif not glide_ever_used and player.rect.x >= 1160:
			instruction = pygame.image.load('assets/img/Tutorial/gliding.png')
			instruction = pygame.transform.scale(instruction, teach_box_size)
			screen.blit(instruction, (player.rect.x - offset_x - 200, player.rect.y - offset_y - 200))
		elif not ever_changed and player.rect.x >= 2112:
			instruction = pygame.image.load('assets/img/Tutorial/changing.png')
			instruction = pygame.transform.scale(instruction, teach_box_size)
			screen.blit(instruction, (player.rect.x - offset_x - 200, player.rect.y - offset_y - 200))
		elif frozen and (not ever_detransformed): 
			if (not change_1_viewed) and (not change_2_viewed):
				instruction = pygame.image.load('assets/img/Tutorial/changed_1.png')
			elif (not change_2_viewed):
				instruction = pygame.image.load('assets/img/Tutorial/changed_2.png')
			else:
				instruction = pygame.image.load('assets/img/Tutorial/changed_3.png')
			instruction = pygame.transform.scale(instruction, teach_box_size)
			screen.blit(instruction, (player.rect.x - offset_x - 200, player.rect.y - offset_y - 200))			
		if frozen == True:
			player.telekinesis()
		else:
			game_over = player.update(game_over, offset_x, offset_y)

	if game_over == 0:
		blob_group.update()
		kid_clones.update()
		#check if a coin has been collected
		if pygame.sprite.spritecollide(player, coin_group, True):
			score += 1
			coin_fx.play()
			frozen = True 
			
		# draw_text('X ' + str(score), font_score, white, tile_size - 10, 10)
  
	if len(kid_spawn_points) > 0:
		x, y, follow_from_left = kid_spawn_points[0]
		if current_clone is not None:
			if current_clone.walked_past(player.rect.x):
				current_clone = None			
		if (follow_from_left and (player.rect.x - x) >= kid_spawn_threshold) or ((follow_from_left==False) and (x - player.rect.x) >= kid_spawn_threshold):
			if current_clone == None:
				kx, ky, f = kid_spawn_points.pop(0)
				current_clone = Kid(kx, ky, f)
				kid_clones.add(current_clone)
	
	for npc in blob_group:
		npc.draw(offset_x, offset_y)
	for kid_clone in kid_clones:
		kid_clone.draw(offset_x, offset_y)
	for dark_nugget in dark_nugget_group:
		dark_nugget.draw(offset_x, offset_y)
	for coin in coin_group:
		coin.draw(offset_x, offset_y)
	exit_group.draw(screen)

	if ((player.rect.right - offset_x >= screen_width - scroll_area_width) and player.vel_x > 0) or (
			(player.rect.left - offset_x <= scroll_area_width) and player.vel_x < 0):
		offset_x += player.vel_x * 10

	if ((player.rect.top - offset_y >= screen_height - scroll_area_height) and player.vel_y > 0) or (
			(player.rect.bottom - offset_y <= scroll_area_height) and player.vel_y < 0):
		offset_y += player.vel_y * 2

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
		if event.type == pygame.KEYDOWN:	
			if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
				instruction_lr_viewed = True 
			if event.key == pygame.K_SPACE:
				instructuin_jump_viewed = True 
			if frozen and event.key == pygame.K_q:
				frozen = False 
				ever_detransformed = True 
			# @zkzh REMOVE super hacky shit for dev  
			if event.key == pygame.K_BACKSPACE:
				text =  text[:-1]
			elif event.key == pygame.K_p:
				print("coords you're about to get teleported to: ", text)
			elif event.key == pygame.K_h:
				coords = text.split(",")
				print("whoooosh--you're about to go to ", coords[0], coords[1])
				player.rect.x = int(coords[0])
				player.rect.y = int(coords[1])
				game_over = player.update(game_over, offset_x, offset_y)
				text = ""
			else:
				text += event.unicode
		elif event.type == pygame.MOUSEBUTTONDOWN:
			mouse_x, mouse_y = event.pos  # Get mouse position
			# Check if click is inside the rectangle
			if 517 <= mouse_x <= 517+teach_box_size[0]*2 and 90 <= mouse_y <= 90+teach_box_size[1]*2:
				if not change_1_viewed:
					change_1_viewed = True  
				elif not change_2_viewed:
					change_2_viewed = True 
			
	pygame.display.update() 
			

pygame.quit()
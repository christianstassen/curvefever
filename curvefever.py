import pygame
from pygame.locals import *
import numpy as np
import random
import copy

WHITE  = (255, 255, 255)
BLUE   = (  0,   0, 255)
GREEN  = (  0, 255,   0)
RED    = (255,   0,   0)
YELLOW = (255,   255,   0)
BLACK  = (0,   0,   0)

class Rect(pygame.sprite.Sprite):
    def __init__(self,x,y,width,height,dir,color):
        super().__init__()
        self.image = pygame.Surface([width, height])
        self.image.fill(color)
        self.rect = self.image.get_rect()

        self.rect.centerx = x
        self.rect.centery = y

class field:

    def __init__(self, nx, ny, thick, color):
        # Dimension of field
        self.nx    = nx
        self.ny    = ny
        # Thickness of boundary
        self.thick = thick
        # Color of boundary
        self.color = color

        # Boundaries                                     left top width height
        self.boundaries = {'left':    pygame.Rect(0, 0, self.thick, self.ny),                  # Left boundary
                         'top':     pygame.Rect(0, 0, self.nx, self.thick),                  # Top boundary
                         'right':   pygame.Rect(self.nx-self.thick, 0, self.thick, self.ny), # Right boundary
                         'bottom':  pygame.Rect(0, self.ny-self.thick, self.nx, self.thick)} # Bottom boundary

        self.item_counter = 0

    def draw_boundary(self, screen):
        # Loop through boundaries and draw them
        for boundary in self.boundaries:
            pygame.draw.rect(screen, self.color, self.boundaries[boundary])


class player(pygame.sprite.Sprite):

    def __init__(self, id, points, posx, posy, thick, speed, dir, dirspeed, color, controls):
        pygame.sprite.Sprite.__init__(self)
        # Player ID
        self.id = id
        # Player points
        self.points = points
        self.point_trigger = False
        # Player alive
        self.alive = True
        # Player position
        self.posx     = posx
        self.posy     = posy
        self.posx_old = posx
        self.posy_old = posy
        # Player thickness
        self.thick    = thick
        # The tracl each player leaves behind
        self.track    = pygame.sprite.Group()
        # Random number to dicide if gap is created
        self.track_gapcounter = 0
        self.no_gap           = 0
        self.min_no_gap       = 200
        self.max_no_gap       = 300
        self.orig_max_no_gap  = 300
        self.l_gap            = False
        self.gap_length       = 15
        # Player speed and direction
        self.speed     = speed
        self.dir       = dir
        self.dirspeed  = dirspeed
        # Player color
        self.color    = color
        # Player control
        self.controls = controls
        # Image
        self.rect  = Rect(self.posx-self.thick, self.posy-self.thick, self.thick*2, self.thick*2, self.dir, self.color)
        # No collisiosn zone
        self.len_nocollide = 5
        self.nocollide     = [self.rect] * self.len_nocollide
        # Item effect
        self.effects = []

    def update(self,screen,pressed,gamefield, players):

        # Update the player position
        self.update_pos()

        # Update the player direction
        self.update_dir(pressed)

        # Update the track
        self.update_track(screen)
        self.gap()

        # Update no collision zone
        self.update_no_collide(screen)

        # Check for colision
        self.collision_with_boundary(gamefield, screen)
        self.collision_with_player(players, screen)
        self.collision_with_track(players, screen)

        # Check for effects
        self.activate_effects(self.effects)
        self.cooldown_effects(self.effects)

        # Check if alive
        self.check_alive()

        # Draw the player
        self.draw(screen)

        # Get points
        self.get_points(players)

    def update_pos(self):
        # Keep direction between 0 and 360
        self.dir = self.dir % 360
        # Update the position
        self.posx_old = self.posx
        self.posy_old = self.posy
        self.posx = self.posx_old + self.speed*np.cos(np.deg2rad(self.dir))
        self.posy = self.posy_old + self.speed*np.sin(np.deg2rad(self.dir))

        self.rect = Rect(self.posx-self.thick, self.posy-self.thick, self.thick*2, self.thick*2, self.dir, self.color)


    def update_dir(self, pressed):
        if pressed[self.controls['left']]: self.dir -= self.dirspeed
        if pressed[self.controls['right']]: self.dir += self.dirspeed

    def draw(self,screen):
        pygame.draw.circle(screen, YELLOW, (int(self.rect.rect.centerx),int(self.rect.rect.centery)), self.thick)



    def gap(self):
        self.no_gap += 1 # Add something to the no gap counter
        # Make the gaps random, but definitely occur after a certain period
        if not self.l_gap and random.randint(1,101) == 1 and self.no_gap > self.min_no_gap or self.no_gap >= self.max_no_gap:
            self.l_gap = True

        if self.l_gap:
            self.track_gapcounter += 1 # Count the length of gaps

        # Turn the gap of after the size has been reached and set theno gap counter back to zero
        if self.track_gapcounter >= self.gap_length and self.max_no_gap > 0: # If it is zero -> invisible
            self.l_gap  = False
            self.no_gap = 0
            self.track_gapcounter = 0

    def update_track(self,screen):
        if not self.l_gap:
            self.track.add(self.rect)
            #print(pygame.draw.line(screen, self.color, (self.posx_old,self.posy_old), (self.posx,self.posy)))

        self.track.draw(screen)

    def update_no_collide(self, screen):

        # Move all items 1 to the right
        self.nocollide = [self.nocollide[-1]] + self.nocollide[:-1]

        # Make the first entry the most recent position
        self.nocollide[0] = self.rect

    def collision_with_boundary(self,gamefield, screen):
        for boundary in gamefield.boundaries:
            colrect = pygame.Rect(self.posx-self.thick, self.posy-self.thick, self.thick*2, self.thick*2)

            if colrect.colliderect(gamefield.boundaries[boundary]):
                # pygame.draw.rect(screen, WHITE, colrect) # Collision test
                self.alive = False

    def collision_with_player(self, players, screen):
         colrect1 = pygame.Rect(self.posx-self.thick, self.posy-self.thick, self.thick*2, self.thick*2)
         for player in players:

            # Only do for other player (self collision does not count)
            if not player.id == self.id:
                colrect2 = pygame.Rect(player.posx-player.thick, player.posy-player.thick, player.thick*2, player.thick*2)

                if colrect1.colliderect(colrect2) and not self.l_gap:  # Collision only if you don't have a gap
                    # pygame.draw.rect(screen, WHITE, colrect) # Collision test
                    self.alive = False

    def collision_with_track(self, players, screen):
        for player in players:
            col_with_any_track     = pygame.sprite.spritecollideany(self.rect, player.track) # Check if the player collides with any track (including own)
            if not col_with_any_track is None and not self.l_gap:                            # If there is a collision check if it is with your no collisionzone. If yes ignore.
                nocollide_group = pygame.sprite.Group()
                for s in self.nocollide[1:]:
                    if s is not None:
                        nocollide_group.add(s)
                #[pygame.draw.rect(screen,WHITE,s) for s in nocollide_group] # Draw the no collision zone white

                col_with_no_collzone   = pygame.sprite.spritecollideany(col_with_any_track, nocollide_group)
                if col_with_no_collzone is None: # If it is not with your own most recent track you lost
                    self.alive = False

    def activate_effects(self, effects):
        if not self.alive:
            return
        for effect in effects:
            if not effect.active:
                effect.active = True # Only activate effect once
                # Increase speed
                self.speed += effect.speed
                # Increase thickness
                self.thick += effect.thick
                # Change direction
                if effect.directionchanger:
                    dummy = self.controls.copy()
                    self.controls['right'] = dummy['left']
                    self.controls['left'] = dummy['right']
                # Invisible
                if effect.invisible:
                    self.max_no_gap = 0
                # Delete all tracks
                if effect.delete_track:
                    self.track.empty()

    def cooldown_effects(self, effects):
        for i, effect in enumerate(effects):
            effect.timer += 1
            if effect.timer >= effect.cooldown:
                # Speed item
                self.speed -= effect.speed

                # Thickness item
                self.thick -= effect.thick

                # Direction changer
                if effect.directionchanger:
                    dummy = self.controls.copy()
                    self.controls['right'] = dummy['left']
                    self.controls['left'] = dummy['right']

                # Invisible
                if effect.invisible:
                    self.max_no_gap = self.orig_max_no_gap

                del(self.effects[i])

    def check_alive(self):
        if not self.alive:
            self.speed = 0

    def get_points(self,players):
        if not self.alive and not self.point_trigger:
            self.point_trigger = True
            for player in players:
                if not player.id == self.id:
                    if player.alive:
                        player.points += 1


class effect:
    def __init__(self, cooldown=100, speed=0, thick=0, directionchanger=False, invisible=False, delete_track=False, group='', color=GREEN, name=''):
        self.timer    = 0
        self.cooldown = cooldown
        self.active   = False
        self.controls = {}
        self.speed    = speed
        self.thick    = thick
        self.directionchanger = directionchanger
        self.delete_track     = delete_track
        self.invisible = invisible
        self.color     = color
        self.name      = name
        self.group     = group

class item(pygame.sprite.Sprite):

    def __init__(self, id, posx, posy, thick, color, effect, image):
        pygame.sprite.Sprite.__init__(self)
        self.id   = id
        self.posx = posx
        self.posy = posy
        self.thick = thick
        self.color = color
        self.has_been_picked = False
        self.time_effect = 0
        self.max_time_effect = 10
        self.effect = effect
        self.rect  = Rect(self.posx, self.posy, self.thick, self.thick, 0, self.color)
        self.image = image

    def draw(self,screen):
        pygame.draw.rect(screen, self.color, self.rect)
        self.image.get_rect().center = (self.rect.rect.centerx,self.rect.rect.centery)

        screen.blit(self.image, self.rect.rect)

    def item_picked_up(self,screen, players):
        # Check for collisions with items
        playeritem = pygame.sprite.spritecollideany(self.rect, players)
        # Check if the item is for one self or all enemies
        if not playeritem is None and 'self' in self.effect.group: # Items for one self
            playeritem.effects.append(self.effect)
            self.kill() # Remove item once picked up

        if not playeritem is None and 'enemy' in self.effect.group: # Items for enemies
            for player in players: # Activate effects for all other players
                if not player.id == playeritem.id and player.alive: # Excluding one self and dead players (otherwise dead players get fat)
                    player.effects.append(copy.deepcopy(self.effect))
                self.kill() # Remove item once picked up

    def update(self, screen, players):
        self.item_picked_up(screen, players)
        self.draw(screen)

    def generator(gamefield, items, effectlist, images):
        # Random times
        if random.randint(0,300) == 1:
            # Random position
            randx = random.randint(0,gamefield.nx)
            randy = random.randint(0,gamefield.ny)
            # Random effect
            ieffect = random.randint(0,len(effectlist)-1)
            itemeffect = copy.deepcopy(effectlist[ieffect])
            # Add one to the item counter
            gamefield.item_counter += 1
            items.add( item(id=gamefield.item_counter, posx=randx, posy=randy, thick=40, color=itemeffect.color, effect=itemeffect, image=images[itemeffect.name] ))


def pause(event, paused):
    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_SPACE:
            paused = not paused
    return paused

def exit_game(event, paused):
    if paused:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return True
    return False

def display_points(screen,nx,npbox,ny, players,points2win):

    fontsize = 25
    font = pygame.font.Font('freesansbold.ttf', fontsize)



    iy = 0 + ny // 10

    text = font.render('Points to win: {}'.format(points2win), True, RED, BLACK)
    textRect = text.get_rect()
    textRect.center = (nx + npbox // 2, iy)
    screen.blit(text, textRect)

    iy += fontsize * 2


    point_list = []
    player_list = []
    for iplyr in players:
        point_list.append(iplyr.points)
        player_list.append(iplyr.id)
    sorted_points, sorted_players = zip(*sorted(zip(point_list, player_list)))

    for jplyr in sorted_players[::-1]:
        for iplyr in players:
            if jplyr == iplyr.id:
                print(iplyr)
                text = font.render('Player{}: {}'.format(iplyr.id,iplyr.points), True, iplyr.color, BLACK)
                textRect = text.get_rect()
                textRect.center = (nx + npbox // 2, iy)
                screen.blit(text, textRect)

                iy += fontsize

def check_points_victory(players, points_for_victory):
    for iplyr in players:
        if iplyr.points >= points_for_victory:
            return True

def display_victory(screen,nx,ny,players):
    fontsize = 25
    font = pygame.font.Font('freesansbold.ttf', fontsize)

    point_list = []
    player_list = []
    for iplyr in players:
        point_list.append(iplyr.points)
        player_list.append(iplyr.id)
    sorted_points, sorted_players = zip(*sorted(zip(point_list, player_list)))

    text = font.render('VICTORY for Player{} with {} points'.format(sorted_players[-1],sorted_points[-1]), True, GREEN, BLACK)
    textRect = text.get_rect()
    textRect.center = (nx // 2, ny // 2)
    screen.blit(text, textRect)


def curvefever(l_learning):
    # Initialise the game
    pygame.init()

    # Set parameters for the game size
    npbox = 250
    nx    = 600
    ny    = 600

    points2win = 10

    flags = DOUBLEBUF

    # Set up a screen
    screen = pygame.display.set_mode([nx+npbox,ny], flags)

    # Set up a field for the game and draw it
    gamefield = field(nx=nx, ny=ny, thick=5, color=YELLOW)

    # Dictionary for points
    points = {1:0, 2:0, 3:0, 4:0, 5:0}

    matchdone = False
    while not matchdone:

        # Wait a second and then pause the game
        paused   = False
        done     = False
        gamedone = False

        clock = pygame.time.Clock()

        # Fill every screen with black
        screen.fill(BLACK)

        # Generate player
        players = pygame.sprite.Group()
        players.add(player(id=1, points=points[1], posx=random.randint(0+gamefield.nx // 10 ,gamefield.nx - gamefield.nx // 10 ), posy=random.randint(0+gamefield.ny//10,gamefield.ny-gamefield.ny//10), thick=3, speed=1.8, dir=random.randint(0,360), dirspeed=3.0, color=RED, controls = {'left' : pygame.K_q, 'right': pygame.K_w}))
        players.add(player(id=2, points=points[2], posx=random.randint(0+gamefield.nx // 10 ,gamefield.nx - gamefield.nx // 10 ), posy=random.randint(0+gamefield.ny//10,gamefield.ny-gamefield.ny//10), thick=3, speed=1.8, dir=random.randint(0,360), dirspeed=3.0, color=GREEN, controls = {'left' : pygame.K_a, 'right': pygame.K_s}))
        players.add(player(id=3, points=points[3], posx=random.randint(0+gamefield.nx // 10 ,gamefield.nx - gamefield.nx // 10 ), posy=random.randint(0+gamefield.ny//10,gamefield.ny-gamefield.ny//10), thick=3, speed=1.8, dir=random.randint(0,360), dirspeed=3.0, color=YELLOW, controls = {'left' : pygame.K_d, 'right': pygame.K_f}))
        players.add(player(id=4, points=points[4], posx=random.randint(0+gamefield.nx // 10 ,gamefield.nx - gamefield.nx // 10 ), posy=random.randint(0+gamefield.ny//10,gamefield.ny-gamefield.ny//10), thick=3, speed=1.8, dir=random.randint(0,360), dirspeed=3.0, color=BLUE, controls = {'left' : pygame.K_g, 'right': pygame.K_h}))
        players.add(player(id=5, points=points[5], posx=random.randint(0+gamefield.nx // 10 ,gamefield.nx - gamefield.nx // 10 ), posy=random.randint(0+gamefield.ny//10,gamefield.ny-gamefield.ny//10), thick=3, speed=1.8, dir=random.randint(0,360), dirspeed=3.0, color=WHITE, controls = {'left' : pygame.K_j, 'right': pygame.K_k}))

        # Items is an empty list for starters
        items = pygame.sprite.Group()

        # Define some items effects
        effectlist = []
        #effectlist.append(effect(speed=2,               color=GREEN,            name='self_fast',               group='self'))
        #effectlist.append(effect(directionchanger=True, color=RED,              name='enemy_directionchanger',  group='enemy'))
        #effectlist.append(effect(invisible=True, cooldown=300, color=YELLOW,    name='self_invisible',          group='self'))
        effectlist.append(effect(thick=9, cooldown=250, color=BLACK,           name='enemy_fat',               group='enemy'))
        #effectlist.append(effect(delete_track=True,     color=BLUE,             name='all_delete_track',        group=['enemy','self']))

        # Define the images for the items
        images = {}
        images['self_fast']              = pygame.image.load("self_invisible.png")
        images['self_invisible']         = pygame.image.load("self_invisible.png")
        images['enemy_fat']              = pygame.image.load("enemy_fat.png")
        images['all_delete_track']       = pygame.image.load("self_invisible.png")
        images['enemy_directionchanger'] = pygame.image.load("self_invisible.png")

        start_ticks=pygame.time.get_ticks() #starter tick

        # Main loop
        while not gamedone:
            for event in pygame.event.get():

                paused   = pause(event, paused)
                if exit_game(event,paused):
                    matchdone = True

                if check_points_victory(players, points2win):
                    if event.key == pygame.K_SPACE:
                        matchdone = True
                    pygame.display.update()

                if matchdone:
                    gamedone = True
                    paused   = True

                if done and not paused:
                    gamedone = True


            if done:
                paused   = True

                #Save points
                for iplyr in players:
                    points[iplyr.id] = iplyr.points

            pressed = pygame.key.get_pressed()


            # Fill every screen with black
            screen.fill(BLACK)
            # Draw the boundary
            gamefield.draw_boundary(screen)

            display_points(screen,nx,npbox,ny,players,points2win)

            # Pause the game until space is hit, but only after 0.5 second
            seconds=(pygame.time.get_ticks()-start_ticks)/1000 #calculate how many seconds
            if seconds>0.3 and seconds <0.4:
                paused = True


            # Run the game if not paused
            if not paused:

                # Randomly generate items from the list of effect available
                item.generator(gamefield, items, effectlist, images)

                #Update items
                items.update(screen, players)

                # Update players and items
                players.update(screen, pressed, gamefield, players)

                # End game if all players are dead
                done = any([player.alive for player in players])==False

                if check_points_victory(players, points2win):
                    display_victory(screen, nx, ny, players)

                # Update screen
                #pygame.display.flip()

                pygame.display.update()
                clock.tick(45)
        if l_learning:
            points2win=9999999999999


if __name__ == '__main__':
    curvefever(True)

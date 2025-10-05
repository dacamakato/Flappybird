import sys
import pygame
import random
import os

def resource_path(relative):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative)
    return os.path.join(relative)

def draw_button( text, x, y ):
    font = pygame.font.SysFont(None, 40)
    rect = pygame.Rect(x, y ,200 ,50)
    pygame.draw.rect(screen, (200, 200, 210), rect)
    label = font.render(text, True, (0, 0, 0))
    screen.blit(label, (x + 10, y + 10))
    return rect
def load_records():
    if os.path.exists('records.txt'):
        with open('records.txt', "r", encoding="utf-8" ) as f:
            lines = [line.strip().split(',') for line in f]
            return [(name, int(score)) for name , score in lines]
    return []
def save_records(name, score):
    records = load_records()
    records.append((name, score))
    records.sort(key= lambda x:x[1], reverse= True)
    records = records[:5]
    with open('records.txt', "w", encoding="utf-8" ) as f:
        for name, score in records:
            f.write(f"{name},{score}\n")
            
pygame.init()
WIDTH, HEIGHT = 1200, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flappy birds")
clock = pygame.time.Clock()
start_time = pygame.time.get_ticks()

bird_images = [pygame.image.load(resource_path('Bird4.png')).convert_alpha(),
               pygame.image.load(resource_path('Bird5.png')).convert_alpha(),
               pygame.image.load(resource_path('Bird8.png')).convert_alpha()]


pipe_image = pygame.image.load(resource_path('pipe_ts.png')).convert_alpha()
pipe_width = pipe_image.get_width()
pipe_height = pipe_image.get_height()

bird_index = 0
bird_speed = 0
gravity = 0.3
bird_x = 50
bird_y = HEIGHT // 2
game_active = True
score = 0

big_font = pygame.font.SysFont(None, 72)
score_font = pygame.font.SysFont(None, 36)
score_text = None

game_state = 'menu'
username = ""
input_active = False

button_width = 200
button_height = 50
button_x = WIDTH // 2 - button_width // 2
button_y = 215

pipes = []
pipe_gap = 125
pipe_speed = 10
pipe_frequency = 1000
SPAWNPIPE = pygame.USEREVENT
pygame.time.set_timer(SPAWNPIPE, pipe_frequency)

font = pygame.font.SysFont(None,72)
text = font.render("Game over", True, (255, 0, 0))


while True:
    clock.tick(60)
    screen.fill((135, 205, 250))
    

    if game_state == 'menu':
        title = big_font.render('Flappy bird', True,  (0, 0, 0))
        screen.blit(title, (WIDTH // 2 - title.get_width()// 2, 100))
        start_button = draw_button('Start game', button_x, button_y)
        levels_button = draw_button('Levels', button_x, button_y + 15 + button_height)
        records_button = draw_button('Records', button_x, button_y + 30  + button_height * 2 )
    
    elif game_state == 'records':
        title = big_font.render("Top scores",True, (0, 0, 0))
        screen.blit(title, (WIDTH // 2 - title.get_width()// 2, 100))
        records = load_records()
        for i, (name, rec_score) in enumerate(records):
            rec_text = score_font.render(f"{i + 1}. {name} - {rec_score}", True ,(0, 0, 0))
            screen.blit(rec_text, (WIDTH // 2 - rec_text.get_width()// 2, 200 + i * 40))
        back_button = draw_button("Back", button_x, HEIGHT - 100)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif game_state == 'play':
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    bird_speed = -6
            if event.type == SPAWNPIPE:
                pipe_y = random.randint(100, HEIGHT - 100 - pipe_gap)
                pipes.append({"x": WIDTH, "y": pipe_y, "passed":False})
        elif game_state == 'menu':
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()

                if start_button.collidepoint(pos):
                    bird_y = HEIGHT // 2
                    bird_speed = 0
                    pipes.clear()
                    score = 0
                    game_active = True
                    game_state = 'play'
                elif levels_button.collidepoint(pos):
                    pass
                elif records_button.collidepoint(pos):
                    game_state = 'records'
        elif game_state == 'records':
            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if back_button.collidepoint(pos):
                    game_state = 'menu'
        elif game_state == "Game_over":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    game_state = "menu"

    

    
    if game_state == 'play':
        bird_speed += gravity
        bird_y += bird_speed
        bird_index += 0.4
        if bird_index >= len(bird_images):
            bird_index = 0
        current_bird = bird_images[int(bird_index)]
        if bird_y > HEIGHT :
            game_active = False
        bird_rect = pygame.Rect(bird_x, bird_y, current_bird.get_width(),current_bird.get_height())
        for pipe in pipes:
            pipe["x"] -= pipe_speed
        pipes = [pipe for pipe in pipes if pipe["x"] + pipe_width > 0] 
        for pipe in pipes:
            screen.blit(pipe_image, (pipe["x"], pipe["y"] + pipe_gap))
            flipped_pipe = pygame.transform.flip(pipe_image, False, True)
            screen.blit(flipped_pipe,(pipe["x"] , pipe["y"] - pipe_height))
            top_pipe_rect = pygame.Rect(pipe["x"] , pipe["y"] - pipe_height, pipe_width - 5, pipe_height - 5)
            bottom_pipe_rect = pygame.Rect(pipe["x"] , pipe["y"] + pipe_gap, pipe_width - 5, pipe_height - 5)
            if bird_rect.colliderect(top_pipe_rect) or bird_rect.colliderect(bottom_pipe_rect):
                game_active = False
            if pipe['x'] + pipe_width < bird_x and not pipe['passed']:
                score += 1
                pipe['passed'] = True
                print("Очки:", score)
        screen.blit(current_bird, (bird_x, bird_y))
        score_text = score_font.render(f"Score:{score}", True, (0, 0, 0))
        screen.blit(score_text, (10,10))
        
        if not game_active:
            save_records("player",score)
            game_state = "Game_over"
    elif game_state == "Game_over":
        over_text = big_font.render("Game Over", True, (255, 0, 0))
        info_text = font.render("Press Enter to go to menu", True, (0, 0, 0))
        screen.blit(over_text, (WIDTH // 2 - over_text.get_width() // 2, HEIGHT // 2 - 50))
        screen.blit(info_text, (WIDTH // 2 - info_text.get_width() // 2, HEIGHT // 2 + 10))
        #screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//2 - text.get_height()//2)) 
  
      
    pygame.display.flip()
    
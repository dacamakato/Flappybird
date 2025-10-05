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

def start_game():
    # Reset ship movement flags first
    ship.moving_right = False
    ship.moving_left = False
    ship.moving_up = False
    ship.moving_down = False
    
    stats.game_active = True
    stats.reset_stats()
    pygame.mouse.set_visible(False)
    
    # Empty game objects
    aliens.empty()
    bullets.empty()
    cargoes.empty()
    
    # Create new fleet and center ship
    create_fleet(ai_settings, screen, ship, aliens, cargoes)
    ship.center_ship()
    
    nonlocal current_menu
    current_menu = None 

def handle_events(ai_settings, screen, ship, aliens, bullets, cargoes):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
        elif event.type == pygame.VIDEORESIZE and not ai_settings.fullscreen:
            # Handle window resize
            width, height = ai_settings.handle_resize(event.w, event.h)
            screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
            # Update background for new size
            screen_bg = pygame.transform.scale(screen_bg, (width*2, width*2))
            screen_bg_2 = pygame.transform.rotate(screen_bg, 180)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RIGHT:
                ship.moving_right = True
            elif event.key == pygame.K_LEFT:
                ship.moving_left = True
            elif event.key == pygame.K_UP:
                ship.moving_up = True
            elif event.key == pygame.K_DOWN:
                ship.moving_down = True 
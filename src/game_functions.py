import sys
import pygame
from time import sleep
from random import randint
from src.bullet import Bullet
from src.alien import Alien

pygame.mixer.init()

sound_fire = pygame.mixer.Sound('data/assets/sounds/fire.ogg')
sound_explosion = pygame.mixer.Sound('data/assets/sounds/explosion.ogg')


def load_sounds():
    global sound_fire, sound_explosion
    sound_fire = pygame.mixer.Sound('data/assets/sounds/fire.ogg')
    sound_explosion = pygame.mixer.Sound('data/assets/sounds/explosion.ogg')


def play_sound(sound, ai_settings):
    """Play a sound if sound effects are enabled."""
    if ai_settings.sound_fx_on:
        sound.play()


def check_keydown_events(event, ai_settings, screen, ship, bullets):
    """Respond to keypresses."""
    # Check if the pressed key matches any of our actions
    if event.key == pygame.K_ESCAPE:
        return
        
    if ai_settings.input_handler.is_key_for_action(event.key, 'move_right'):
        ship.moving_right = True
    elif ai_settings.input_handler.is_key_for_action(event.key, 'move_left'):
        ship.moving_left = True
    elif ai_settings.input_handler.is_key_for_action(event.key, 'move_up'):
        ship.moving_up = True
    elif ai_settings.input_handler.is_key_for_action(event.key, 'move_down'):
        ship.moving_down = True
    elif ai_settings.input_handler.is_key_for_action(event.key, 'fire'):
        fire_bullet(ai_settings, screen, ship, bullets)


def fire_bullet(ai_settings, screen, ship, bullets):
    """Fire a bullet if limit not reached yet."""
    # Create a new bullet and add it to the bullets group.
    if len(bullets) < ai_settings.bullets_allowed:
        new_bullet = Bullet(ai_settings, screen, ship)
        bullets.add(new_bullet)
        play_sound(sound_fire, ai_settings)


def check_keyup_events(event, ship, ai_settings):
    """Respond to key releases."""
    # Check which key was released
    if event.key == pygame.K_ESCAPE:
        return
        
    if ai_settings.input_handler.is_key_for_action(event.key, 'move_right'):
        ship.moving_right = False
    elif ai_settings.input_handler.is_key_for_action(event.key, 'move_left'):
        ship.moving_left = False
    elif ai_settings.input_handler.is_key_for_action(event.key, 'move_up'):
        ship.moving_up = False
    elif ai_settings.input_handler.is_key_for_action(event.key, 'move_down'):
        ship.moving_down = False


def check_events(ai_settings, screen, stats, play_button, ship, aliens, bullets, cargoes):
    """Respond to key presses and mouse events."""
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            sys.exit()
        elif event.type == pygame.KEYDOWN and stats.game_active:
            check_keydown_events(event, ai_settings, screen, ship, bullets)
        elif event.type == pygame.KEYUP and stats.game_active:
            check_keyup_events(event, ship, ai_settings)
        elif event.type == pygame.MOUSEBUTTONDOWN and not stats.game_active:
            mouse_x, mouse_y = pygame.mouse.get_pos()
            check_play_button(ai_settings, screen, stats, play_button, ship, aliens, bullets, cargoes, mouse_x, mouse_y)


def check_play_button(ai_settings, screen, stats, play_button, ship, aliens, cargoes, bullets, mouse_x, mouse_y):
    """start a new game when the player clicks play."""
    button_clicked = play_button.rect.collidepoint(mouse_x, mouse_y)
    if button_clicked and not stats.game_active:
        # reset the game settings.
        ai_settings.initialize_dynamic_settings()

        # Hide the mouse cursor.
        pygame.mouse.set_visible(False)
        # Reset the game statistics.
        stats.reset_stats()
        stats.game_active = True          

        # Empty the list of aliens and bullets.
        aliens.empty()
        bullets.empty()
        cargoes.empty()

        # Create a new fleet and center the ship.
        create_fleet(ai_settings, screen, ship, aliens, cargoes)
        ship.center_ship()


def update_screen(ai_settings, screen, stats, sb, ship, aliens, bullets, play_button, screen_bg, screen_bg_2, cargoes):
    """Update image on the screen and flip to the new screen."""
    # Redraw the screen during each pass through the loop
    screen.fill(ai_settings.bg_color)
    screen.blit(screen_bg, (ai_settings.bg_screen_x, ai_settings.bg_screen_y))
    screen.blit(screen_bg_2, (ai_settings.bg_screen_2_x, ai_settings.bg_screen_2_y))

    # Redraw all bullets behind ship and aliens.
    for bullet in bullets.sprites():
        # TODO: There is an interesting bug in here!
        try:
            bullet.draw_bullet()
        except:
            pass

    ship.bltime()
    aliens.draw(screen)
    cargoes.draw(screen)

    # Draw the score information.
    sb.show_score()

    # Draw the play button if the game is inactive
    if not stats.game_active:
        play_button.draw_button()
    else:
        # Resetting the background when it leaves screen
        if ai_settings.bg_screen_y >= ai_settings.screen_height:
            ai_settings.bg_screen_y = -ai_settings.screen_height * 2

        if ai_settings.bg_screen_2_y >= ai_settings.screen_height:
            ai_settings.bg_screen_2_y = -ai_settings.screen_height * 2

        # Updating the background when it leaves screen
        ai_settings.bg_screen_y += ai_settings.bg_screen_scroll_speed
        ai_settings.bg_screen_2_y += ai_settings.bg_screen_scroll_speed

    pygame.display.flip()


def update_bullets(ai_settings, screen, stats, sb, ship, aliens, bullets, cargoes, alien_bullets):
    """Update position of bullets and get rid of old bullets."""
    # Update bullet positions
    bullets.update()
    alien_bullets.update()

    # Get rid of bullets that have disappeared
    for bullet in bullets.copy():
        if bullet.rect.bottom <= 0:
            bullets.remove(bullet)

    for bullet in alien_bullets.copy():
        if bullet.rect.top >= ai_settings.screen_height:
            alien_bullets.remove(bullet)

    check_bullet_alien_collisions(ai_settings, screen, stats, sb, ship, aliens, bullets, cargoes)
    check_bullet_ship_collisions(ai_settings, stats, screen, ship, alien_bullets, aliens, bullets, cargoes, sb)


def check_bullet_alien_collisions(ai_settings, screen, stats, sb, ship, aliens, bullets, cargoes):
    """Respond to bullet-alien collisions."""
    # Remove any bullets and aliens that have collided.
    # Check for any bullets that have hit aliens.
    # If so, get rid of the bullet and the alien.
    collisions_1 = pygame.sprite.groupcollide(bullets, aliens, True, True)
    collisions_2 = pygame.sprite.groupcollide(bullets, cargoes, True, True)
    collisions_3 = pygame.sprite.groupcollide(aliens, cargoes, False, True)

    # if we hit alien
    if collisions_1:
        for aliens in collisions_1.values():
            stats.score += ai_settings.alien_points * len(aliens)
            sb.prep_score()
            play_sound(sound_explosion, ai_settings)

    # if we hit cargo:
    if collisions_2:
        for _ in collisions_2.values():
            stats.score -= ai_settings.cargo_points
            sb.prep_score()
            play_sound(sound_explosion, ai_settings)

    # if cargo hit alien:
    if collisions_3:
        for _ in collisions_3.values():
            stats.score -= ai_settings.cargo_points
            sb.prep_score()
            play_sound(sound_explosion, ai_settings)

    if len(aliens) == 0:
        # Destroy existing bullets, speed up game, and create new fleet.
        bullets.empty()
        ai_settings.increase_speed()
        create_fleet(ai_settings, screen, ship, aliens, cargoes)


def get_number_aliens_x(ai_settings, alien_width):
    """Determine the number of aliens that fit in row."""
    available_space_x = ai_settings.screen_width - 2 * alien_width
    # Escape 2 aliens_width from each side of display
    number_aliens_x = int(available_space_x / (2 * alien_width))
    # available_space_x / ([Two aliens in each side SO ONE IN MIDDLE])
    return number_aliens_x


def get_number_rows(ai_settings, ship_height, alien_height):
    """Determine the number of rows of aliens that fit on the screen."""
    available_space_y = (ai_settings.screen_height - (3 * alien_height) - ship_height)
    number_rows = int(available_space_y / (2 * alien_height))
    return number_rows


def create_alien(ai_settings, screen, aliens, alien_number, row_number):
    """Create an alien and place it in the row."""
    alien = Alien(ai_settings, screen, alien_type=0)
    alien_width = alien.rect.width
    alien.x = alien_width + 2 * alien_width * alien_number
    alien.rect.x = alien.x
    alien.rect.y = alien.rect.height + 2 * alien.rect.height * row_number
    aliens.add(alien)


def create_cargo(ai_settings, screen, cargoes):
    """Create a cargo and place it in the aliens."""
    cargo = Alien(ai_settings, screen, alien_type=1)
    cargoes.add(cargo)


def create_fleet(ai_settings, screen, ship, aliens, cargoes):
    """Create a full fleet of aliens."""
    # Create an alien and find the number of aliens in a row.
    # Spacing between each alien is equal to one alien width.
    alien = Alien(ai_settings, screen)
    number_aliens_x = get_number_aliens_x(ai_settings, alien.rect.width)
    number_rows = get_number_rows(ai_settings, ship.rect.height, alien.rect.height)

    # Create the first row of aliens.
    for row_number in range(number_rows):
        for alien_number in range(number_aliens_x):
            # Create an alien and place it in the row.
            create_alien(ai_settings, screen, aliens, alien_number, row_number)


def check_fleet_edges(ai_settings, aliens):
    """Respond appropriately if any aliens have reached an edge."""
    for alien in aliens.sprites():
        if alien.type == 0:
            if alien.check_edges():
                change_fleet_direction(ai_settings, aliens)
                break


def change_fleet_direction(ai_settings, aliens):
    """Drop the entire fleet and change the fleet's direction."""
    for aliens in aliens.sprites():
        aliens.rect.y += ai_settings.fleet_drop_speed
    ai_settings.fleet_direction *= -1


def ship_hit(ai_settings, stats, screen, ship, aliens, bullets, cargoes, sb):
    """Respond to ship being hit by alien."""
    if stats.ships_left > 0:
        # Decrement ships_left.
        stats.ships_left -= 1
        
        # Update scoreboard.
        sb.prep_ships()

        # Empty the list of aliens and bullets.
        aliens.empty()
        bullets.empty()
        cargoes.empty()

        # Create a new fleet and center the ship.
        create_fleet(ai_settings, screen, ship, aliens, cargoes)
        ship.center_ship()

        # Pause.
        sleep(0.5)
    else:
        stats.game_active = False
        pygame.mouse.set_visible(True)
        return "game_over"  # Signal to show game over menu


def check_aliens_bottom(ai_settings, stats, screen, ship, aliens, bullets, cargoes, sb):
    """Check if any alien have reached the bottom of the screen."""
    screen_rect = screen.get_rect()
    for alien in aliens.sprites():
        if alien.rect.bottom >= screen_rect.bottom:
            # Treat this same as if the ship got hit.
            if alien.type == 0:
                ship_hit(ai_settings, stats, screen, ship, aliens, bullets, cargoes, sb)
                break


def update_aliens(ai_settings, stats, screen, ship, aliens, bullets, cargoes, sb):
    """Check if the fleet is at the edge, and then update the position of all aliens in the fleet."""
    check_fleet_edges(ai_settings, aliens)
    aliens.update()
    cargoes.update()

    # Randomly spawn cargo ships during gameplay
    if stats.game_active and ai_settings.cargo_drop_chance > 0:
        if randint(1, 100) <= ai_settings.cargo_drop_chance:
            create_cargo(ai_settings, screen, cargoes)

    if pygame.sprite.spritecollideany(ship, aliens):
        result = ship_hit(ai_settings, stats, screen, ship, aliens, bullets, cargoes, sb)
        if result == "game_over":
            return result

    if pygame.sprite.spritecollideany(ship, cargoes):
        result = ship_hit(ai_settings, stats, screen, ship, aliens, bullets, cargoes, sb)
        if result == "game_over":
            return result

    # look for aliens hitting the bottom of the screen.
    result = check_aliens_bottom(ai_settings, stats, screen, ship, aliens, bullets, cargoes, sb)
    if result == "game_over":
        return result


def alien_fire(ai_settings, screen, aliens, alien_bullets):
    """Have aliens randomly fire bullets."""
    for alien in aliens.sprites():
        # Random chance for each alien to fire
        if randint(1, 1000) <= ai_settings.alien_fire_chance:
            # Create a new bullet
            bullet = Bullet(ai_settings, screen, alien, -1)  # -1 for downward direction
            alien_bullets.add(bullet)
            if ai_settings.sound_fx_on:
                play_sound(sound_fire, ai_settings)


def check_bullet_ship_collisions(ai_settings, stats, screen, ship, alien_bullets, aliens, bullets, cargoes, sb):
    """Check for collisions between alien bullets and the player's ship."""
    if pygame.sprite.spritecollideany(ship, alien_bullets):
        ship_hit(ai_settings, stats, screen, ship, aliens, bullets, cargoes, sb)
        alien_bullets.empty()  # Clear alien bullets after hit

"""Pre-train the alien Q-learning policies headless (no window, no audio).

The trainer replays the real game kinematics (real aliens, real bullets)
against a scripted stand-in for the player, and writes the learned
Q-tables to ``data/rl/*.json`` for the game to load.

Examples:
    python train_rl.py                          # train (continues existing tables)
    python train_rl.py --fresh --episodes 4000  # start over
    python train_rl.py --eval 300               # policy vs. classic heuristic
"""

from __future__ import annotations

import argparse
import logging
import math
import os
import random
import sys
import time
from collections import deque
from pathlib import Path

# SDL must run headless *before* pygame (or src.settings) initialises it.
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
from pygame.sprite import Group

from src import rl
from src.alien import AlienL1, AlienL2
from src.bullet import AlienBullet, ShipBullet
from src.rl import QLearningAgent
from src.rl import state as features
from src.rl.controller import FIRE_FILE, MOVEMENT_FILE
from src.resources.texture_atlas import TextureAtlas
from src.settings import BULLETS_ALLOWED, SCREEN_HEIGHT, SCREEN_WIDTH, Settings

# --- Rewards ---------------------------------------------------------------

APPROACH_REWARD = 0.012  # per pixel closed since the previous decision
HIT_PENALTY = -1.0  # the alien lost one hit point
DEATH_REWARD = -15.0  # the alien was shot down (episode over)
RAM_REWARD = 15.0  # the alien crashed into the ship (episode over)
SHOT_HIT_REWARD = 8.0  # the alien's bullet hit the ship
SHOT_MISS_REWARD = -0.15  # the alien's bullet left the screen without hitting
DODGE_REWARD = 1.0  # an enemy bullet passed within DODGE_RADIUS without hitting
DODGE_RADIUS = 150.0  # px - how close a bullet must pass to count as a dodge

logger = logging.getLogger("train_rl")


def offscreen(bullet) -> bool:
    """Same off-screen predicate the game loop uses for bullets."""
    rect = bullet.rect
    return rect.bottom <= 0 or rect.top >= SCREEN_HEIGHT or rect.left < 0 or rect.right > SCREEN_WIDTH


class BotShip:
    """Scripted stand-in for the human player, used only while pre-training.

    It wanders the screen, dodges incoming fire sideways and shoots back
    with a little aim noise, so the enemies see a variety of situations.
    """

    MARGIN = 120

    def __init__(self, rng: random.Random):
        image = TextureAtlas.get_sprite_texture("ship/ship.png")
        self.rect = image.get_rect()
        self.rect.center = (rng.randint(self.MARGIN, SCREEN_WIDTH - self.MARGIN), SCREEN_HEIGHT - 160)
        self.screen_rect = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        self.angle = 0.0
        self.hearts = 5
        self.rng = rng
        self.target = [float(self.rect.centerx), float(self.rect.centery)]
        self.retarget_at = 0
        self.dodge_until = -1
        self.next_shot = rng.randint(20, 80)

    def _retarget(self, frame: int) -> None:
        rng = self.rng
        self.target = [
            rng.uniform(self.MARGIN, SCREEN_WIDTH - self.MARGIN),
            rng.uniform(self.MARGIN, SCREEN_HEIGHT - self.MARGIN),
        ]
        self.retarget_at = frame + rng.randint(50, 160)

    def _dodge(self, alien_bullets, frame: int) -> None:
        """Sidestep perpendicular to the closest incoming bullet."""
        threat = None
        best_distance = 170.0
        for bullet in alien_bullets:
            dx = self.rect.centerx - bullet.rect.centerx
            dy = self.rect.centery - bullet.rect.centery
            distance = math.hypot(dx, dy)
            if distance >= best_distance:
                continue
            velocity_x = -math.sin(bullet.angle)
            velocity_y = -math.cos(bullet.angle)
            if velocity_x * dx + velocity_y * dy <= 0:
                continue  # travelling away, harmless
            threat = bullet
            best_distance = distance

        if threat is None:
            return

        velocity_x = -math.sin(threat.angle)
        velocity_y = -math.cos(threat.angle)
        side_x, side_y = -velocity_y, velocity_x
        away = side_x * (self.rect.centerx - threat.rect.centerx) + side_y * (self.rect.centery - threat.rect.centery)
        sign = 1.0 if away >= 0 else -1.0
        self.target = [self.rect.centerx + side_x * 150 * sign, self.rect.centery + side_y * 150 * sign]
        self.dodge_until = frame + 30

    def update(self, frame: int, alien, ship_bullets, alien_bullets, settings) -> None:
        if frame >= self.retarget_at and frame > self.dodge_until:
            self._retarget(frame)
        self._dodge(alien_bullets, frame)

        speed_x = settings.ship_speed_factor_x * settings.delta_time
        speed_y = settings.ship_speed_factor_y * settings.delta_time

        delta_x = self.target[0] - self.rect.centerx
        if abs(delta_x) >= 1:
            self.rect.centerx += int(math.copysign(min(abs(delta_x), speed_x), delta_x))
        delta_y = self.target[1] - self.rect.centery
        if abs(delta_y) >= 1:
            self.rect.centery += int(math.copysign(min(abs(delta_y), speed_y), delta_y))
        self.rect.clamp_ip(self.screen_rect)

        # Aim at the alien (with a little noise) and shoot back.
        aim_x = alien.rect.centerx - self.rect.centerx
        aim_y = alien.rect.centery - self.rect.centery
        self.angle = math.atan2(-aim_x, -aim_y) + self.rng.uniform(-0.22, 0.22)
        if frame >= self.next_shot and len(ship_bullets) < BULLETS_ALLOWED:
            ship_bullets.add(ShipBullet(self))
            self.next_shot = frame + self.rng.randint(30, 90)


def spawn_alien(settings, screen, rng: random.Random):
    """Replicates ``gf.spawn_random_alien`` (random edge, occasional L2)."""
    if random.randint(1, 100) <= settings.alien_l2_spawn_chance:
        alien = AlienL2(settings, screen)
    else:
        alien = AlienL1(settings, screen)

    direction = rng.choice(("top", "bottom", "left", "right"))
    if direction == "top":
        x, y = rng.randint(0, settings.screen_width), -50
    elif direction == "bottom":
        x, y = rng.randint(0, settings.screen_width), settings.screen_height + 50
    elif direction == "left":
        x, y = -50, rng.randint(0, settings.screen_height)
    else:
        x, y = settings.screen_width + 50, rng.randint(0, settings.screen_height)

    alien.rect.x = x
    alien.rect.y = y
    alien.x = float(x)
    alien.y = float(y)
    return alien


class Trainer:
    """Owns the game world used for pre-training and evaluation."""

    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.settings = Settings()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        TextureAtlas.initialize()

        self.save_dir = Path(args.save_dir) if args.save_dir else rl.RL_DATA_DIR
        self.controller = rl.init_controller(self.save_dir)
        if args.fresh or self.controller.movement is None:
            self.controller.movement = QLearningAgent(
                "movement",
                features.RELATIVE_MOVEMENT_ACTIONS,
                alpha=args.alpha,
                gamma=args.gamma,
                space_id=features.ENEMY_STATE_SPACE,
            )
        if args.fresh or self.controller.fire is None:
            self.controller.fire = QLearningAgent(
                "fire",
                features.FIRE_ACTIONS,
                alpha=args.alpha,
                gamma=args.gamma,
                space_id=features.ENEMY_STATE_SPACE,
            )

        self.rng = random.Random(args.seed)
        if args.seed is not None:
            random.seed(args.seed)

    # --- One episode --------------------------------------------------------

    def run_episode(self, *, training: bool, active: bool, epsilon: float, max_seconds: float) -> dict:
        controller = self.controller
        settings = self.settings
        movement_agent = controller.movement
        fire_agent = controller.fire

        controller.active = active
        controller.training = training
        controller.play_epsilon = epsilon
        controller.last_movement_decision = None
        controller.last_fire = None
        controller.now_ms = 0.0
        controller._ship_position = None
        controller._ship_velocity = (0.0, 0.0)
        controller._ship_measured_at = 0

        alien = spawn_alien(settings, self.screen, self.rng)
        bot = BotShip(self.rng)
        ship_bullets: Group = Group()
        alien_bullets: Group = Group()
        fire_pending: dict = {}

        total_frames = max(1, int(max_seconds * settings.fps))
        fire_every = max(1, int(settings.fps // 10))  # ~100 ms, same cadence as the game loop

        pending = None  # (state, action, distance) awaiting its movement reward
        carry = 0.0  # movement rewards that arrived between two decisions
        near_misses: set = set()  # enemy bullets that came close but were dodged
        frames_survived = total_frames
        outcome = "timeout"
        stats = {"died": 0, "ram": 0, "bot_hits": 0, "bot_downs": 0, "fires": 0}

        def close_movement(next_state, done: bool, extra: float = 0.0) -> None:
            """Resolve the held movement action (approach + carry + terminal)."""
            nonlocal pending, carry
            if pending is None:
                carry = 0.0
                return
            state, action, distance = pending
            reward = extra + carry + APPROACH_REWARD * (distance - features.distance_to(alien, bot))
            movement_agent.learn(state, action, reward, next_state, done)
            pending = None
            carry = 0.0

        for frame in range(total_frames):
            frames_survived = frame + 1

            bot.update(frame, alien, ship_bullets, alien_bullets, settings)
            ship_bullets.update()
            alien_bullets.update()

            # Expired bullets.
            for bullet in ship_bullets.copy():
                if offscreen(bullet):
                    ship_bullets.remove(bullet)
            for bullet in alien_bullets.copy():
                if not offscreen(bullet):
                    continue
                alien_bullets.remove(bullet)
                shot = fire_pending.pop(bullet, None)
                if shot is not None:
                    fire_agent.learn(
                        shot[0], shot[1], SHOT_MISS_REWARD, features.fire_state(alien, bot, controller._ship_velocity), False
                    )

            # --- Dodge accounting: bullets that came close then flew past ---
            for bullet in ship_bullets:
                if (
                    math.hypot(bullet.rect.centerx - alien.rect.centerx, bullet.rect.centery - alien.rect.centery)
                    <= DODGE_RADIUS
                ):
                    near_misses.add(bullet)
            for bullet in list(near_misses):
                if bullet not in ship_bullets:  # it hit the alien (or expired): no reward
                    near_misses.discard(bullet)
                    continue
                away_x = alien.rect.centerx - bullet.rect.centerx
                away_y = alien.rect.centery - bullet.rect.centery
                if -math.sin(bullet.angle) * away_x + -math.cos(bullet.angle) * away_y <= 0:
                    near_misses.discard(bullet)
                    carry += DODGE_REWARD

            # --- Movement: the decision happens inside alien.update ---
            controller.last_movement_decision = None
            alien.update(bot, ship_bullets)
            decision = controller.last_movement_decision
            if decision is not None:
                close_movement(decision[0], False)
                if training:
                    pending = decision

            # --- Firing pass (~10x per second, like the real game loop) ---
            if frame % fire_every == 0:
                controller.now_ms = frame * (1000.0 / settings.fps)  # simulated clock
                fire = None
                lead = (0.0, 0.0)
                if controller.enabled:
                    controller.update_ship_velocity(bot)
                    controller.last_fire = None
                    fire = controller.should_fire(alien, bot)
                    if fire:
                        lead = controller.ship_velocity_per_frame()  # aim at an intercept point
                if fire is None:
                    chance = settings.alien_fire_chance if type(alien) is AlienL1 else settings.alien_l2_fire_chance
                    fire = random.randint(1, 1000) <= chance
                if fire:
                    bullet = AlienBullet(alien, bot, lead)
                    alien_bullets.add(bullet)
                    stats["fires"] += 1
                    if training and controller.last_fire is not None:
                        fire_pending[bullet] = controller.last_fire

            # --- Collisions & rewards ---
            hits = pygame.sprite.spritecollide(alien, ship_bullets, True)
            if hits:
                alien.health -= len(hits)
                carry += HIT_PENALTY * len(hits)
                if alien.health <= 0:
                    close_movement(None, True, DEATH_REWARD)
                    outcome = "death"
                    stats["died"] = 1
                    break

            if alien.rect.colliderect(bot.rect):
                close_movement(None, True, RAM_REWARD)
                outcome = "ram"
                stats["ram"] = 1
                bot.hearts -= 1
                break

            for bullet in alien_bullets.copy():
                if not bullet.rect.colliderect(bot.rect):
                    continue
                alien_bullets.remove(bullet)
                stats["bot_hits"] += 1
                bot.hearts -= 1
                if bot.hearts <= 0:
                    bot.hearts = 5
                    stats["bot_downs"] += 1
                shot = fire_pending.pop(bullet, None)
                if shot is not None:
                    fire_agent.learn(
                        shot[0], shot[1], SHOT_HIT_REWARD, features.fire_state(alien, bot, controller._ship_velocity), False
                    )
        else:
            # Ran out of time: episode ends without a terminal bonus.
            close_movement(None, True, 0.0)

        stats["frames"] = frames_survived
        stats["outcome"] = outcome
        return stats

    # --- Training -----------------------------------------------------------

    def train(self) -> None:
        args = self.args
        controller = self.controller
        recent: deque = deque(maxlen=100)
        started = time.time()

        logger.info("Training for %d episodes (max %.1fs each)...", args.episodes, args.max_seconds)

        for episode in range(1, args.episodes + 1):
            epsilon = max(args.epsilon_min, args.epsilon * (args.epsilon_decay ** episode))
            alpha = max(args.alpha_min, args.alpha * (args.alpha_decay ** episode))
            controller.movement.alpha = alpha
            controller.fire.alpha = alpha

            recent.append(self.run_episode(training=True, active=True, epsilon=epsilon, max_seconds=args.max_seconds))

            if episode % args.log_every == 0:
                self._log_progress(episode, recent, epsilon, alpha, started)

        self.save()
        logger.info("Training finished in %.1fs", time.time() - started)

    def _log_progress(self, episode: int, recent: deque, epsilon: float, alpha: float, started: float) -> None:
        count = len(recent)
        survival = sum(r["frames"] for r in recent) / count / self.settings.fps
        died = sum(r["died"] for r in recent) / count * 100
        rammed = sum(r["ram"] for r in recent) / count * 100
        hits = sum(r["bot_hits"] for r in recent) / count
        logger.info(
            "ep %5d | survival %5.1fs | died %3.0f%% | ram %3.0f%% | ship hits %4.1f"
            " | eps %.2f | alpha %.3f | states %d/%d | %4.0fs",
            episode,
            survival,
            died,
            rammed,
            hits,
            epsilon,
            alpha,
            len(self.controller.movement),
            len(self.controller.fire),
            time.time() - started,
        )

    def save(self) -> None:
        self.controller.movement.save(self.save_dir / MOVEMENT_FILE)
        self.controller.fire.save(self.save_dir / FIRE_FILE)
        logger.info(
            "Saved %d movement states -> %s and %d fire states -> %s",
            len(self.controller.movement),
            self.save_dir / MOVEMENT_FILE,
            len(self.controller.fire),
            self.save_dir / FIRE_FILE,
        )

    # --- Evaluation ---------------------------------------------------------

    def evaluate(self, episodes: int) -> None:
        logger.info("=== Evaluation: %d episodes per mode, max %.1fs each ===", episodes, self.args.max_seconds)
        logger.info(
            "%-18s %9s %7s %7s %9s %9s %9s", "mode", "survival", "died", "ram", "hits/ep", "fires/ep", "accuracy"
        )

        for label, active in (("RL policy", True), ("Classic heuristic", False)):
            results = [
                self.run_episode(training=False, active=active, epsilon=0.0, max_seconds=self.args.max_seconds)
                for _ in range(episodes)
            ]
            count = len(results)
            survival = sum(r["frames"] for r in results) / count / self.settings.fps
            died = sum(r["died"] for r in results) / count * 100
            rammed = sum(r["ram"] for r in results) / count * 100
            hits = sum(r["bot_hits"] for r in results) / count
            fires = sum(r["fires"] for r in results) / count
            total_fires = max(1, sum(r["fires"] for r in results))
            accuracy = sum(r["bot_hits"] for r in results) / total_fires * 100
            logger.info(
                "%-18s %8.1fs %6.0f%% %6.0f%% %9.1f %9.1f %8.0f%%", label, survival, died, rammed, hits, fires, accuracy
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--episodes", type=int, default=3000, help="number of training episodes (default: 3000)")
    parser.add_argument("--max-seconds", type=float, default=15.0, help="time limit per episode (default: 15)")
    parser.add_argument("--eval", type=int, default=0, metavar="N", help="run N evaluation episodes per mode instead of training")
    parser.add_argument("--fresh", action="store_true", help="discard existing Q-tables and start over")
    parser.add_argument("--save-dir", default=None, help="where to write the Q-tables (default: data/rl)")
    parser.add_argument("--alpha", type=float, default=0.3, help="initial learning rate")
    parser.add_argument("--alpha-min", type=float, default=0.03)
    parser.add_argument("--alpha-decay", type=float, default=0.9997)
    parser.add_argument("--gamma", type=float, default=0.95, help="discount factor")
    parser.add_argument("--epsilon", type=float, default=0.4, help="initial exploration rate")
    parser.add_argument("--epsilon-min", type=float, default=0.05)
    parser.add_argument("--epsilon-decay", type=float, default=0.9995)
    parser.add_argument("--seed", type=int, default=None, help="random seed for reproducibility")
    parser.add_argument("--log-every", type=int, default=100, help="progress log interval (episodes)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)

    trainer = Trainer(args)
    if args.eval > 0:
        trainer.evaluate(args.eval)
    else:
        trainer.train()
    return 0


if __name__ == "__main__":
    sys.exit(main())

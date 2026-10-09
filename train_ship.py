"""Pre-train the ship auto-pilot's Q-tables headless (no window, no audio).

The ship fights the real, already RL-trained enemies (data/rl/*.json) in
the real game loop, learning to dodge alien fire and to shoot back. The
learned tables power the "Auto" toggle on the main menu.

Examples:
    python train_ship.py                      # train (continues existing tables)
    python train_ship.py --fresh --episodes 8000
    python train_ship.py --eval 300           # RL movement vs aim-and-fire only
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

import src.game_functions as gf
from src import rl
from src.bullet import ShipBullet
from src.health import Health
from src.input import Input
from src.rl import QLearningAgent, ShipAutopilot
from src.rl import state as features
from src.rl.autopilot import SHIP_FIRE_FILE, SHIP_MOVEMENT_FILE
from src.rl.controller import RL_DATA_DIR
from src.resources.texture_atlas import TextureAtlas
from src.settings import SCREEN_HEIGHT, SCREEN_WIDTH, Settings
from src.ship import Ship
from train_rl import offscreen

# --- Rewards ---------------------------------------------------------------

SHIP_HIT_PENALTY = -10.0  # the ship lost one heart
SHIP_RAM_PENALTY = -10.0  # the ship collided with an alien
SHIP_DEATH_REWARD = -15.0  # all hearts gone (episode over)
SHIP_DODGE_REWARD = 1.5  # an alien bullet passed within DODGE_RADIUS without hitting
SHIP_DODGE_RADIUS = 150.0
ALIEN_HIT_REWARD = 2.0  # fire agent: a shot damaged an alien
ALIEN_KILL_REWARD = 6.0  # fire agent: that shot destroyed the alien
SHOT_MISS_PENALTY = -0.15  # fire agent: a shot left the screen without hitting

logger = logging.getLogger("train_ship")


class Stats:
    """Minimal stand-in for GameStats during training."""

    def __init__(self) -> None:
        self.game_active = True
        self.credits_active = False
        self.score = 0
        self.ships_left = 2


class ShipTrainer:
    """Owns the headless world used to train and evaluate the auto-pilot."""

    def __init__(self, args: argparse.Namespace):
        self.args = args
        self.settings = Settings()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        TextureAtlas.initialize()

        # Real (already trained) enemies provide the opposition.
        self.enemy_controller = rl.init_controller()

        self.save_dir = Path(args.save_dir) if args.save_dir else RL_DATA_DIR
        self.autopilot = rl.init_autopilot(self.save_dir)
        if args.fresh or self.autopilot.movement is None:
            self.autopilot.movement = QLearningAgent(
                "ship_movement",
                features.RELATIVE_MOVEMENT_ACTIONS,
                alpha=args.alpha,
                gamma=args.gamma,
                space_id=features.SHIP_STATE_SPACE,
            )
        if args.fresh or self.autopilot.fire is None:
            self.autopilot.fire = QLearningAgent(
                "ship_fire",
                features.FIRE_ACTIONS,
                alpha=args.alpha,
                gamma=args.gamma,
                space_id=features.SHIP_STATE_SPACE,
            )

        self.rng = random.Random(args.seed)
        if args.seed is not None:
            random.seed(args.seed)

    # --- One episode --------------------------------------------------------

    def run_episode(self, *, training: bool, active: bool, epsilon: float, max_seconds: float) -> dict:
        autopilot = self.autopilot
        settings = self.settings
        movement_agent = autopilot.movement
        fire_agent = autopilot.fire

        autopilot.training = training
        autopilot.active = active
        autopilot.play_epsilon = epsilon
        autopilot.last_movement_decision = None
        autopilot.last_fire = None
        autopilot.now_ms = 0.0
        autopilot._last_fire_ms = -10_000
        autopilot._cooldown = 0

        ship = Ship(Input())
        ship.center_ship()
        health = Health()
        health.reset()
        stats = Stats()

        aliens: Group = Group()
        ship_bullets: Group = Group()
        alien_bullets: Group = Group()
        fire_pending: dict = {}
        near_misses: set = set()

        total_frames = max(1, int(max_seconds * settings.fps))
        fire_every = max(1, int(settings.fps // 10))  # alien fire cadence, as in the game
        fire_pass = 0

        pending = None  # (state, relative action) awaiting its movement reward
        carry = 0.0  # event rewards (dodge/hit/ram) since the last decision
        frames_survived = total_frames
        outcome = "timeout"
        results = {"kills": 0, "hits_taken": 0, "shots": 0, "dodges": 0, "hearts_left": health.current_hearts}

        def close_movement(next_state, done: bool, extra: float = 0.0) -> None:
            nonlocal pending, carry
            if pending is None:
                carry = 0.0
                return
            state, action = pending
            movement_agent.learn(state, action, extra + carry, next_state, done)
            pending = None
            carry = 0.0

        def resolve_shot(bullet, reward: float) -> None:
            shot = fire_pending.pop(bullet, None)
            if shot is not None:
                fire_agent.learn(
                    shot[0], shot[1], reward, features.ship_fire_state(ship, aliens), False
                )

        for frame in range(total_frames):
            frames_survived = frame + 1

            # --- Enemies: real movement, real fire function ---
            for alien in aliens.sprites():
                alien.update(ship, ship_bullets)
            for alien in aliens.copy():
                rect = alien.rect
                if rect.right < 0 or rect.left > SCREEN_WIDTH or rect.bottom < 0 or rect.top > SCREEN_HEIGHT:
                    aliens.remove(alien)

            if frame % fire_every == 0:
                self.enemy_controller.clock_override = frame * (1000.0 / settings.fps)
                gf.alien_fire(settings, stats, self.screen, aliens, alien_bullets, ship)
                if fire_pass % 10 == 0:
                    gf.spawn_random_alien(settings, screen=self.screen, aliens=aliens)
                fire_pass += 1

            # --- Ship: auto-pilot decides, Ship applies ---
            autopilot.now_ms = frame * (1000.0 / settings.fps)
            autopilot.plan(ship, aliens, alien_bullets)
            ship.update()
            autopilot.apply_aim(ship)

            if autopilot.last_movement_decision is not None:
                close_movement(autopilot.last_movement_decision[0], False)
                if training:
                    pending = autopilot.last_movement_decision

            if autopilot.should_fire(ship, aliens, ship_bullets):
                bullet = ShipBullet(ship)
                ship_bullets.add(bullet)
                results["shots"] += 1
                if training and autopilot.last_fire is not None:
                    fire_pending[bullet] = autopilot.last_fire

            # --- Bullets fly ---
            ship_bullets.update()
            alien_bullets.update()

            for bullet in ship_bullets.copy():
                if offscreen(bullet):
                    ship_bullets.remove(bullet)
                    resolve_shot(bullet, SHOT_MISS_PENALTY)
            for bullet in alien_bullets.copy():
                if offscreen(bullet):
                    alien_bullets.remove(bullet)

            # --- Dodge accounting: alien bullets that came close then flew past ---
            for bullet in alien_bullets:
                if math.hypot(bullet.rect.centerx - ship.rect.centerx, bullet.rect.centery - ship.rect.centery) <= SHIP_DODGE_RADIUS:
                    near_misses.add(bullet)
            for bullet in list(near_misses):
                if bullet not in alien_bullets:
                    near_misses.discard(bullet)
                    continue
                away_x = ship.rect.centerx - bullet.rect.centerx
                away_y = ship.rect.centery - bullet.rect.centery
                if -math.sin(bullet.angle) * away_x + -math.cos(bullet.angle) * away_y <= 0:
                    near_misses.discard(bullet)
                    carry += SHIP_DODGE_REWARD
                    results["dodges"] += 1

            # --- Ship bullets vs aliens ---
            for alien in aliens.sprites():
                hits = pygame.sprite.spritecollide(alien, ship_bullets, True)
                if not hits:
                    continue
                for bullet in hits:
                    alien.health -= 1
                    if alien.health <= 0:
                        aliens.remove(alien)
                        resolve_shot(bullet, ALIEN_HIT_REWARD + ALIEN_KILL_REWARD)
                        results["kills"] += 1
                    else:
                        resolve_shot(bullet, ALIEN_HIT_REWARD)

            # --- Alien bullets vs ship ---
            hit = pygame.sprite.spritecollideany(ship, alien_bullets)
            if hit is not None:
                alien_bullets.remove(hit)
                carry += SHIP_HIT_PENALTY
                results["hits_taken"] += 1
                health.decrease(stats)
                if not stats.game_active:
                    close_movement(None, True, SHIP_DEATH_REWARD)
                    outcome = "dead"
                    break

            # --- Alien vs ship (ram) ---
            rammed = pygame.sprite.spritecollideany(ship, aliens)
            if rammed is not None:
                aliens.remove(rammed)
                carry += SHIP_RAM_PENALTY
                health.decrease(stats)
                if not stats.game_active:
                    close_movement(None, True, SHIP_DEATH_REWARD)
                    outcome = "dead"
                    break
                # Surviving a ram still hurts (and the penalty lands now).
                close_movement(None, False)
        else:
            close_movement(None, True, 0.0)

        results["frames"] = frames_survived
        results["outcome"] = outcome
        results["hearts_left"] = health.current_hearts
        return results

    # --- Training -----------------------------------------------------------

    def train(self) -> None:
        args = self.args
        autopilot = self.autopilot
        recent: deque = deque(maxlen=100)
        started = time.time()

        logger.info("Training the ship auto-pilot for %d episodes (max %.1fs each)...", args.episodes, args.max_seconds)

        for episode in range(1, args.episodes + 1):
            epsilon = max(args.epsilon_min, args.epsilon * (args.epsilon_decay ** episode))
            alpha = max(args.alpha_min, args.alpha * (args.alpha_decay ** episode))
            autopilot.movement.alpha = alpha
            autopilot.fire.alpha = alpha

            recent.append(self.run_episode(training=True, active=True, epsilon=epsilon, max_seconds=args.max_seconds))

            if episode % args.log_every == 0:
                self._log_progress(episode, recent, epsilon, alpha, started)

        self.save()
        logger.info("Training finished in %.1fs", time.time() - started)

    def _log_progress(self, episode: int, recent: deque, epsilon: float, alpha: float, started: float) -> None:
        count = len(recent)
        survival = sum(r["frames"] for r in recent) / count / self.settings.fps
        dead = sum(r["outcome"] == "dead" for r in recent) / count * 100
        kills = sum(r["kills"] for r in recent) / count
        hits = sum(r["hits_taken"] for r in recent) / count
        dodges = sum(r["dodges"] for r in recent) / count
        logger.info(
            "ep %5d | survival %5.1fs | died %3.0f%% | kills %4.1f | hits taken %4.1f | dodges %4.1f"
            " | eps %.2f | alpha %.3f | states %d/%d | %4.0fs",
            episode,
            survival,
            dead,
            kills,
            hits,
            dodges,
            epsilon,
            alpha,
            len(self.autopilot.movement),
            len(self.autopilot.fire),
            time.time() - started,
        )

    def save(self) -> None:
        self.autopilot.movement.save(self.save_dir / SHIP_MOVEMENT_FILE)
        self.autopilot.fire.save(self.save_dir / SHIP_FIRE_FILE)
        logger.info(
            "Saved %d ship movement states -> %s and %d fire states -> %s",
            len(self.autopilot.movement),
            self.save_dir / SHIP_MOVEMENT_FILE,
            len(self.autopilot.fire),
            self.save_dir / SHIP_FIRE_FILE,
        )

    # --- Evaluation ---------------------------------------------------------

    def evaluate(self, episodes: int) -> None:
        logger.info("=== Ship evaluation: %d episodes per mode, max %.1fs each ===", episodes, self.args.max_seconds)
        logger.info(
            "%-22s %9s %7s %7s %9s %9s %9s",
            "mode",
            "survival",
            "died",
            "kills/ep",
            "hits/ep",
            "dodges/ep",
            "accuracy",
        )

        for label, active in (("RL auto-pilot", True), ("Aim & fire only", False)):
            results = [
                self.run_episode(training=False, active=active, epsilon=0.0, max_seconds=self.args.max_seconds)
                for _ in range(episodes)
            ]
            count = len(results)
            survival = sum(r["frames"] for r in results) / count / self.settings.fps
            dead = sum(r["outcome"] == "dead" for r in results) / count * 100
            kills = sum(r["kills"] for r in results) / count
            hits = sum(r["hits_taken"] for r in results) / count
            dodges = sum(r["dodges"] for r in results) / count
            shots = max(1, sum(r["shots"] for r in results))
            accuracy = sum(r["kills"] for r in results) / shots * 100
            logger.info(
                "%-22s %8.1fs %6.0f%% %7.1f %9.1f %9.1f %8.0f%%",
                label,
                survival,
                dead,
                kills,
                hits,
                dodges,
                accuracy,
            )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--episodes", type=int, default=8000, help="number of training episodes (default: 8000)")
    parser.add_argument("--max-seconds", type=float, default=20.0, help="time limit per episode (default: 20)")
    parser.add_argument("--eval", type=int, default=0, metavar="N", help="run N evaluation episodes per mode instead of training")
    parser.add_argument("--fresh", action="store_true", help="discard existing Q-tables and start over")
    parser.add_argument("--save-dir", default=None, help="where to write the Q-tables (default: data/rl)")
    parser.add_argument("--alpha", type=float, default=0.3, help="initial learning rate")
    parser.add_argument("--alpha-min", type=float, default=0.03)
    parser.add_argument("--alpha-decay", type=float, default=0.9996)
    parser.add_argument("--gamma", type=float, default=0.95, help="discount factor")
    parser.add_argument("--epsilon", type=float, default=0.4, help="initial exploration rate")
    parser.add_argument("--epsilon-min", type=float, default=0.05)
    parser.add_argument("--epsilon-decay", type=float, default=0.9996)
    parser.add_argument("--seed", type=int, default=None, help="random seed for reproducibility")
    parser.add_argument("--log-every", type=int, default=250, help="progress log interval (episodes)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)

    trainer = ShipTrainer(args)
    if args.eval > 0:
        trainer.evaluate(args.eval)
    else:
        trainer.train()
    return 0


if __name__ == "__main__":
    sys.exit(main())

"""A tiny tabular Q-learning agent (pure Python, no dependencies).

The same agent class is used by ``train_rl.py`` (which writes Q-values)
and by the in-game controller (which only reads them), so training and
inference can never drift apart.
"""

from __future__ import annotations

import json
import random
from pathlib import Path


class QLearningAgent:
    """Tabular Q-learning over small discrete state tuples.

    Q-values are stored as one list per state, aligned with ``actions``.
    """

    def __init__(
        self,
        name: str,
        actions: tuple[str, ...] | list[str],
        alpha: float = 0.25,
        gamma: float = 0.95,
        space_id: str = "",
    ):
        self.name = name
        self.actions = list(actions)
        self.alpha = alpha
        self.gamma = gamma
        # Identifies the state encoding the table was trained for, so an
        # outdated table is rejected instead of silently misinterpreted.
        self.space_id = space_id
        # state_key -> [q_value_per_action]
        self.q: dict[str, list[float]] = {}

    @staticmethod
    def state_key(state: tuple[int, ...]) -> str:
        """Serialise a discrete state tuple into a hashable key."""
        return ",".join(str(int(value)) for value in state)

    def is_known(self, state: tuple[int, ...]) -> bool:
        """Return True if the state has been visited before."""
        return self.state_key(state) in self.q

    def values(self, state: tuple[int, ...]) -> list[float] | None:
        """Return the Q-value row for a state, or None if unseen."""
        return self.q.get(self.state_key(state))

    def act(self, state: tuple[int, ...], epsilon: float = 0.0) -> int:
        """Epsilon-greedy action selection; returns an index into actions."""
        if random.random() < epsilon:
            return random.randrange(len(self.actions))

        row = self.q.get(self.state_key(state))
        if row is None:
            # Unseen state: every action is equally unknown, pick at random.
            return random.randrange(len(self.actions))

        best_value = max(row)
        best_actions = [index for index, value in enumerate(row) if value == best_value]
        return random.choice(best_actions)

    def learn(self, state: tuple[int, ...], action: int, reward: float, next_state: tuple[int, ...] | None, done: bool) -> None:
        """Apply one Q-learning update."""
        row = self.q.setdefault(self.state_key(state), [0.0] * len(self.actions))

        if done or next_state is None:
            target = reward
        else:
            next_row = self.q.get(self.state_key(next_state))
            # Unseen next states are optimistically (and safely) valued at 0.
            best_next = max(next_row) if next_row is not None else 0.0
            target = reward + self.gamma * best_next

        row[action] += self.alpha * (target - row[action])

    def save(self, path: str | Path) -> None:
        """Write the Q-table to a JSON file (states sorted for stable diffs)."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "name": self.name,
            "actions": self.actions,
            "alpha": self.alpha,
            "gamma": self.gamma,
            "space_id": self.space_id,
            "q": {key: [round(value, 6) for value in row] for key, row in sorted(self.q.items())},
        }
        path.write_text(json.dumps(payload), encoding="utf-8")

    @classmethod
    def load(cls, path: str | Path) -> "QLearningAgent":
        """Read a Q-table previously written by :meth:`save`."""
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        agent = cls(
            payload["name"],
            payload["actions"],
            alpha=payload.get("alpha", 0.25),
            gamma=payload.get("gamma", 0.95),
            space_id=payload.get("space_id", ""),
        )
        agent.q = {key: list(row) for key, row in payload["q"].items()}
        return agent

    def __len__(self) -> int:
        return len(self.q)

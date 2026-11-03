import zmq
import json
import os
import subprocess
import gymnasium as gym
from gymnasium import spaces
import numpy as np
from env.observation import OBSERVATION_SIZE, build_observation
from env.rewards import compute_reward
from env.route import DoorRoute

PROTOCOL_VERSION = 5
MAX_EPISODE_STEPS = 6000  # decyzji na gre w treningu i ocenie; 3000 nie starczalo na dojscie do bossa na poziomie 1

class RogueLikeEnv(gym.Env):
    def __init__(self, port=5555, sim_path=None, frame_skip=4, extra_args=()):
        """Bez sim_path laczy sie z juz uruchomiona gra (RogueLikeGame --ai-mode)."""
        super().__init__()
        self.process = None
        if sim_path:
            self.process = subprocess.Popen(
                [sim_path, "--port", str(port), "--frame-skip", str(frame_skip), *extra_args],
                cwd=os.path.dirname(sim_path),
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.setsockopt(zmq.RCVTIMEO, 30000)
        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.connect(f"tcp://127.0.0.1:{port}")
        self.action_space = spaces.Discrete(6)
        self.observation_space = spaces.Box(low=-1, high=1, shape=(OBSERVATION_SIZE,), dtype=np.float32)
        self.visited_maps = set()
        self.visited_tiles = {}
        self.route = DoorRoute()
        self.key_potential = None
        self.max_level = 0

    def _request(self, command):
        self.socket.send_string(command)
        state = json.loads(self.socket.recv_string())
        if state.get("protocol") != PROTOCOL_VERSION:
            raise RuntimeError(f"Niezgodny protokol gry: {state.get('protocol')}, oczekiwano {PROTOCOL_VERSION}")
        return state

    def _observation(self, state):
        tiles = self.visited_tiles.setdefault((state["level"], state["map"]), set())
        tiles.add((state["playerX"], state["playerY"]))
        return build_observation(state, tiles, self.visited_maps, self.route.target(state),
                                 self.route.explore_target(state, self.visited_maps))

    def _key_progress(self, state):
        # Tylko gdy klucz byl i jest, zeby podniesienie i uzycie klucza nie zmienialo potencjalu
        potential = self.route.potential(state)
        progress = 0.0 if potential is None or self.key_potential is None else potential - self.key_potential
        self.key_potential = potential
        return progress

    def step(self, action):
        state = self._request(str(int(action)))
        current_map = (state["level"], state["map"])
        entered_new_map = current_map not in self.visited_maps
        entered_new_level = state["level"] > self.max_level
        self.max_level = max(self.max_level, state["level"])
        self.visited_maps.add(current_map)
        self.route.update(state)
        done = not state["alive"] or state["won"]
        info = {"state": state, "new_map": entered_new_map}
        reward = compute_reward(state, entered_new_map, self._key_progress(state), entered_new_level)
        return self._observation(state), reward, done, False, info

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        state = self._request("reset")
        self.visited_tiles = {}
        self.visited_maps = {(state["level"], state["map"])}
        self.max_level = state["level"]
        self.route = DoorRoute()
        self.route.update(state)
        self.key_potential = self.route.potential(state)
        return self._observation(state), {}

    def close(self):
        self.socket.close()
        self.context.term()
        if self.process:
            self.process.terminate()
            self.process.wait()
        super().close()

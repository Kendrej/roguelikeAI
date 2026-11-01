import zmq
import json
import os
import subprocess
import gymnasium as gym
from gymnasium import spaces
import numpy as np
from env.rewards import compute_reward

PROTOCOL_VERSION = 2

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
        self.action_space = spaces.Discrete(5)
        self.observation_space = spaces.Box(low=-5, high=500, shape=(504,), dtype=np.float32)

    def _request(self, command):
        self.socket.send_string(command)
        state = json.loads(self.socket.recv_string())
        if state.get("protocol") != PROTOCOL_VERSION:
            raise RuntimeError(f"Niezgodny protokol gry: {state.get('protocol')}, oczekiwano {PROTOCOL_VERSION}")
        return state

    def _observation(self, state):
        extras = np.array([state["hp"], state["playerX"], state["playerY"], state["key"]], dtype=np.float32)
        grid_flat = np.array(state["grid"], dtype=np.float32).flatten()
        enemies_values = []
        for e in state["enemies"]:
            enemies_values.extend([e['type'], e['x'], e['y'], e['hp']])
        enemies_flat = np.array(enemies_values, dtype=np.float32)
        return np.concatenate((enemies_flat, grid_flat, extras))

    def step(self, action):
        state = self._request(str(int(action)))
        done = not state["alive"] or state["won"]
        return self._observation(state), compute_reward(state), done, False, {}

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        state = self._request("reset")
        return self._observation(state), {}

    def close(self):
        self.socket.close()
        self.context.term()
        if self.process:
            self.process.terminate()
            self.process.wait()
        super().close()

import zmq
import json
import gymnasium as gym
from gymnasium import spaces
import numpy as np

class RogueLikeEnv(gym.Env):
    def __init__(self):
        super().__init__()
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.setsockopt(zmq.RCVTIMEO, 5000)
        self.socket.setsockopt(zmq.LINGER, 0)
        self.socket.connect("tcp://localhost:5555")
        self.action_space = spaces.Discrete(5)
        self.observation_space = spaces.Box(low=-5, high=500, shape=(504,), dtype=np.float32)

    def step(self, action):
        self.socket.send_string(str(action))
        #print(f"Sent action: {action!r}")
        response = self.socket.recv_string()
        response_data = json.loads(response)
        #print(f"Received response: {response!r}")
        extras = np.array([response_data["hp"], response_data["playerX"], response_data["playerY"], response_data["key"]], dtype=np.float32)
        grid = response_data["grid"]
        grid_flat = np.array(grid, dtype=np.float32).flatten()
        enemies = response_data["enemies"]
        enemies_values = []
        for e in enemies:
            enemies_values.extend([e['type'], e['x'], e['y'], e['hp']])

        enemies_flat = np.array(enemies_values, dtype=np.float32)
        observation = np.concatenate((enemies_flat,grid_flat, extras))
        reward = response_data["reward"]
        done = not response_data["alive"]
        info = {}
        return observation, reward, done, False, info
    
    def reset(self, seed=None, options=None):
        self.socket.send_string("reset")
        #print("Sent reset command: '0'")
        response = self.socket.recv_string()
        response_data = json.loads(response)
        #print(f"Received response: {response!r}")
        extras = np.array([response_data["hp"], response_data["playerX"], response_data["playerY"], response_data["key"]], dtype=np.float32)
        grid = response_data["grid"]
        grid_flat = np.array(grid, dtype=np.float32).flatten()
        enemies = response_data["enemies"]
        enemies_values = []
        for e in enemies:
            enemies_values.extend([e['type'], e['x'], e['y'], e['hp']])

        enemies_flat = np.array(enemies_values, dtype=np.float32)
        observation = np.concatenate((enemies_flat,grid_flat, extras))
        #print(f"Initial observation: {observation!r}")
        info = {}
        return observation, info
    
    def close(self):
        self.socket.close()
        self.context.term()
        super().close()
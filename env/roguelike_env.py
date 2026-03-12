# from multiprocessing import context

# import zmq
# import random
# import time
# import json

# def main():
#     print("Agent is starting...")
#     context = zmq.Context()
#     socket = context.socket(zmq.REQ)
#     socket.setsockopt(zmq.RCVTIMEO, 5000)
#     socket.setsockopt(zmq.LINGER, 0)

#     try:
#         socket.connect("tcp://localhost:5555")
#         while True:
#             random_movement = str(random.randint(0, 3))
#             print(f"Sending: {random_movement!r}")
#             socket.send_string(random_movement)
#             response = socket.recv_string()
#             response_data = json.loads(response)
#             hp = response_data["hp"]
#             alive = response_data["alive"]
#             print(f"Received response: {response!r}, HP: {hp}, Alive: {alive}")
#             if not alive:
#                 print("Agent has died. Stopping.")
#                 break
#     except zmq.error.Again:
#         print("No response received within the timeout period.")
#     finally:
#         socket.close()
#         context.term()


# if __name__ == "__main__":
#     main()



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
        self.observation_space = spaces.Box(low=0, high=255, shape=(483,), dtype=np.float32)

    def step(self, action):
        self.socket.send_string(str(action))
        #print(f"Sent action: {action!r}")
        response = self.socket.recv_string()
        response_data = json.loads(response)
        #print(f"Received response: {response!r}")
        extras = np.array([response_data["hp"], response_data["playerX"], response_data["playerY"]], dtype=np.float32)
        grid = response_data["grid"]
        grid_flat = np.array(grid, dtype=np.float32).flatten()
        observation = np.concatenate((grid_flat, extras))
        reward = response_data["reward"]
        done = not response_data["alive"]
        info = {}
        return observation, reward, done, False, info
    
    def reset(self, seed=None, options=None):
        self.socket.send_string("0")
        #print("Sent reset command: '0'")
        response = self.socket.recv_string()
        response_data = json.loads(response)
        #print(f"Received response: {response!r}")
        extras = np.array([response_data["hp"], response_data["playerX"], response_data["playerY"]], dtype=np.float32)
        grid = response_data["grid"]
        grid_flat = np.array(grid, dtype=np.float32).flatten()
        observation = np.concatenate((grid_flat, extras))
        info = {}
        return observation, info
    
    def close(self):
        self.socket.close()
        self.context.term()
        super().close()
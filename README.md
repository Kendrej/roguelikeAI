# RogueLike AI (Reinforcement Learning)

An Artificial Intelligence agent based on Reinforcement Learning, developed for autonomous gameplay in a custom C++ game engine: [RogueLike](https://github.com/Kendrej/RogueLikeGame). 

This repository contains the model architecture, a custom environment based on the Gymnasium API, and the Inter-Process Communication (IPC) system.

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Gymnasium](https://img.shields.io/badge/Gymnasium-API-brightgreen.svg)](https://gymnasium.farama.org/)
[![Stable Baselines3](https://img.shields.io/badge/Stable_Baselines3-PPO-orange.svg)](https://stable-baselines3.readthedocs.io/)
[![ZeroMQ](https://img.shields.io/badge/ZeroMQ-IPC-red.svg)](https://zeromq.org/)

---

## About the Project

This project separates the machine learning logic (Python) from the game engine (C++). The model learns to navigate dungeons, avoid obstacles, and reach the exit using the **Proximal Policy Optimization (PPO)** algorithm.

### Key Features

* **Custom Gymnasium Environment** - A full implementation of `gymnasium.Env` tailored to the game's unique mechanics.
* **IPC Communication (ZeroMQ)** - Asynchronous data exchange (game state, actions, rewards) with the C++ environment via ZeroMQ sockets.
* **Reward Shaping** - An advanced reward system solving the *sparse rewards* problem, utilizing penalties for hitting walls and micro-rewards for decreasing the distance to the goal.
* **Hyperparameter Tuning** - Finely-tuned entropy and episode length (3000 steps) to prevent the agent from getting stuck in local minima.

---

## Technologies

| Category | Technology / Library |
| --- | --- |
| **Language** | Python 3.9+ |
| **RL Algorithms** | Stable Baselines3 |
| **AI Environment** | Gymnasium |
| **Neural Networks** | PyTorch |
| **Game Communication** | PyZMQ (ZeroMQ) |
| **Math Operations** | NumPy |

---

## Architecture

The repository is organized as follows:

```text
roguelikeAI/
├── envs/                 # Custom Gymnasium environment
│   ├── roguelike_env.py  # Environment logic and ZeroMQ integration
│   └── __init__.py       # Environment registration
├── checkpoints/          # Saved model weights (.zip)
├── logs/                 # Training metrics and TensorBoard logs
├── train.py              # Main script for training the PPO agent
└── README.md             # Project documentation
```

### Communication Cycle (ZeroMQ REQ/REP):
1. **Agent (Python)** sends the chosen action to the game.
2. **Game (C++)** executes the physics step and calculates the new state.
3. **Game (C++)** sends back the updated observation vector and reward.
4. **Agent (Python)** updates the neural network policy.

---

## Reward Shaping System

The game only reports raw events; the reward is computed in Python (`env/rewards.py`):

| Category | Event | Reward | Purpose |
| :--- | :--- | :--- | :--- |
| **Survival** | Every Step | `-0.001` | Small time penalty against standing still. |
| **Exploration** | New Tile Visited | `+0.01` | Counted once per tile on each map. |
| **Progression** | First Visit to a Map | `+2.0` | Going back and forth through a door pays nothing. |
| **Progression** | Picking up / Using a Key | `+2.0` each | Opens the locked door to the next level. |
| **Combat** | Killing an Enemy | `+1.0` | Clear incentive to eliminate threats. |
| **Combat** | Clearing a Room | `+3.0` | Doors open only after every enemy on the map is dead. |
| **Combat** | Dealing / Taking Damage | `±0.01 per HP` | Rewards offence, penalises poor positioning. |
| **Outcome** | Game Won | `+10.0` | Ultimate objective. |
| **Outcome** | Player Death | `-1.0` | Terminal failure. |

The agent has 6 actions: move up/down/left/right, melee attack and a shot aimed automatically at the nearest enemy (the human game aims with the mouse, which the headless simulator does not have).

---

## Getting Started

1. **Prerequisites**: Build the `ai-headless` branch of the [RogueLike Game](https://github.com/Kendrej/RogueLikeGame). It produces `RogueLikeGame` (windowed) and `RogueLikeSim` (no graphics).
2. **Setup**:
   ```bash
   pip install stable-baselines3[extra] gymnasium pyzmq numpy
   ```
3. **Running** (Windows, with both repositories in the same folder): the first run installs dependencies into `.venv`.
   * `train.bat` trains without graphics and starts the simulators itself. Extra options such as `--timesteps 1000000` are passed through.
   * `watch.bat` opens the game and shows the newest model from `checkpoints/`. Use `--speed 3` to play faster.
4. **Monitoring**:
   Track the learning progress using TensorBoard:
   ```bash
   tensorboard --logdir logs/
   ```

---

## Author

* GitHub: [@Kendrej](https://github.com/Kendrej)

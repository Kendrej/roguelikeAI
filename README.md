# RogueLike AI (Reinforcement Learning)

An Artificial Intelligence agent based on Reinforcement Learning, developed for autonomous gameplay in a custom C++ game engine: [RogueLike Dungeon Crawler](https://github.com/Kendrej/RogueLikeGame). 

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

The agent's behavior is guided by a sophisticated multi-objective reward function implemented in the C++ engine:

| Category | Event | Reward | Purpose |
| :--- | :--- | :--- | :--- |
| **Survival** | Every Step | `-50.0 / n_steps` | Constant time penalty to encourage speed. |
| **Progression** | Picking up a Key | `+40.0` | Incentivizes interacting with key items. |
| **Progression** | Using a Key | `+40.0` | Reward for solving the door puzzle. |
| **Combat** | Killing an Enemy | `+10.0` | Clear incentive to eliminate threats. |
| **Combat** | Dealing Damage | `+0.5 per HP` | Reward for offensive actions. |
| **Defense** | Taking Damage | `-0.5 per HP` | Penalty for poor positioning/defense. |
| **Exploration** | New Tile Visited | `+25.0 / 480` | Encourages exploring the entire 30x16 grid. |
| **Progression** | Next Floor | `+100.0` | Massive reward for map completion. |
| **Outcome** | Game Won | `+500.0` | Ultimate objective. |
| **Outcome** | Player Death | `-100.0` | Strong penalty for terminal failure. |

---

## Getting Started

1. **Prerequisites**: Ensure you have the [RogueLike Game](https://github.com/Kendrej/RogueLikeGame) compiled and running in AI mode.
2. **Setup**:
   ```bash
   pip install stable-baselines3[extra] gymnasium pyzmq numpy
   ```
3. **Training**:
   Start the game server, then run the training script:
   ```bash
   python train.py
   ```
4. **Monitoring**:
   Track the learning progress using TensorBoard:
   ```bash
   tensorboard --logdir logs/
   ```

---

## Author

* GitHub: [@Kendrej](https://github.com/Kendrej)
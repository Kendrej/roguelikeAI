"""Porownuje model z losowym graczem, zeby bylo widac, czy trening cos daje."""
import argparse
import random
import statistics

from stable_baselines3 import PPO

from env.paths import find_executable
from env.roguelike_env import RogueLikeEnv
from gymnasium.wrappers import TimeLimit
from watch import newest_model

MAX_STEPS = 3000


def play(policy, port, episodes):
    env = TimeLimit(RogueLikeEnv(port=port, sim_path=find_executable("RogueLikeSim")), max_episode_steps=MAX_STEPS)
    rewards, steps, maps, kills, deaths, keys, wins = [], [], [], [], 0, 0, 0
    for _ in range(episodes):
        obs, _ = env.reset()
        total = 0.0
        new_maps = killed = length = 0
        done = False
        while not done:
            obs, reward, terminated, truncated, info = env.step(policy(obs))
            done = terminated or truncated
            state = info["state"]
            total += reward
            length += 1
            new_maps += info["new_map"]
            killed += state["events"]["enemiesKilled"]
            keys += state["events"]["keysPicked"]
            wins += state["won"]
            deaths += not state["alive"]
        rewards.append(total)
        steps.append(length)
        maps.append(new_maps)
        kills.append(killed)
    env.close()
    return (f"nagroda {statistics.mean(rewards):7.2f} | kroki {statistics.mean(steps):5.0f} | nowe mapy {statistics.mean(maps):.2f} "
            f"(max {max(maps)}) | zabici {statistics.mean(kills):.2f} | smierci {deaths}/{episodes} | klucze {keys} | wygrane {wins}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=None)
    parser.add_argument("--episodes", type=int, default=50)
    args = parser.parse_args()

    rng = random.Random(1)
    print("losowy:", play(lambda _: rng.randrange(5), 5590, args.episodes))
    model_path = args.model or newest_model()
    model = PPO.load(model_path, device="cpu")
    print(f"model ({model.num_timesteps} krokow):", play(lambda obs: model.predict(obs, deterministic=False)[0], 5591, args.episodes))


if __name__ == "__main__":
    main()

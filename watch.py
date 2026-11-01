import argparse
import glob
import os
import time

from stable_baselines3 import PPO
import zmq

from env.paths import find_executable
from env.roguelike_env import RogueLikeEnv

WATCH_PORT = 5599
FRAME_SKIP = 4
DECISIONS_PER_SECOND = 60 / FRAME_SKIP


def newest_model():
    files = glob.glob(os.path.join(os.path.dirname(os.path.abspath(__file__)), "checkpoints", "*.zip"))
    if not files:
        raise FileNotFoundError("Brak modelu w checkpoints/. Najpierw uruchom trening.")
    return max(files, key=os.path.getmtime)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default=None, help="domyslnie najnowszy z checkpoints/")
    parser.add_argument("--speed", type=float, default=1.0, help="tempo wzgledem normalnej gry")
    parser.add_argument("--seconds", type=float, default=None, help="domyslnie do zamkniecia okna")
    args = parser.parse_args()

    model_path = args.model or newest_model()
    model = PPO.load(model_path, device="cpu")
    print(f"Model: {model_path} ({model.num_timesteps} krokow treningu)")

    env = RogueLikeEnv(port=WATCH_PORT, sim_path=find_executable("RogueLikeGame"), frame_skip=FRAME_SKIP, extra_args=["--ai-mode"])
    delay = 1.0 / (DECISIONS_PER_SECOND * args.speed)
    start = time.perf_counter()
    try:
        obs, _ = env.reset()
        while args.seconds is None or time.perf_counter() - start < args.seconds:
            action, _ = model.predict(obs, deterministic=False)
            obs, _, done, _, _ = env.step(action)
            if done:
                obs, _ = env.reset()
            time.sleep(delay)
    except (zmq.Again, KeyboardInterrupt):
        print("Koniec podgladu")
    finally:
        env.close()


if __name__ == "__main__":
    main()

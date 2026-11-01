import os

GAME_REPO = os.environ.get(
    "ROGUELIKE_GAME_REPO",
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "RogueLikeGame"),
)


def find_executable(name):
    path = os.path.normpath(os.path.join(GAME_REPO, "build", "win-ninja-release", "bin", f"{name}.exe"))
    if not os.path.exists(path):
        raise FileNotFoundError(f"Nie znaleziono {path}. Zbuduj gre presetem win-ninja-release (galaz ai-headless).")
    return path

import numpy as np

VIEW_RADIUS = 5
VIEW_SIZE = 2 * VIEW_RADIUS + 1
CHANNELS = 5  # sciana lub zamkniete drzwi, otwarte drzwi, wrog, przedmiot, odwiedzone pole
MAX_ENEMIES = 3
GRID_WIDTH = 30
GRID_HEIGHT = 16
MAX_ENEMY_HP = 250.0
MAX_ENEMY_COUNT = 10.0
VECTOR_SIZE = 12 + 5 * MAX_ENEMIES + 3 + 3
OBSERVATION_SIZE = CHANNELS * VIEW_SIZE * VIEW_SIZE + VECTOR_SIZE


def _relative(target, px, py):
    return (target[0] - px) / GRID_WIDTH, (target[1] - py) / GRID_HEIGHT


def _nearest(points, px, py):
    return min(points, key=lambda p: abs(p[0] - px) + abs(p[1] - py), default=None)


def build_observation(state, visited_tiles, visited_maps):
    """Widok wokol gracza plus kierunki do celow; wszystkie wartosci w zakresie -1..1."""
    px, py = state["playerX"], state["playerY"]
    grid = np.array(state["grid"], dtype=np.int8)

    view = np.zeros((CHANNELS, VIEW_SIZE, VIEW_SIZE), dtype=np.float32)
    view[0] = 1.0  # poza mapa traktujemy jak sciane
    x0, x1 = max(px - VIEW_RADIUS, 0), min(px + VIEW_RADIUS + 1, GRID_WIDTH)
    y0, y1 = max(py - VIEW_RADIUS, 0), min(py + VIEW_RADIUS + 1, GRID_HEIGHT)
    if x0 < x1 and y0 < y1:
        dx, dy = x0 - (px - VIEW_RADIUS), y0 - (py - VIEW_RADIUS)
        part = grid[y0:y1, x0:x1]
        h, w = part.shape
        view[0, dy:dy + h, dx:dx + w] = (part == 1) | (part == 3)
        view[1, dy:dy + h, dx:dx + w] = part == 2

    def mark(channel, x, y):
        vx, vy = x - px + VIEW_RADIUS, y - py + VIEW_RADIUS
        if 0 <= vx < VIEW_SIZE and 0 <= vy < VIEW_SIZE:
            view[channel, vy, vx] = 1.0

    enemies = [e for e in state["enemies"] if e["hp"] > 0]
    for e in enemies:
        mark(2, e["x"], e["y"])
    items = [(i["x"], i["y"]) for i in state["items"]]
    for x, y in items:
        mark(3, x, y)
    for x, y in visited_tiles:
        mark(4, x, y)

    # Drzwi otwieraja sie dopiero po zabiciu wszystkich wrogow na mapie
    doors_closed = state["enemyCount"] > 0

    vector = [
        state["hp"] / 100.0,
        float(state["key"]),
        float(state["lockedDoor"]),
        float(state["meleeReady"]),
        float(state["rangedReady"]),
        np.clip(state["facingX"], -1, 1),
        np.clip(state["facingY"], -1, 1),
        state["fracX"],
        state["fracY"],
        min(state["enemyCount"] / MAX_ENEMY_COUNT, 1.0),
        float(doors_closed),
        state["level"],
    ]

    enemies.sort(key=lambda e: abs(e["x"] - px) + abs(e["y"] - py))
    for i in range(MAX_ENEMIES):
        if i < len(enemies):
            e = enemies[i]
            rx, ry = _relative((e["x"], e["y"]), px, py)
            vector += [1.0, rx, ry, min(e["hp"] / MAX_ENEMY_HP, 1.0), e["type"] / 5.0]
        else:
            vector += [0.0, 0.0, 0.0, 0.0, 0.0]

    item = _nearest(items, px, py)
    vector += [1.0, *_relative(item, px, py)] if item else [0.0, 0.0, 0.0]

    # Wyjscie prowadzace na nieodwiedzona mape, a gdy takiego nie ma, dowolne; przy zamknietych drzwiach brak celu
    gateways = [] if doors_closed else state["gateways"]
    fresh = [(g["x"], g["y"]) for g in gateways if (g["level"], g["map"]) not in visited_maps]
    exit_tile = _nearest(fresh or [(g["x"], g["y"]) for g in gateways], px, py)
    vector += [float(bool(fresh)), *_relative(exit_tile, px, py)] if exit_tile else [0.0, 0.0, 0.0]

    return np.concatenate((view.ravel(), np.array(vector, dtype=np.float32))).astype(np.float32)

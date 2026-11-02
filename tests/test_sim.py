"""Testy integracyjne symulatora. Uruchomienie: python tests/test_sim.py <RogueLikeSim.exe> [RogueLikeGame.exe]"""
import json
import os
import random
import subprocess
import sys
import time
from collections import deque

import zmq

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from env import rewards
from env.rewards import compute_reward

SIM = None
GAME = None
RESULTS = []
next_port = 6000


class Client:
    def __init__(self, exe, *args):
        global next_port
        self.port = next_port
        next_port += 1
        self.proc = subprocess.Popen(
            [exe, "--port", str(self.port), *args], cwd=os.path.dirname(exe),
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.ctx = zmq.Context()
        self.sock = self.ctx.socket(zmq.REQ)
        self.sock.setsockopt(zmq.RCVTIMEO, 30000)
        self.sock.setsockopt(zmq.LINGER, 0)
        self.sock.connect(f"tcp://127.0.0.1:{self.port}")

    def raw(self, command):
        self.sock.send_string(command)
        return self.sock.recv_string()

    def rq(self, command):
        return json.loads(self.raw(command))

    def close(self):
        self.sock.close()
        self.ctx.term()
        self.proc.terminate()
        self.proc.wait()


def check(name, ok, detail=""):
    RESULTS.append(ok)
    print(f"{'OK  ' if ok else 'FAIL'} {name} {detail}")


def sequence(seed, n):
    rng = random.Random(seed)
    out = []
    while len(out) < n:
        # Dluzsze serie tego samego ruchu, zeby gracz realnie sie przemieszczal
        out.extend([rng.randrange(6)] * rng.randint(1, 12))
    return out[:n]


def run_sequence(client, actions):
    trace = [client.raw("reset")]
    for action in actions:
        reply = client.raw(str(action))
        trace.append(reply)
        state = json.loads(reply)
        if not state["alive"] or state["won"]:
            trace.append(client.raw("reset"))
    return trace


def test_protocol():
    c = Client(SIM)
    check("zle polecenie", c.raw("xyz") == "unknown_command")
    check("akcja spoza zakresu", c.raw("9") == "unknown_command")
    state = c.rq("reset")
    check("wersja protokolu", state["protocol"] == 4)
    check("rozmiar siatki", len(state["grid"]) == 16 and len(state["grid"][0]) == 30)
    check("5 slotow wrogow", len(state["enemies"]) == 5)
    c.rq("quit")
    check("quit konczy proces", c.proc.wait(5) == 0)
    c.close()


def test_lockstep():
    def tiles_moved(skip, steps):
        c = Client(SIM, "--frame-skip", str(skip))
        x0 = c.rq("reset")["playerX"]
        for _ in range(steps):
            x = c.rq("3")["playerX"]
        c.close()
        return x - x0

    four, one = tiles_moved(4, 20), tiles_moved(1, 80)
    check("ruch zalezy od tickow, nie od czasu", abs(four - one) <= 1 and four > 0, f"skip4={four} skip1={one}")

    c = Client(SIM)
    c.rq("reset")
    a = c.rq("3")
    time.sleep(1.0)
    b = c.rq("3")
    idle = c.rq("reset")
    time.sleep(0.5)
    check("gra stoi miedzy krokami", idle["playerX"] == c.rq("4")["playerX"], f"{a['playerX']}->{b['playerX']}")
    c.close()


def test_determinism(exe, label):
    actions = sequence(1, 4000)
    c1, c2 = Client(exe), Client(exe)
    t1, t2 = run_sequence(c1, actions), run_sequence(c2, actions)
    c1.close()
    c2.close()
    diff = next((i for i, (a, b) in enumerate(zip(t1, t2)) if a != b), None)
    check(f"powtarzalnosc miedzy procesami [{label}]", diff is None and len(t1) == len(t2), f"pierwsza roznica: {diff}, krokow {len(t1)}")


def test_reset():
    c = Client(SIM)
    first = c.raw("reset")
    run_sequence(c, sequence(2, 3000))
    check("reset przywraca stan poczatkowy", c.raw("reset") == first)
    trace = run_sequence(c, sequence(3, 500))
    trace2 = run_sequence(c, sequence(3, 500))
    diff = next((i for i, (a, b) in enumerate(zip(trace, trace2)) if a != b), None)
    check("powtarzalnosc po resecie", diff is None, f"pierwsza roznica: {diff}")
    c.close()


def test_events():
    c = Client(SIM)
    rng = random.Random(4)
    state = c.rq("reset")
    bad_hp = episodes = ended = 0
    hp_start = state["hp"]
    hp_sum = 0
    negative = False
    bad_count = 0
    # Bez strzalu, bo losowy gracz ze strzalem prawie nie ginie, a sciezka smierci tez ma byc sprawdzona
    for _ in range(30000):
        state = c.rq(str(rng.randrange(5)))
        e = state["events"]
        alive = sum(en["hp"] > 0 for en in state["enemies"])
        bad_count += alive != min(state["enemyCount"], len(state["enemies"]))
        hp_sum += e["hpDelta"]
        negative |= any(e[k] < 0 for k in ("keysPicked", "keysUsed", "enemiesKilled", "damageDealt", "newTiles", "mapsChanged", "roomsCleared"))
        if not state["alive"] or state["won"]:
            ended += 1
            bad_hp += hp_start + hp_sum != state["hp"]
            if not state["alive"]:
                after = c.rq("0")
                check_after = after["alive"] is False and not any(after["events"].values()) and after["hp"] == state["hp"]
                if not check_after:
                    bad_hp += 1000
            state = c.rq("reset")
            hp_start = state["hp"]
            hp_sum = 0
            episodes += 1
    check("zdarzenia HP sumuja sie do stanu", bad_hp == 0 and episodes > 0, f"epizodow {episodes}, bledow {bad_hp}")
    check("liczniki zdarzen nieujemne", not negative)
    check("enemyCount zgodny z lista wrogow", bad_count == 0, f"bledow {bad_count}")
    c.close()


def test_rewards():
    zero = {k: 0 for k in ("keysPicked", "keysUsed", "enemiesKilled", "damageDealt", "hpDelta", "newTiles", "mapsChanged", "roomsCleared")}

    def reward(won=False, alive=True, new_map=False, **events):
        return compute_reward({"events": {**zero, **events}, "won": won, "alive": alive}, new_map) - rewards.STEP_PENALTY

    ok = all(abs(a - b) < 1e-6 for a, b in [
        (reward(keysPicked=1), rewards.KEY_PICKED), (reward(keysUsed=1), rewards.KEY_USED),
        (reward(enemiesKilled=1), rewards.ENEMY_KILLED), (reward(roomsCleared=1), rewards.ROOM_CLEARED), (reward(damageDealt=4), 4 * rewards.DAMAGE_DEALT),
        (reward(hpDelta=-4), -4 * rewards.HP_CHANGE), (reward(newTiles=1), rewards.NEW_TILE),
        (reward(new_map=True), rewards.NEW_MAP), (reward(mapsChanged=1), 0.0),
        (reward(won=True), rewards.GAME_WON), (reward(alive=False), rewards.PLAYER_DIED)])
    check("nagrody zgodne z tabela", ok)


def test_observation():
    import numpy as np
    from env.observation import OBSERVATION_SIZE, build_observation

    c = Client(SIM)
    state = c.rq("reset")
    worst = 0.0
    bad_shape = False
    rng = random.Random(8)
    tiles = set()
    for _ in range(5000):
        tiles.add((state["playerX"], state["playerY"]))
        obs = build_observation(state, tiles, {(state["level"], state["map"])})
        bad_shape |= obs.shape != (OBSERVATION_SIZE,) or obs.dtype != np.float32
        worst = max(worst, float(np.abs(obs).max()))
        state = c.rq(str(rng.randrange(6)))
        if not state["alive"] or state["won"]:
            state = c.rq("reset")
            tiles = set()
    check("obserwacja ma staly rozmiar i zakres", not bad_shape and worst <= 1.0, f"max {worst:.3f}")
    c.close()


def test_memory():
    import ctypes
    from ctypes import wintypes

    class PMC(ctypes.Structure):
        _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [(n, ctypes.c_size_t) for n in (
            "PeakWorkingSetSize", "WorkingSetSize", "QuotaPeakPagedPoolUsage", "QuotaPagedPoolUsage",
            "QuotaPeakNonPagedPoolUsage", "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]

    def private_mb(pid):
        k = ctypes.windll.kernel32
        k.OpenProcess.restype = wintypes.HANDLE
        h = k.OpenProcess(0x1000, False, pid)
        pmc = PMC()
        pmc.cb = ctypes.sizeof(PMC)
        ctypes.windll.psapi.GetProcessMemoryInfo(wintypes.HANDLE(h), ctypes.byref(pmc), pmc.cb)
        k.CloseHandle(wintypes.HANDLE(h))
        return pmc.PagefileUsage / 1e6

    c = Client(SIM)
    rng = random.Random(5)

    def burn(steps):
        c.rq("reset")
        for i in range(steps):
            s = c.rq(str(rng.randrange(6)))
            if not s["alive"] or s["won"] or i % 500 == 0:
                c.rq("reset")

    burn(20000)
    start = private_mb(c.proc.pid)
    burn(100000)
    end = private_mb(c.proc.pid)
    check("brak wycieku pamieci", end - start < 5, f"{start:.1f} MB -> {end:.1f} MB po 100k krokach")
    c.close()


def bfs(grid, start, goals, blocked=()):
    rows, cols = len(grid), len(grid[0])
    q = deque([start])
    prev = {start: None}
    while q:
        cur = q.popleft()
        if cur in goals:
            while prev[cur] and prev[cur][0] != start:
                cur = prev[cur][0]
            return prev[cur][1] if prev[cur] else None
        x, y = cur
        for action, nx, ny in ((0, x, y - 1), (1, x, y + 1), (2, x - 1, y), (3, x + 1, y)):
            if 0 <= nx < cols and 0 <= ny < rows and (nx, ny) not in prev and grid[ny][nx] in (0, 2) and (nx, ny) not in blocked:
                prev[(nx, ny)] = (cur, action)
                q.append((nx, ny))
    return None


def test_bot(max_steps=60000, seed=6):
    """Bot strzela do wrogow i od nich odchodzi, potem wchodzi w drzwi; ma przejsc klucz, drzwi i kolejne mapy."""
    c = Client(SIM)
    rng = random.Random(seed)
    totals = {}
    maps = set()
    visited = {}
    state = c.rq("reset")
    won = False
    deaths = 0
    for _ in range(max_steps):
        pos = (state["playerX"], state["playerY"])
        maps.add(state["map"])
        seen = visited.setdefault(state["map"], set())
        seen.add(pos)
        enemies = [(e["x"], e["y"]) for e in state["enemies"] if e["hp"] > 0]
        grid = state["grid"]
        action = None
        if enemies:
            target = min(enemies, key=lambda e: abs(e[0] - pos[0]) + abs(e[1] - pos[1]))
            dist = abs(target[0] - pos[0]) + abs(target[1] - pos[1])
            if state["rangedReady"]:
                action = 5
            elif dist <= 2:
                # Strzela i ucieka, bo rycerze sa wolniejsi od gracza
                moves = [(a, (pos[0] + dx, pos[1] + dy)) for a, dx, dy in ((0, 0, -1), (1, 0, 1), (2, -1, 0), (3, 1, 0))]
                moves = [(a, n) for a, n in moves if 0 <= n[0] < 30 and 0 <= n[1] < 16 and grid[n[1]][n[0]] == 0]
                if moves:
                    action = max(moves, key=lambda m: abs(m[1][0] - target[0]) + abs(m[1][1] - target[1]))[0]
        if action is None:
            doors = {(x, y) for y, row in enumerate(grid) for x, v in enumerate(row) if v == 2 and (x, y) not in seen}
            action = bfs(grid, pos, doors) if doors else None
        if action is None or rng.random() < 0.1:
            action = rng.randrange(6)
        state = c.rq(str(action))
        for k, v in state["events"].items():
            totals[k] = totals.get(k, 0) + v
        if state["won"]:
            won = True
            break
        if not state["alive"]:
            deaths += 1
            state = c.rq("reset")
    c.close()
    return totals, maps, won, deaths


def test_windowed():
    actions = sequence(7, 1200)
    c1 = Client(SIM)
    c2 = Client(GAME, "--ai-mode")
    time.sleep(4)
    t1, t2 = run_sequence(c1, actions), run_sequence(c2, actions)
    c1.close()
    c2.close()
    diff = next((i for i, (a, b) in enumerate(zip(t1, t2)) if a != b), None)
    detail = f"pierwsza roznica: {diff}, krokow {len(t1)}"
    if diff is not None:
        a, b = json.loads(t1[diff]), json.loads(t2[diff])
        detail += " pola: " + ",".join(k for k in a if a[k] != b.get(k))
    check("symulator i gra z oknem daja to samo", diff is None and len(t1) == len(t2), detail)


if __name__ == "__main__":
    SIM = os.path.abspath(sys.argv[1])
    GAME = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else None
    test_rewards()
    test_observation()
    test_protocol()
    test_lockstep()
    test_determinism(SIM, os.path.basename(os.path.dirname(os.path.dirname(SIM))))
    test_reset()
    test_events()
    if GAME:
        test_windowed()
    totals, maps, won, deaths = test_bot()
    print("bot:", totals, "mapy", sorted(maps), "wygrana", won, "smierci", deaths)
    check("bot zabija wrogow i zmienia mapy", totals.get("enemiesKilled", 0) > 0 and totals.get("mapsChanged", 0) > 0)
    check("bot czysci pokoje", totals.get("roomsCleared", 0) > 0)
    test_memory()
    print(f"{sum(RESULTS)}/{len(RESULTS)} OK")
    sys.exit(0 if all(RESULTS) else 1)

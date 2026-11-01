STEP_PENALTY = -50.0 / 4000
KEY_PICKED = 40.0
KEY_USED = 40.0
ENEMY_KILLED = 10.0
DAMAGE_DEALT = 0.5
HP_CHANGE = 0.5
NEW_TILE = 25.0 / 480
MAP_CHANGED = 100.0
GAME_WON = 500.0
PLAYER_DIED = -100.0


def compute_reward(state):
    events = state["events"]
    reward = STEP_PENALTY
    reward += events["keysPicked"] * KEY_PICKED
    reward += events["keysUsed"] * KEY_USED
    reward += events["enemiesKilled"] * ENEMY_KILLED
    reward += events["damageDealt"] * DAMAGE_DEALT
    reward += events["hpDelta"] * HP_CHANGE
    reward += events["newTiles"] * NEW_TILE
    reward += events["mapsChanged"] * MAP_CHANGED
    if state["won"]:
        reward += GAME_WON
    elif not state["alive"]:
        reward += PLAYER_DIED
    return reward

STEP_PENALTY = -0.001
KEY_PICKED = 2.0
KEY_USED = 2.0
ENEMY_KILLED = 0.5
DAMAGE_DEALT = 0.01
HP_CHANGE = 0.01
NEW_TILE = 0.01
NEW_MAP = 2.0
GAME_WON = 10.0
PLAYER_DIED = -1.0


def compute_reward(state, entered_new_map):
    """entered_new_map tylko za pierwsze wejscie, zeby chodzenie tam i z powrotem sie nie oplacalo."""
    events = state["events"]
    reward = STEP_PENALTY
    reward += events["keysPicked"] * KEY_PICKED
    reward += events["keysUsed"] * KEY_USED
    reward += events["enemiesKilled"] * ENEMY_KILLED
    reward += events["damageDealt"] * DAMAGE_DEALT
    reward += events["hpDelta"] * HP_CHANGE
    reward += events["newTiles"] * NEW_TILE
    if entered_new_map:
        reward += NEW_MAP
    if state["won"]:
        reward += GAME_WON
    elif not state["alive"]:
        reward += PLAYER_DIED
    return reward

STEP_PENALTY = -0.001
KEY_PICKED = 2.0
KEY_USED = 5.0
KEY_ROUTE = 1.0  # za kazde przejscie blizej zamknietych drzwi z kluczem; cofanie odbiera tyle samo
ENEMY_KILLED = 1.0
ROOM_CLEARED = 3.0
DAMAGE_DEALT = 0.01
HP_CHANGE = 0.01
NEW_TILE = 0.01
NEW_MAP = 2.0
NEW_LEVEL = 5.0  # pierwsze wejscie na wyzszy poziom, oprocz NEW_MAP
GAME_WON = 10.0
PLAYER_DIED = -1.0


def compute_reward(state, entered_new_map, key_progress=0.0, entered_new_level=False):
    """entered_new_map tylko za pierwsze wejscie, zeby chodzenie tam i z powrotem sie nie oplacalo.

    key_progress: zmiana potencjalu drogi do drzwi (DoorRoute.potential), wiec krazenie nic nie daje."""
    events = state["events"]
    reward = STEP_PENALTY + key_progress * KEY_ROUTE
    reward += events["keysPicked"] * KEY_PICKED
    reward += events["keysUsed"] * KEY_USED
    reward += events["enemiesKilled"] * ENEMY_KILLED
    reward += events["roomsCleared"] * ROOM_CLEARED
    reward += events["damageDealt"] * DAMAGE_DEALT
    reward += events["hpDelta"] * HP_CHANGE
    reward += events["newTiles"] * NEW_TILE
    if entered_new_map:
        reward += NEW_MAP
    if entered_new_level:
        reward += NEW_LEVEL
    if state["won"]:
        reward += GAME_WON
    elif not state["alive"]:
        reward += PLAYER_DIED
    return reward

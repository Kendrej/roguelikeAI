from collections import deque

DOOR_DISTANCE_SCALE = 30 + 16  # odleglosc w polach na biezacej mapie, przeskalowana do ulamka jednego przejscia


class DoorRoute:
    """Pamieta polaczenia miedzy odwiedzonymi mapami i mape z zamknietymi drzwiami.

    Z kluczem wskazuje droge do drzwi, a bez niego droge do najblizszej mapy z nieodwiedzonym sasiadem."""

    def __init__(self):
        self.links = {}
        self.door_map = None
        self.door_tile = None

    def update(self, state):
        here = (state["level"], state["map"])
        self.links[here] = {(g["level"], g["map"]) for g in state["gateways"]}
        if state["lockedDoor"]:
            self.door_map, self.door_tile = here, (state["lockedDoorX"], state["lockedDoorY"])
        elif self.door_map == here:
            self.door_map = self.door_tile = None

    def _first_hop(self, start, is_goal):
        """(liczba przejsc, pierwsza mapa na drodze) do najblizszej mapy spelniajacej is_goal albo None."""
        if is_goal(start):
            return 0, None
        prev = {start: None}
        queue = deque([start])
        while queue:
            cur = queue.popleft()
            for nxt in self.links.get(cur, ()):
                if nxt in prev:
                    continue
                prev[nxt] = cur
                if is_goal(nxt):
                    hops = 1
                    while prev[nxt] != start:
                        nxt = prev[nxt]
                        hops += 1
                    return hops, nxt
                queue.append(nxt)
        return None

    def _route(self, state):
        if not state["key"] or self.door_map is None:
            return None
        return self._first_hop((state["level"], state["map"]), lambda m: m == self.door_map)

    @staticmethod
    def _exit_towards(state, next_map):
        px, py = state["playerX"], state["playerY"]
        exits = [(g["x"], g["y"]) for g in state["gateways"] if (g["level"], g["map"]) == next_map]
        return min(exits, key=lambda p: abs(p[0] - px) + abs(p[1] - py), default=None)

    def explore_target(self, state, visited_maps):
        """Wyjscie w strone najblizszej znanej mapy z nieodwiedzonym sasiadem, gdy z biezacej nie ma wyjscia na nowa."""
        here = (state["level"], state["map"])
        frontier = lambda m: m != here and any(n not in visited_maps for n in self.links.get(m, ()))
        route = self._first_hop(here, frontier)
        if route is None or route[1] is None:
            return None
        return self._exit_towards(state, route[1])

    def target(self, state):
        """Pole na biezacej mapie, do ktorego trzeba isc z kluczem: drzwi albo wyjscie na nastepna mape drogi."""
        route = self._route(state)
        if route is None:
            return None
        hops, next_map = route
        if hops == 0:
            return self.door_tile
        return self._exit_towards(state, next_map)

    def potential(self, state):
        """Minus odleglosc do drzwi: przejscia miedzy mapami plus pola do celu na biezacej; None bez klucza lub drogi."""
        route = self._route(state)
        target = self.target(state)
        if route is None or target is None:
            return None
        dx, dy = target[0] - state["playerX"], target[1] - state["playerY"]
        return -(route[0] + (abs(dx) + abs(dy)) / DOOR_DISTANCE_SCALE)

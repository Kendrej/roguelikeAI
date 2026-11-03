# HANDOFF: roguelikeAI

Stan na 2026-11-03. Ten plik zastępuje pamięć Claude z laptopa, której nie ma na innym komputerze.

## Cel

Agent RL (PPO), który sam gra w roguelike'a napisanego w C++. Dwa osobne repozytoria, celowo, żeby w CV były dwa projekty:

- **roguelikeAI** (to repo, `Kendrej/roguelikeAI`, gałąź `ai-headless`): środowisko Gymnasium, nagrody, trening, podgląd.
- **RogueLikeGame** (`Kendrej/RogueLikeGame`, gałąź `ai-headless`): gra w C++20/Vulkan oraz symulator bez grafiki `RogueLikeSim`.

## Stack

- Python 3.11, Stable Baselines3 (PPO, `MlpPolicy`), Gymnasium, PyTorch (CPU), PyZMQ, NumPy.
- Gra: C++20, Vulkan, ImGui, GLFW, CMake + Ninja, vcpkg (submoduł), MSVC z Visual Studio 2022.
- Komunikacja: ZeroMQ REQ/REP, JSON. Python wysyła akcję, gra robi krok i odsyła stan. Gra czeka na agenta (lockstep).

## Uruchomienie od zera (Windows)

Oba repo muszą leżeć obok siebie w jednym folderze (albo ustaw zmienną `ROGUELIKE_GAME_REPO`).

```powershell
git clone -b ai-headless https://github.com/Kendrej/roguelikeAI.git
git clone --recursive -b ai-headless https://github.com/Kendrej/RogueLikeGame.git
cd RogueLikeGame
git remote rename origin kendrej
git remote add origin https://github.com/erybie222/RogueLikeGame.git
```

Build gry w środowisku VS (VsDevCmd, x64), preset release:

```powershell
cmake --preset win-ninja-release
cmake --build --preset win-ninja-release-build
```

Powstaje `build/win-ninja-release/bin/RogueLikeGame.exe` (okno) i `RogueLikeSim.exe` (bez grafiki). Python szuka ich właśnie tam (`env/paths.py`).

W `roguelikeAI` (w PowerShellu z `.\`):

- `.\watch.bat --model models\ppo_shoot_1m.zip` — podgląd modelu w oknie gry (`--speed 3` szybciej).
- `.\train.bat --timesteps 1000000` — trening bez grafiki, sam uruchamia 4 symulatory.
- `.venv\Scripts\python.exe evaluate.py --model models\ppo_shoot_1m.zip` — 50 gier, porównanie z losowym graczem.
- `.venv\Scripts\python.exe tests\test_sim.py <RogueLikeSim.exe> [RogueLikeGame.exe]` — testy integracyjne symulatora.
- `tensorboard --logdir logs/` — wykresy treningu.

Pierwsze uruchomienie `.bat` tworzy `.venv` i instaluje zależności (`setup.bat`).

## Co zrobione

- Symulator bez grafiki w grze (`src/ai`), z tego samego kodu korzysta `RogueLikeGame --ai-mode`. Stały krok 1/60 s, 4 klatki na decyzję.
- Protokół 4: gra zgłasza surowe zdarzenia (klucze, zabicia, wyczyszczone pokoje, obrażenia, nowe pola), a nagrodę liczy Python w `env/rewards.py`.
- Obserwacja (`env/observation.py`): lokalny widok 11x11 wokół gracza plus wektor (wrogowie, cele, klucz, gotowość strzału).
- 6 akcji: ruch w 4 strony, miecz, strzał z auto-celem w najbliższego wroga.
- Trening równoległy na 4 grach, ok. 650 kroków/s na 8 wątkach.
- Najlepszy model: `models/ppo_shoot_1m.zip` (1 mln kroków), jedyny model w gicie.

| | losowy gracz | model |
|---|---|---|
| średnia nagroda | 2,4 | **26,5** |
| podniesione klucze (50 gier) | 0 | **47** |
| wygrane | 0 | 0 |

Model czyści mapę 0/1, przechodzi na 0/4, zabija bossa i bierze klucz. Szczegóły w `RESULTS.md`.

## Co dalej

1. **Główny problem:** model nie wraca z kluczem do zamkniętych drzwi na mapie 0/0, więc nie wchodzi na kolejny poziom. Wskaźnik wyjścia w obserwacji kieruje tylko na nieodwiedzone mapy. Pomysł: wskazówka w obserwacji lub nagrodzie, że z kluczem trzeba iść do zamkniętych drzwi, potem dłuższy trening.
2. Drobny błąd w grze: powielone wyjście (27,6) na mapie 0/1.
3. Debug gry nie był przebudowany po ostatnich zmianach (Release: CTest 2/2, symulator 20/20).
4. Porządek: w gicie są śmieci `env/__pycache__/*.cpython-310.pyc`.

## Ważne decyzje i ustalenia

- Zasad gry nie zmieniamy. Tryb AI tylko upraszcza sterowanie: klucz używa się sam przy drzwiach, strzał celuje sam (człowiek celuje myszką), bez przedmiotów i skrzyń.
- Strzał z auto-celem zamiast samego miecza: samym mieczem mapa 0/1 (3 rycerzy i 2 orki, drzwi otwierają się po zabiciu wszystkich) była nie do przejścia. Użytkownik wybrał auto-cel.
- `train.py` wznawia od najnowszego zipa w `checkpoints/`. Przy zmianie obserwacji lub akcji przenieś stare modele do podfolderu, inaczej trening się wysypie.
- Najlepiej 4 gry i 1 wątek PyTorcha; więcej wątków było wolniejsze.
- Na Windowsie środowisko wirtualne o krótkiej ścieżce (`.venv` w repo), bo pip wywalał się na za długiej ścieżce.
- `checkpoints/` i `logs/` są poza gitem. Stare modele (`checkpoints/obs_v3`, `old_obs`) zostały tylko na laptopie i nie są potrzebne.

## Zasady współpracy z Claude

- Po polsku, krótko.
- Zależności instaluje Claude sam i sprawdza import; użytkownikowi podaje tylko, jak uruchomić.
- Commity Claude może robić sam, ale **bez** `Co-Authored-By` i innych oznaczeń Claude. Push tylko na prośbę.
- W `RogueLikeGame`: pushuj na `kendrej` (fork). `origin` to repo `erybie222`, tam nic nie wysyłaj.
- Stare commity z linią Co-Authored zostają, tak zdecydował użytkownik.
- Na starcie sesji użytkownik lubi najpierw zobaczyć model w akcji (`watch.bat`), a potem krótkie przypomnienie wyników.

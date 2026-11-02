# Wyniki treningow

Ocena: `evaluate.py`, 50 gier po maks. 3000 decyzji, porownanie z losowym graczem.

## 2026-11-02: strzal z auto-celem, nagroda za wyczyszczenie pokoju

Model: `models/ppo_shoot_1m.zip` (PPO, 1 001 472 krokow, ok. 21 min na 4 grach). Gra `9c78b65`, AI `c864a75`, protokol 4, 6 akcji.

| | losowy gracz | model |
|---|---|---|
| srednia nagroda | 2,41 | **26,51** |
| srednio krokow | 3000 | 2841 |
| nowe mapy (maks.) | 0,52 (2) | **2,00 (2)** |
| zabici wrogowie | 2,12 | **5,94** |
| smierci | 0/50 | 3/50 |
| podniesione klucze | 0 | **47** |
| wygrane | 0 | 0 |

Srednia nagroda za epizod w treningu rosla rowno: 7 na starcie, 14 po 420 tys. krokow, 23 na koncu.
Model czysci mape 0/1, przechodzi na mape 0/4, zabija bossa i podnosi klucz prawie w kazdej grze.
Nie wraca jeszcze z kluczem do zamknietych drzwi na mapie 0/0, wiec nie wchodzi na kolejny poziom.

Podglad: `watch.bat --model models/ppo_shoot_1m.zip`

## 2026-11-02: tylko miecz (5 akcji)

Model po 1 mln krokow (lokalnie w `checkpoints/obs_v3`, nie w repozytorium).

| | losowy gracz | model |
|---|---|---|
| srednia nagroda | -0,59 | 1,27 |
| nowe mapy (maks.) | 0,64 (1) | 1,00 (1) |
| zabici wrogowie | 1,10 | 2,12 |
| smierci | 17/50 | 28/50 |
| klucze / wygrane | 0 / 0 | 0 / 0 |

Utykal na mapie 0/1: drzwi otwieraja sie dopiero po zabiciu wszystkich wrogow (3 rycerze i 2 orki), a samym mieczem to prawie niemozliwe.
Losowy gracz w tym przebiegu mial inne nagrody, wiec jego wynik nie jest porownywalny z tabela wyzej.

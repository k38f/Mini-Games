# Mini-Games

# Mini Games Collection 🎮

A small collection of classic games in one window, built with **Python + Pygame**.

```
1   – Tic-Tac-Toe      (3×3 — two players or vs AI)
1.2 – Gomoku           (5 in a row on a big scrollable board — two players or vs AI)
2   – Guess the Number (computer picks 1–100, you guess)
3   – Snake            (classic; grid field, scaly visuals, speed increases as you eat)
```

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Pygame](https://img.shields.io/badge/Pygame-2.x-green)

---

## Requirements

- Python 3.8+
- Pygame 2.x

```bash
pip install pygame
```

## Run

```bash
python mini_games.py
```

---

## Controls

| Game           | Controls                                                    |
|----------------|-------------------------------------------------------------|
| Tic-Tac-Toe    | Mouse click                                                 |
| Gomoku         | Mouse click to place · Arrow keys / scroll wheel to pan · **R** to restart after win |
| Guess Number   | Type on keyboard · Enter or button to confirm               |
| Snake          | Arrow keys or WASD                                          |

---

## AI difficulty levels (Tic-Tac-Toe & Gomoku)

Both games ask you to pick a mode before starting:

| Mode      | Behaviour                                                                 |
|-----------|---------------------------------------------------------------------------|
| 2 Players | Local two-player, no AI                                                   |
| Easy      | Picks random nearby moves — makes obvious mistakes                        |
| Medium    | Plays smart most of the time, but slips up ~40 % of moves                 |
| Hard      | Plays as well as possible (minimax for TTT, deep heuristic for Gomoku)    |

When you win in Gomoku the 5 winning stones are highlighted with a pulsing gold glow.

---

## Project structure

Everything lives in a single file — no assets or extra files needed.

```
mini_games.py
│
├── main_menu()         – game picker screen
├── mode_select()       – 2P / Easy / Medium / Hard picker (shared)
│
├── game_ttt()          – Tic-Tac-Toe
│   ├── _ttt_check()    – win detection
│   ├── _ttt_minimax()  – minimax algorithm
│   └── ttt_ai_move()   – AI move selector
│
├── game_gomoku()       – Gomoku (5 in a row)
│   ├── _gom_candidates()  – nearby empty cells
│   ├── _gom_score_dir()   – line heuristic scorer
│   ├── _gom_eval_cell()   – total cell score
│   ├── _gom_find_five()   – winning cells finder
│   └── gomoku_ai_move()   – AI move selector
│
├── game_guess()        – Guess the Number
└── game_snake()        – Snake
```

---

## License

MIT — do whatever you want with it.

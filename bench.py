"""Benchmarks for the README: search efficiency + results vs a random-move player. Writes docs/."""
import random

import chess
import chess.svg
import matplotlib.pyplot as plt

from engine import Engine

FEN = "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"  # Italian game
configs = {
    "Plain minimax": dict(use_ab=False, use_ordering=False),
    "Alpha-beta": dict(use_ab=True, use_ordering=False),
    "Alpha-beta + move ordering": dict(use_ab=True, use_ordering=True),
}
fig, ax = plt.subplots(figsize=(8, 4.5))
for name, cfg in configs.items():
    depths = [1, 2, 3] if name == "Plain minimax" else [1, 2, 3, 4]
    nodes = []
    for d in depths:
        e = Engine(d, use_quiescence=False, **cfg)
        e.choose(chess.Board(FEN))
        nodes.append(e.last["nodes"])
    ax.plot(depths, nodes, marker="o", label=name)
    print(f"{name:28s}", dict(zip(depths, nodes)))
ax.set(yscale="log", xlabel="Search depth (half-moves ahead)", ylabel="Positions searched (log)",
       title="Pruning lets the bot look deeper for the same work")
ax.set_xticks([1, 2, 3, 4]); ax.grid(alpha=0.3); ax.legend()
fig.tight_layout(); fig.savefig("docs/search-efficiency.png", dpi=110)

# bot vs random mover
rng, results, lengths = random.Random(1), {"Bot wins": 0, "Draws": 0, "Bot losses": 0}, []
bot = Engine(2)
for g in range(20):
    board, bot_color = chess.Board(), chess.WHITE if g % 2 == 0 else chess.BLACK
    while not board.is_game_over() and board.fullmove_number < 150:
        board.push(bot.choose(board) if board.turn == bot_color else rng.choice(list(board.legal_moves)))
    outcome = board.outcome()
    if outcome and outcome.winner == bot_color:
        results["Bot wins"] += 1
        lengths.append(board.fullmove_number)
        last_win = board
    elif outcome and outcome.winner is not None:
        results["Bot losses"] += 1
    else:
        results["Draws"] += 1
print(results, "avg moves to win:", sum(lengths) / max(len(lengths), 1))

fig, ax = plt.subplots(figsize=(6, 3.5))
bars = ax.bar(list(results), list(results.values()), color=["#2a9d8f", "#8d99ae", "#e76f51"])
ax.bar_label(bars)
ax.set(title=f"Bot (depth 2) vs random mover, 20 games\navg {sum(lengths) / max(len(lengths), 1):.0f} moves to checkmate", ylabel="Games")
fig.tight_layout(); fig.savefig("docs/vs-random.png", dpi=110)

with open("docs/final-position.svg", "w") as f:
    f.write(chess.svg.board(last_win, lastmove=last_win.peek(), size=420,
                            check=last_win.king(last_win.turn)))

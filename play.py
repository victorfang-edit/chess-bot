"""Play against the bot in your terminal.
usage: python play.py [--depth 3] [--black]     moves in SAN (e4, Nf3, O-O) or UCI (e2e4); 'quit' to exit"""
import argparse
import sys

import chess

from engine import Engine

GLYPH = dict(zip("KQRBNPkqrbnp", "♔♕♖♗♘♙♚♛♜♝♞♟"))


def show(board, flip):
    ranks = range(8) if flip else range(7, -1, -1)
    files = range(7, -1, -1) if flip else range(8)
    for r in ranks:
        row = []
        for f in files:
            p = board.piece_at(chess.square(f, r))
            row.append(GLYPH[p.symbol()] if p else ("·" if (r + f) % 2 else " "))
        print(f" {r + 1}  " + " ".join(row))
    print("    " + " ".join("abcdefgh"[f] for f in files))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--depth", type=int, default=3)
    ap.add_argument("--black", action="store_true", help="you play black")
    args = ap.parse_args()
    board, bot, human = chess.Board(), Engine(args.depth), chess.BLACK if args.black else chess.WHITE

    while not board.is_game_over():
        if board.turn == human:
            show(board, flip=human == chess.BLACK)
            text = input("\nyour move: ").strip()
            if not sys.stdin.isatty():
                print(text)  # echo scripted input so recorded sessions read naturally
            if text == "quit":
                return
            try:
                move = board.parse_san(text)
            except ValueError:
                try:
                    move = chess.Move.from_uci(text)
                    if move not in board.legal_moves:
                        raise ValueError
                except ValueError:
                    print("illegal move, try again (examples: e4, Nf3, e2e4)")
                    continue
            board.push(move)
        else:
            move = bot.choose(board)
            info = bot.last
            print(f"\nbot plays {board.san(move)}   (bot's eval {info['score'] / 100:+.2f}, {info['nodes']:,} positions, {info['seconds']:.1f}s)\n")
            board.push(move)
    show(board, flip=human == chess.BLACK)
    print(f"\nGame over: {board.result()} ({board.outcome().termination.name.lower()})")


if __name__ == "__main__":
    main()

import chess

from engine import Engine, evaluate


def test_start_position_is_balanced():
    assert evaluate(chess.Board()) == 0


def test_finds_mate_in_one():
    board = chess.Board("6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1")  # back-rank mate: Rd8#
    assert Engine(2).choose(board) == chess.Move.from_uci("d1d8")


def test_takes_free_queen():
    board = chess.Board("4k3/8/8/3q4/4P3/8/8/4K3 w - - 0 1")
    assert Engine(2).choose(board) == chess.Move.from_uci("e4d5")


def test_alpha_beta_same_move_fewer_nodes():
    board = chess.Board("r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3")
    full, pruned = Engine(3, use_ab=False, use_ordering=False, use_quiescence=False), Engine(3, use_quiescence=False)
    assert full.choose(board.copy()) and pruned.choose(board.copy())
    assert full.last["score"] == pruned.last["score"]  # pruning never changes the answer
    assert pruned.last["nodes"] < full.last["nodes"] / 5


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f()
    print("all tests passed")

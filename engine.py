"""A small chess engine: material + piece-square evaluation, negamax with alpha-beta,
move ordering, and quiescence search. python-chess handles the rules."""
import time

import chess

VALUES = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330, chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0}

# piece-square tables from white's point of view (a8..h8 first row), classic "simplified evaluation" values
PST = {
    chess.PAWN: [0, 0, 0, 0, 0, 0, 0, 0, 50, 50, 50, 50, 50, 50, 50, 50, 10, 10, 20, 30, 30, 20, 10, 10, 5, 5, 10, 25, 25, 10, 5, 5,
                 0, 0, 0, 20, 20, 0, 0, 0, 5, -5, -10, 0, 0, -10, -5, 5, 5, 10, 10, -20, -20, 10, 10, 5, 0, 0, 0, 0, 0, 0, 0, 0],
    chess.KNIGHT: [-50, -40, -30, -30, -30, -30, -40, -50, -40, -20, 0, 0, 0, 0, -20, -40, -30, 0, 10, 15, 15, 10, 0, -30,
                   -30, 5, 15, 20, 20, 15, 5, -30, -30, 0, 15, 20, 20, 15, 0, -30, -30, 5, 10, 15, 15, 10, 5, -30,
                   -40, -20, 0, 5, 5, 0, -20, -40, -50, -40, -30, -30, -30, -30, -40, -50],
    chess.BISHOP: [-20, -10, -10, -10, -10, -10, -10, -20, -10, 0, 0, 0, 0, 0, 0, -10, -10, 0, 5, 10, 10, 5, 0, -10,
                   -10, 5, 5, 10, 10, 5, 5, -10, -10, 0, 10, 10, 10, 10, 0, -10, -10, 10, 10, 10, 10, 10, 10, -10,
                   -10, 5, 0, 0, 0, 0, 5, -10, -20, -10, -10, -10, -10, -10, -10, -20],
    chess.ROOK: [0, 0, 0, 0, 0, 0, 0, 0, 5, 10, 10, 10, 10, 10, 10, 5, -5, 0, 0, 0, 0, 0, 0, -5, -5, 0, 0, 0, 0, 0, 0, -5,
                 -5, 0, 0, 0, 0, 0, 0, -5, -5, 0, 0, 0, 0, 0, 0, -5, -5, 0, 0, 0, 0, 0, 0, -5, 0, 0, 0, 5, 5, 0, 0, 0],
    chess.QUEEN: [-20, -10, -10, -5, -5, -10, -10, -20, -10, 0, 0, 0, 0, 0, 0, -10, -10, 0, 5, 5, 5, 5, 0, -10,
                  -5, 0, 5, 5, 5, 5, 0, -5, 0, 0, 5, 5, 5, 5, 0, -5, -10, 5, 5, 5, 5, 5, 0, -10,
                  -10, 0, 5, 0, 0, 0, 0, -10, -20, -10, -10, -5, -5, -10, -10, -20],
    chess.KING: [-30, -40, -40, -50, -50, -40, -40, -30, -30, -40, -40, -50, -50, -40, -40, -30, -30, -40, -40, -50, -50, -40, -40, -30,
                 -30, -40, -40, -50, -50, -40, -40, -30, -20, -30, -30, -40, -40, -30, -30, -20, -10, -20, -20, -20, -20, -20, -20, -10,
                 20, 20, 0, 0, 0, 0, 20, 20, 20, 30, 10, 0, 0, 10, 30, 20],
}
MATE = 100_000


def evaluate(board):
    """Score from the side-to-move's perspective (negamax convention), in centipawns."""
    score = 0
    for sq, piece in board.piece_map().items():
        # tables are written rank 8 first, so flip the square for white
        idx = chess.square_mirror(sq) if piece.color == chess.WHITE else sq
        v = VALUES[piece.piece_type] + PST[piece.piece_type][idx]
        score += v if piece.color == chess.WHITE else -v
    return score if board.turn == chess.WHITE else -score


def ordered(board, moves):
    """Captures first, best victim with cheapest attacker first (MVV-LVA): makes alpha-beta cut far more."""
    def key(m):
        if board.is_capture(m):
            victim = board.piece_at(m.to_square)
            v = VALUES[victim.piece_type] if victim else VALUES[chess.PAWN]  # en passant
            return -(10 * v - VALUES[board.piece_at(m.from_square).piece_type])
        return 0 if not m.promotion else -800
    return sorted(moves, key=key)


class Engine:
    def __init__(self, depth=3, use_ordering=True, use_ab=True, use_quiescence=True):
        self.depth, self.use_ordering, self.use_ab, self.use_q = depth, use_ordering, use_ab, use_quiescence
        self.nodes = 0

    def quiesce(self, board, alpha, beta):
        """Keep searching captures past the depth limit so we never stop mid-trade (the 'horizon effect')."""
        self.nodes += 1
        stand = evaluate(board)
        if stand >= beta:
            return beta
        alpha = max(alpha, stand)
        for m in ordered(board, [m for m in board.legal_moves if board.is_capture(m)]):
            board.push(m)
            score = -self.quiesce(board, -beta, -alpha)
            board.pop()
            if score >= beta:
                return beta
            alpha = max(alpha, score)
        return alpha

    def negamax(self, board, depth, alpha, beta, ply=0):
        self.nodes += 1
        if board.is_checkmate():
            return -MATE + ply  # prefer faster mates
        if board.is_stalemate() or board.is_insufficient_material() or board.can_claim_draw():
            return 0
        if depth == 0:
            return self.quiesce(board, alpha, beta) if self.use_q else evaluate(board)
        moves = list(board.legal_moves)
        if self.use_ordering:
            moves = ordered(board, moves)
        best = -MATE * 2
        for m in moves:
            board.push(m)
            score = -self.negamax(board, depth - 1, -beta, -alpha, ply + 1)
            board.pop()
            best = max(best, score)
            alpha = max(alpha, score)
            if self.use_ab and alpha >= beta:
                break  # opponent will never allow this line: prune the rest
        return best

    def choose(self, board):
        self.nodes, start = 0, time.time()
        best_move, alpha, beta = None, -MATE * 2, MATE * 2
        moves = ordered(board, list(board.legal_moves)) if self.use_ordering else list(board.legal_moves)
        for m in moves:
            board.push(m)
            score = -self.negamax(board, self.depth - 1, -beta, -alpha, 1)
            board.pop()
            if best_move is None or score > alpha:
                best_move, alpha = m, score
        self.last = {"score": alpha, "nodes": self.nodes, "seconds": time.time() - start}
        return best_move

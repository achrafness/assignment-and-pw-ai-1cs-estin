import numpy as np
from game import ROW_COUNT, COLUMN_COUNT, EMPTY, PLAYER_PIECE, AI_PIECE

WINDOW_LENGTH = 4

def evaluate_window(window, piece):
    """
    Evaluate a window of 4 positions for the given piece.
    
    Args:
        window: List of 4 pieces in a row
        piece: Piece type to evaluate for (PLAYER_PIECE or AI_PIECE)
        
    Returns:
        Score for the window
    """
    score = 0
    opp_piece = PLAYER_PIECE if piece == AI_PIECE else AI_PIECE

    # Score based on piece count and empty spaces
    if window.count(piece) == 4:
        score += 100
    elif window.count(piece) == 3 and window.count(EMPTY) == 1:
        score += 5
    elif window.count(piece) == 2 and window.count(EMPTY) == 2:
        score += 2

    # Penalize opponent's three in a row
    if window.count(opp_piece) == 3 and window.count(EMPTY) == 1:
        score -= 4

    return score

def score_position(board, piece):
    """
    Score the entire board position for the given piece.
    
    Args:
        board: array with the current board state
        piece: Piece type to evaluate for (PLAYER_PIECE or AI_PIECE)
        
    Returns:
        Score for the position
    """
    score = 0

    center_array = [int(i) for i in list(board[:, COLUMN_COUNT//2])]
    center_count = center_array.count(piece)
    score += center_count * 3

    # Score Horizontal
    for r in range(ROW_COUNT):
        row_array = [int(i) for i in list(board[r,:])]
        for c in range(COLUMN_COUNT-3):
            window = row_array[c:c+WINDOW_LENGTH]
            score += evaluate_window(window, piece)

    # Score Vertical
    for c in range(COLUMN_COUNT):
        col_array = [int(i) for i in list(board[:,c])]
        for r in range(ROW_COUNT-3):
            window = col_array[r:r+WINDOW_LENGTH]
            score += evaluate_window(window, piece)

    # Score positive sloped diagonal
    for r in range(ROW_COUNT-3):
        for c in range(COLUMN_COUNT-3):
            window = [board[r+i][c+i] for i in range(WINDOW_LENGTH)]
            score += evaluate_window(window, piece)

    # Score negative sloped diagonal
    for r in range(ROW_COUNT-3):
        for c in range(COLUMN_COUNT-3):
            window = [board[r+3-i][c+i] for i in range(WINDOW_LENGTH)]
            score += evaluate_window(window, piece)

    return score
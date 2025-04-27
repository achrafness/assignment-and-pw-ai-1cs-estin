import random
import math
from game import PLAYER_PIECE, AI_PIECE
from heuristic import score_position

def minimax(game, depth, alpha, beta, maximizing_player):
    """
    Minimax algorithm with alpha-beta pruning implementation.
    
    Args:
        game: GameBoard instance
        depth: The search depth
        alpha: Alpha value for pruning
        beta: Beta value for pruning
        maximizing_player: Boolean indicating if current player is maximizing
        
    Returns:
        Tuple of (best column, score)
    """
    valid_locations = game.get_valid_locations()
    is_terminal = game.is_terminal_node()
    
    # If terminal node or max depth reached, return evaluation
    if depth == 0 or is_terminal:
        if is_terminal:
            if game.winning_move(AI_PIECE):
                return (None, 100000000000000)
            elif game.winning_move(PLAYER_PIECE):
                return (None, -10000000000000)
            else:  # Game is over, no more valid moves
                return (None, 0)
        else:  # Depth is zero
            return (None, score_position(game.board, AI_PIECE))
    
    if maximizing_player:
        value = -math.inf
        column = random.choice(valid_locations)
        for col in valid_locations:
            row = game.get_next_open_row(col)
            if row is not None:  # Check if row is not None
                # Create a copy of the board and make the move
                temp_game = copy_game_state(game)
                temp_game.drop_piece(row, col, AI_PIECE)
                
                # Recursive minimax call
                new_score = minimax(temp_game, depth-1, alpha, beta, False)[1]
                
                # Update best move if better score found
                if new_score > value:
                    value = new_score
                    column = col
                    
                # Alpha-beta pruning
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
                    
        return column, value
    
    else:  # Minimizing player
        value = math.inf
        column = random.choice(valid_locations)
        for col in valid_locations:
            row = game.get_next_open_row(col)
            if row is not None:  # Check if row is not None
                # Create a copy of the board and make the move
                temp_game = copy_game_state(game)
                temp_game.drop_piece(row, col, PLAYER_PIECE)
                
                # Recursive minimax call
                new_score = minimax(temp_game, depth-1, alpha, beta, True)[1]
                
                # Update best move if better score found
                if new_score < value:
                    value = new_score
                    column = col
                    
                # Alpha-beta pruning
                beta = min(beta, value)
                if alpha >= beta:
                    break
                    
        return column, value

def copy_game_state(game):
    """Create a copy of the game state to avoid modifying the original."""
    from game import GameBoard
    new_game = GameBoard()
    new_game.board = game.board.copy()
    new_game.game_over = game.game_over
    new_game.winner = game.winner
    return new_game
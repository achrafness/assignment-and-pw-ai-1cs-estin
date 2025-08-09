import numpy as np

ROW_COUNT = 6
COLUMN_COUNT = 7

EMPTY = 0
PLAYER_PIECE = 1
AI_PIECE = 2

class GameBoard:
    def __init__(self):
        self.board = self.create_board()
        self.game_over = False
        self.winner = None
        
    def create_board(self):
        """Create an empty game board."""
        board = np.zeros((ROW_COUNT, COLUMN_COUNT))
        return board
    
    def drop_piece(self, row, col, piece):
        """Place a piece on the board."""
        self.board[row][col] = piece
    
    def is_valid_location(self, col):
        """Check if a column has space for another piece."""
        return self.board[ROW_COUNT-1][col] == 0
    
    def get_next_open_row(self, col):
        """Find the next available row in the given column."""
        for r in range(ROW_COUNT):
            if self.board[r][col] == 0:
                return r
        return None
    
    def print_board(self):
        """Print the current board state."""
        print(np.flip(self.board, 0))
    
    def get_valid_locations(self):
        """Get all valid column locations for the next move."""
        valid_locations = []
        for col in range(COLUMN_COUNT):
            if self.is_valid_location(col):
                valid_locations.append(col)
        return valid_locations
    
    def is_terminal_node(self):
        """Check if the game has reached a terminal state."""
        return self.winning_move(PLAYER_PIECE) or self.winning_move(AI_PIECE) or len(self.get_valid_locations()) == 0
    
    def winning_move(self, piece):
        """Check if the given piece has a winning configuration on the board."""
        for c in range(COLUMN_COUNT-3):
            for r in range(ROW_COUNT):
                if (self.board[r][c] == piece and self.board[r][c+1] == piece and 
                    self.board[r][c+2] == piece and self.board[r][c+3] == piece):
                    return True

        for c in range(COLUMN_COUNT):
            for r in range(ROW_COUNT-3):
                if (self.board[r][c] == piece and self.board[r+1][c] == piece and 
                    self.board[r+2][c] == piece and self.board[r+3][c] == piece):
                    return True

        for c in range(COLUMN_COUNT-3):
            for r in range(ROW_COUNT-3):
                if (self.board[r][c] == piece and self.board[r+1][c+1] == piece and 
                    self.board[r+2][c+2] == piece and self.board[r+3][c+3] == piece):
                    return True

        for c in range(COLUMN_COUNT-3):
            for r in range(3, ROW_COUNT):
                if (self.board[r][c] == piece and self.board[r-1][c+1] == piece and 
                    self.board[r-2][c+2] == piece and self.board[r-3][c+3] == piece):
                    return True
                    
        return False
    
    def check_win_or_draw(self, piece):
        """Check if the game is won or drawn after placing a piece."""
        if self.winning_move(piece):
            return True, piece
        elif len(self.get_valid_locations()) == 0:
            return True, None
        return False, None
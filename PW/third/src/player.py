import random
from abc import ABC, abstractmethod

PLAYER = 0
AI = 1

class Player(ABC):
    """Abstract base class for all player types."""
    
    def __init__(self, piece_type):
        self.piece_type = piece_type
        
    @abstractmethod
    def get_move(self, game):
        """Get the player's next move."""
        pass

class HumanPlayer(Player):
    """Human player that gets moves from user input."""
    
    def get_move(self, game):
        """Get the column to drop a piece from the user."""
        # This is handled by the UI in main.py
        # Just a placeholder as the actual move is processed in the game loop
        return None

class AIPlayer(Player):
    """AI player that uses minimax algorithm to choose moves."""
    
    def __init__(self, piece_type, difficulty=5):
        super().__init__(piece_type)
        self.difficulty = difficulty  
    
    def get_move(self, game):
        """Get the best column to drop a piece using minimax algorithm."""
        from minimax import minimax
        import math
        
        col, _ = minimax(game, self.difficulty, -math.inf, math.inf, True)
        return col
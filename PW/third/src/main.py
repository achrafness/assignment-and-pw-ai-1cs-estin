import numpy as np
import random
import pygame
import sys
import math
from game import GameBoard, PLAYER_PIECE, AI_PIECE, ROW_COUNT, COLUMN_COUNT
from player import Player, HumanPlayer, AIPlayer, PLAYER, AI

# Modern color scheme
NAVY = (31, 58, 147)
DARK_GRAY = (40, 40, 40)
WHITE = (255, 255, 255)
LIGHT_BLUE = (65, 131, 215)
ORANGE = (242, 96, 12)

# Game styling constants
SQUARESIZE = 100
RADIUS = int(SQUARESIZE/2 - 10)
BORDER_WIDTH = 3
TITLE_HEIGHT = 80

# Screen resolution
WIDTH = COLUMN_COUNT * SQUARESIZE
HEIGHT = (ROW_COUNT+1) * SQUARESIZE + TITLE_HEIGHT

def draw_board(screen, game_board):
    """Draw the game board on the screen."""
    # Draw title bar
    pygame.draw.rect(screen, DARK_GRAY, (0, 0, WIDTH, TITLE_HEIGHT))
    
    # Draw game area background
    pygame.draw.rect(screen, NAVY, (0, TITLE_HEIGHT, WIDTH, HEIGHT - TITLE_HEIGHT))
    
    # Draw grid and empty slots
    for c in range(COLUMN_COUNT):
        for r in range(ROW_COUNT):
            # Draw cell with border
            rect_x = c * SQUARESIZE
            rect_y = r * SQUARESIZE + TITLE_HEIGHT + SQUARESIZE
            pygame.draw.rect(screen, NAVY, (rect_x, rect_y, SQUARESIZE, SQUARESIZE))
            
            # Draw circular hole
            circle_x = rect_x + SQUARESIZE//2
            circle_y = rect_y + SQUARESIZE//2
            pygame.draw.circle(screen, DARK_GRAY, (circle_x, circle_y), RADIUS)
            pygame.draw.circle(screen, WHITE, (circle_x, circle_y), RADIUS - BORDER_WIDTH)
    
    # Draw pieces
    for c in range(COLUMN_COUNT):
        for r in range(ROW_COUNT):
            circle_x = c * SQUARESIZE + SQUARESIZE//2
            circle_y = HEIGHT - (r * SQUARESIZE + SQUARESIZE//2)
            
            if game_board.board[r][c] == PLAYER_PIECE:
                pygame.draw.circle(screen, ORANGE, (circle_x, circle_y), RADIUS)
                # Add 3D effect
                pygame.draw.circle(screen, (255, 140, 50), (circle_x, circle_y), RADIUS - 5)
            elif game_board.board[r][c] == AI_PIECE:
                pygame.draw.circle(screen, LIGHT_BLUE, (circle_x, circle_y), RADIUS)
                # Add 3D effect
                pygame.draw.circle(screen, (100, 180, 255), (circle_x, circle_y), RADIUS - 5)
    
    # Display title
    title_font = pygame.font.SysFont("Arial", 36, bold=True)
    title = title_font.render("CONNECT FOUR", True, WHITE)
    screen.blit(title, (WIDTH//2 - title.get_width()//2, TITLE_HEIGHT//2 - title.get_height()//2))
    
    pygame.display.update()

def show_winner_message(screen, winner):
    """Display winner message and game over screen."""
    overlay = pygame.Surface((WIDTH, HEIGHT))
    overlay.set_alpha(180)
    overlay.fill(DARK_GRAY)
    screen.blit(overlay, (0, 0))
    
    message_font = pygame.font.SysFont("Arial", 50, bold=True)
    if winner == PLAYER:
        message = message_font.render("YOU WIN!", True, ORANGE)
    else:
        message = message_font.render("AI WINS!", True, LIGHT_BLUE)
    
    screen.blit(message, (WIDTH//2 - message.get_width()//2, HEIGHT//2 - message.get_height()//2))
    
    instruction_font = pygame.font.SysFont("Arial", 24)
    instruction = instruction_font.render("Click anywhere to play again", True, WHITE)
    screen.blit(instruction, (WIDTH//2 - instruction.get_width()//2, HEIGHT//2 + 50))
    
    pygame.display.update()

def main():
    # Initialize pygame
    pygame.init()
    pygame.display.set_caption('Connect Four AI')
    
    # Create the screen
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    
    # Initialize game
    game_board = GameBoard()
    game_board.print_board()
    game_over = False
    winner = None
    
    # Create fonts
    message_font = pygame.font.SysFont("Arial", 36)
    
    # Draw initial board
    draw_board(screen, game_board)
    
    # Randomly decide who goes first
    turn = random.randint(PLAYER, AI)
    
    # Create players
    human_player = HumanPlayer(PLAYER_PIECE)
    ai_player = AIPlayer(AI_PIECE, difficulty=5)
    
    # Game loop
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
                
            if event.type == pygame.MOUSEMOTION and not game_over:
                pygame.draw.rect(screen, DARK_GRAY, (0, TITLE_HEIGHT, WIDTH, SQUARESIZE))
                posx = event.pos[0]
                
                if turn == PLAYER:
                    pygame.draw.circle(screen, ORANGE, (posx, TITLE_HEIGHT + SQUARESIZE//2), RADIUS)
                    pygame.display.update()
                    
            if event.type == pygame.MOUSEBUTTONDOWN:
                if game_over:
                    # Reset game
                    game_board = GameBoard()
                    game_over = False
                    winner = None
                    draw_board(screen, game_board)
                    turn = random.randint(PLAYER, AI)
                else:
                    if turn == PLAYER:
                        posx = event.pos[0]
                        col = int(math.floor(posx/SQUARESIZE))
                        
                        if 0 <= col < COLUMN_COUNT and game_board.is_valid_location(col):
                            row = game_board.get_next_open_row(col)
                            game_board.drop_piece(row, col, PLAYER_PIECE)
                            
                            # Check if player won
                            game_over, winner = game_board.check_win_or_draw(PLAYER_PIECE)
                            
                            turn = (turn + 1) % 2
                            game_board.print_board()
                            draw_board(screen, game_board)
                            
                            if game_over:
                                show_winner_message(screen, winner)
        
        # AI's turn
        if turn == AI and not game_over:
            pygame.draw.rect(screen, DARK_GRAY, (0, TITLE_HEIGHT, WIDTH, SQUARESIZE))
            thinking = message_font.render("AI is thinking...", True, WHITE)
            screen.blit(thinking, (WIDTH//2 - thinking.get_width()//2, TITLE_HEIGHT + SQUARESIZE//2 - thinking.get_height()//2))
            pygame.display.update()
            
            # Add a small delay to show the AI is thinking
            pygame.time.wait(500)
            
            # Get AI's move
            col = ai_player.get_move(game_board)
            
            if game_board.is_valid_location(col):
                row = game_board.get_next_open_row(col)
                game_board.drop_piece(row, col, AI_PIECE)
                
                # Check if AI won
                game_over, winner = game_board.check_win_or_draw(AI_PIECE)
                
                turn = (turn + 1) % 2
                game_board.print_board()
                draw_board(screen, game_board)
                
                if game_over:
                    show_winner_message(screen, winner)

if __name__ == "__main__":
    main()
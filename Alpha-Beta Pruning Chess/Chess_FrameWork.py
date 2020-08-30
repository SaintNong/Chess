from piece_squares import white_squares, eval_table
import Chess_Main
from math import inf as infinity
import numpy as np
# Wow multiple files?
# That's some overcomplicated stuff


"""
Massive Game State Class

stores all variables, methods, constants and functions to do with the chess board
"""
class game_state:
    
    # The actual evaluation Function
    def eval_board(self,board):
        white_score = 0
        black_score = 0
        for row in range(len(board)):
            for col in range(len(board[0])):
                if board[row][col] != "--":
                    piece = board[row][col][1]
                    if board[row][col][0] == "w":
                        white_score += eval_table[piece]
                        white_score += white_squares[piece][row][col]/2 # ooh fancy tables
                    else:
                        black_score += eval_table[piece]
                        black_score += black_squares[piece][row][col]/2 # even more fancy tables

        if self.check_mate:
            if not self.white_turn:
                white_score = 10000000
                black_score = -10000000
            else:
                black_score = 10000000
                white_score = -10000000
        elif self.stale_mate:
            black_score = white_score = 0
        try:
            white_score = int(white_score)
            black_score = int(black_score)
        except OverflowError:
            pass
        return white_score - black_score

    
    # Initialise board - setting up variables and constants
    def __init__(self):
        self.black_squares = black_squares = {}
        self.white_squares = white_squares
        self.move_functions = {"P":self.get_pawn_moves,"R":self.get_rook_moves,"Q":self.get_queen_moves,"N":self.get_knight_moves,"K":self.get_king_moves,"B":self.get_bishop_moves}
        self.black_squares = load_piece_square_tables(self.black_squares)
        # here's where the board is, cool right?
        self.board = [
        ["bR","bN","bB","bQ","bK","bB","bN","bR"],
        ["bP","bP","bP","bP","bP","bP","bP","bP"],
        ["--","--","--","--","--","--","--","--"],
        ["--","--","--","--","--","--","--","--"],
        ["--","--","--","--","--","--","--","--"],
        ["--","--","--","--","--","--","--","--"],
        ["wP","wP","wP","wP","wP","wP","wP","wP"],
        ["wR","wN","wB","wQ","wK","wB","wN","wR"]]
        self.white_turn = True
        self.move_log = []

        # the pain starts here
        self.current_castling_rights = castle_rights(True, True, True, True) # basically just keeps track of whether any "castling rules" have been broken by which side

        # this is so you can undo and redo castling moves
        self.castle_rights_log = [castle_rights(
            self.current_castling_rights.wks,self.current_castling_rights.bks,
            self.current_castling_rights.wqs,self.current_castling_rights.bqs
        )]

        # game end states
        self.check_mate = False
        self.stale_mate = False

        # load evaluation tables
        black_squares = load_piece_square_tables(black_squares)

        # initialising the all new  King Tracker 9000™
        self.white_king_loc = (7,4)
        self.black_king_loc = (0,4)

        # the pain intensifies
        self.enpassant_possible = ()
    
    # If you don't understand what this does then you are actually a dumbass
    def make_move(self, move):
        self.board[move.start_row][move.start_col] = "--"
        self.board[move.end_row][move.end_col] = move.piece_moved
        self.move_log.append(move)
        self.white_turn = not self.white_turn

        # king location tracking
        if move.piece_moved == "wK":
            self.white_king_loc = (move.end_row, move.end_col)
        elif move.piece_moved == "bK":
            self.black_king_loc = (move.end_row, move.end_col)
        
        # pawn promotions
        if move.is_pawn_promotion:
            self.board[move.end_row][move.end_col] = move.piece_moved[0] + "Q"
        
        # en passant stuff
        if move.is_enpassant_move:
            self.board[move.start_row][move.end_col] = "--" # capture the thing
        
        # update en passant possible variable
        if move.piece_moved[1] == "p" and abs(move.start_row - move.end_row) == 2: # check for 2 square pawn advances
            self.enpassant_possible = ((move.start_row + move.end_row)//2, move.start_col)
        else: # else thing which is absolubtly useless (Don't you dare judge my spelling)
            self.enpassant_possible = ()
        
        # update castling rights
        self.update_castle_rights(move)

        self.castle_rights_log.append(castle_rights(
            self.current_castling_rights.wks,self.current_castling_rights.bks,
            self.current_castling_rights.wqs,self.current_castling_rights.bqs
        )) # update castle rights log so undoing is possible
        return True

    
    def undo_move(self):
        if len(self.move_log) != 0:
            #removing move from logs
            move = self.move_log.pop()
            self.board[move.start_row][move.start_col] = move.piece_moved
            self.board[move.end_row][move.end_col] = move.piece_captured
            #turn tracking
            self.white_turn = not self.white_turn

            #king location tracking
            if move.piece_moved == "wK":
                self.white_king_loc = (move.start_row, move.start_col)
            elif move.piece_moved == "bK":
                self.black_king_loc = (move.start_row, move.start_col)
            
            #pawn promotion thing
            if move.is_pawn_promotion:
                self.board[move.start_row][move.start_col] = move.piece_moved[0] + "P"
            
            # en passant is so painful
            if move.is_enpassant_move:
                self.board[move.end_row][move.end_col] = "--"
                self.board[move.start_row][move.end_col] = move.piece_captured
                self.enpassant_possible = (move.end_row, move.end_col)
            
            # here's code which is REQUIRED because of GOD DAMN EN PASSANT
            if move.piece_moved[1] == "p" and abs(move.start_row - move.end_col) == 2:
                self.enpassant_possible = () # reset en passant possible variable because WHY THE HELL NOT!
            
            # for undoing castle rights logs and castling moves
            self.castle_rights_log.pop() # remove new castle rights from logs
            self.current_castling_rights = self.castle_rights_log[-1] # set current castle rights to the last one on the list

            # undoing a castle move
            if move.is_castle_move:
                if move.end_col - move.start_col == 2: # checking if it's a king side castle
                    self.board[move.end_row][move.end_col+1] = self.board[move.end_row][move.end_col-1] # puts a rook down
                    self.board[move.end_row][move.end_col-1] = "--" # erases a rook
                else: # queenside castle
                    self.board[move.end_row][move.end_col-2] = self.board[move.end_row][move.end_col+1] # puts a rook down
                    self.board[move.end_row][move.end_col+1] = "--" # erases a rook
            
            
    def update_castle_rights(self,move):
        if move.piece_moved == "wK": # white king moved
            self.current_castling_rights.wks = False
            self.current_castling_rights.wqs = False
        elif move.piece_moved == "bK": # black king moved
            self.current_castling_rights.bks = False
            self.current_castling_rights.bqs = False
        elif move.piece_moved == "wR": # white rook moved
            if move.start_row == 7:
                if move.start_col == 0:
                    self.current_castling_rights.wqs = False
                elif move.start_col == 7:
                    self.current_castling_rights.wks = False
        elif move.piece_moved == "bR": # black rook moved
            if move.start_row == 0:
                if move.start_col == 0:
                    self.current_castling_rights.bqs = False
                elif move.start_col == 7:
                    self.current_castling_rights.bks = False
            
    # checks if the king is in check
    def in_check(self):
        if self.white_turn:
            return self.square_under_attack(self.white_king_loc[0],self.white_king_loc[1])
        else:
            return self.square_under_attack(self.black_king_loc[0],self.black_king_loc[1])

    # this is literally used ONLY by the program that checks if we're in check so why does it exist?
    def square_under_attack(self,r,c):
        self.white_turn = not self.white_turn
        opponent_moves = self.get_possible_moves()
        self.white_turn = not self.white_turn
        for move in opponent_moves:
            if move.end_row == r and move.end_col == c:
                return True
        return False
    
    def get_valid_moves(self):
        # temporary variables because Python is weird and referencing stuff
        temp_enpassant_possible = self.enpassant_possible
        temp_castle_rights = castle_rights(
            self.current_castling_rights.wks,self.current_castling_rights.bks,
            self.current_castling_rights.wqs,self.current_castling_rights.bqs
        )

        moves = self.get_possible_moves()

        # castling is put here and not in get_possible_moves in order to evade infinite recursion from check and checkmate functions
        if self.white_turn:
            self.get_castle_moves(self.white_king_loc[0], self.white_king_loc[1], moves)
        else:
            self.get_castle_moves(self.black_king_loc[0], self.black_king_loc[1], moves)

        # random check-mate checking code which took WAY too long to make
        for i in range(len(moves)-1,-1,-1):
            self.make_move(moves[i])
            self.white_turn = not self.white_turn
            if self.in_check():
                moves.remove(moves[i])
            self.white_turn = not self.white_turn
            self.undo_move()
        if len(moves) == 0: # game ended states
            if self.in_check():
                self.check_mate = True
            else:
                self.stale_mate = True
        else:
            self.check_mate = False
            self.stale_mate = False
        
        self.enpassant_possible = temp_enpassant_possible
        self.current_castling_rights = temp_castle_rights
        return moves

    # This is just lazy programming for you to stare at
    def get_possible_moves(self):
        moves = []
        for row in range(len(self.board)):
            for col in range(len(self.board[0])):
                if self.board[row][col] != "--":
                    if (self.board[row][col][0] == "w" and self.white_turn) or (self.board[row][col][0] == "b" and not self.white_turn):
                        piece = self.board[row][col][1]
                        self.move_functions[piece](row,col,moves)
        return moves

    # long as hell, doesn't need to be
    def get_pawn_moves(self,row,col,moves):
        if self.white_turn:
            if 1 <= row < 7:
                if self.board[row-1][col] == "--":
                    moves.append(Move((row,col),(row-1,col),self.board))
                    if row == 6 and self.board[row-2][col] == "--":
                        moves.append(Move((row,col),(row-2,col),self.board))
                if col-1 >= 0 and row > 0:
                    if self.board[row-1][col-1][0] == "b":
                        moves.append(Move((row,col),(row-1,col-1),self.board))
                    elif (row-1, col-1) == self.enpassant_possible:
                        moves.append(Move((row,col),(row-1,col-1),self.board,is_enpassant_move=True))
                if col+1 <= 7 and row > 0:
                    if self.board[row-1][col+1][0] == "b":
                        moves.append(Move((row,col),(row-1,col+1),self.board))
                    elif (row-1, col+1) == self.enpassant_possible:
                        moves.append(Move((row,col),(row-1,col+1),self.board,is_enpassant_move=True))
        else:
            if 1 <= row < 7:
                if self.board[row+1][col] == "--":
                    moves.append(Move((row,col),(row+1,col),self.board))
                    if row == 1 and self.board[row+2][col] == "--":
                        moves.append(Move((row,col),(row+2,col),self.board))
                if col-1 >= 0 and row < 7:
                    if self.board[row+1][col-1][0] == "w":
                        moves.append(Move((row,col),(row+1,col-1),self.board))
                    elif (row+1, col-1) == self.enpassant_possible:
                        moves.append(Move((row,col),(row+1,col-1),self.board,is_enpassant_move=True))
                if col+1 <= 7 and row < 7:
                    if self.board[row+1][col+1][0] == "w":
                        moves.append(Move((row,col),(row+1,col+1),self.board))
                    elif (row+1, col+1) == self.enpassant_possible:
                        moves.append(Move((row,col),(row+1,col+1),self.board,is_enpassant_move=True))
    
    # Copy Pasted Stuff!
    def get_rook_moves(self,row,col,moves):
        directions = ((-1,0),(0,-1),(1,0),(0,1))
        enemy_color = "b" if self.white_turn else "w"
        for d in directions:
            for i in range(1, 8):
                end_row = row + d[0] * i
                end_col = col + d[1] * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    end_piece = self.board[end_row][end_col]
                    if end_piece == "--":
                        moves.append(Move((row,col),(end_row,end_col),self.board))
                    elif end_piece[0] == enemy_color:
                        moves.append(Move((row,col),(end_row,end_col),self.board))
                        break
                    else:
                        break
                else:
                    break

    # Copy Pasted Stuff!
    def get_bishop_moves(self,row,col,moves):
        directions = ((1,-1),(-1,1),(-1,-1),(1,1))
        enemy_color = "b" if self.white_turn else "w"
        for d in directions:
            for i in range(1, 7):
                end_row = row + d[0] * i
                end_col = col + d[1] * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    end_piece = self.board[end_row][end_col]
                    if end_piece == "--":
                        moves.append(Move((row,col),(end_row,end_col),self.board))
                    elif end_piece[0] == enemy_color:
                        moves.append(Move((row,col),(end_row,end_col),self.board))
                        break
                    else:
                        break
                else:
                    break
    
    # Copy Pasted Stuff!
    def get_king_moves(self,row,col,moves):

        # normal king moves
        directions = ((1,-1),(-1,1),(-1,-1),(1,1),(-1,0),(0,-1),(1,0),(0,1))
        enemy_color = "b" if self.white_turn else "w"
        for d in directions:
            end_row = row + d[0]
            end_col = col + d[1]
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                end_piece = self.board[end_row][end_col]
                if end_piece == "--":
                    moves.append(Move((row,col),(end_row,end_col),self.board))
                elif end_piece[0] == enemy_color:
                    moves.append(Move((row,col),(end_row,end_col),self.board))


    # generates all valid castling moves for a king at (r, c) and then adds them to the list of moves
    def get_castle_moves(self, r, c, moves):
        if self.square_under_attack(r, c):
            return
        if (self.white_turn and self.current_castling_rights.wks) or (not self.white_turn and self.current_castling_rights.bks):
            self.get_kingSide_castle_moves(r, c, moves)
        if (self.white_turn and self.current_castling_rights.wqs) or (not self.white_turn and self.current_castling_rights.bqs):
            self.get_queenSide_castle_moves(r, c, moves)
        
    
    def get_kingSide_castle_moves(self, r, c, moves):
        if self.board[r][c+1] == "--" and self.board[r][c+2] == "--":
            if not self.square_under_attack(r, c+1) and not self.square_under_attack(r, c+2):
                moves.append(Move((r, c), (r, c+2), self.board, is_castle_move=True))

    def get_queenSide_castle_moves(self, r, c, moves):
        if self.board[r][c-1] == "--" and self.board[r][c-2] == "--" and self.board[r][c-3] == "--":
            if not self.square_under_attack(r, c-1) and not self.square_under_attack(r, c-2):
                moves.append(Move((r, c), (r, c-2), self.board, is_castle_move=True))

    # Copy Pasted Stuff!
    def get_queen_moves(self,row,col,moves):
        directions = ((1,-1),(-1,1),(-1,-1),(1,1),(-1,0),(0,-1),(1,0),(0,1))
        enemy_color = "b" if self.white_turn else "w"
        for d in directions:
            for i in range(1, 8):
                end_row = row + d[0] * i
                end_col = col + d[1] * i
                if 0 <= end_row < 8 and 0 <= end_col < 8:
                    end_piece = self.board[end_row][end_col]
                    if end_piece == "--":
                        moves.append(Move((row,col),(end_row,end_col),self.board))
                    elif end_piece[0] == enemy_color:
                        moves.append(Move((row,col),(end_row,end_col),self.board))
                        break
                    else:
                        break
                else:
                    break

    # Copy Pasted Stuff!
    def get_knight_moves(self,row,col,moves):
        knight_moves = ((-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1))
        enemy_color = "b" if self.white_turn else "w"
        for m in knight_moves:
            end_row = row + m[0]
            end_col = col + m[1]
            if 0 <= end_row < 8 and 0 <= end_col < 8:
                end_piece = self.board[end_row][end_col]
                if end_piece == "--":
                    moves.append(Move((row,col),(end_row,end_col),self.board))
                elif end_piece[0] == enemy_color:
                    moves.append(Move((row,col),(end_row,end_col),self.board))

"""
Yes, i made an entire class for this.
don't judge
"""

class castle_rights:

    # basically just a data storage class
    def __init__(self, wks, bks, wqs, bqs):

        # white and black king side castle
        self.wks = wks
        self.bks = bks

        # white and black queen side castle
        self.wqs = wqs
        self.bqs = bqs

"""
Move class which states all the data within a move...

except for the move evaluation which FOR SOME GOD FORSAKEN REASON IS HANDLED BY THE BOARD.
WHY? I DON'T KNOW WHY DON'T ASK ME
"""
class Move:
    ranks_to_rows = {"1":7, "2":6, "3":5, "4":4, "5":3, "6":2, "7":1, "8":0}
    rows_to_ranks = {v: k for k, v in ranks_to_rows.items()}

    files_to_cols = {"a":0, "b":1, "c":2, "d":3, "e":4, "f":5, "g":6, "h":7, "i":8}
    cols_to_files = {v: k for k, v in files_to_cols.items()}
    
    def __init__(self,start_sq,end_sq,board, is_enpassant_move = False, is_castle_move=False):
        # coordinates to tell the move how it moves and what it does before and after the move
        self.start_row = start_sq[0]
        self.start_col = start_sq[1]
        self.end_row = end_sq[0]
        self.end_col = end_sq[1]
        self.piece_captured = board[self.end_row][self.end_col]
        self.piece_moved = board[self.start_row][self.start_col]
        self.move_id = self.start_row*1000+self.start_col*100+self.end_row*10+self.end_col
        # pawn promotion
        self.is_pawn_promotion = (self.piece_moved == "wP" and self.end_row == 0) or (self.piece_moved == "bP" and self.end_row == 7)
        # en passant
        self.is_enpassant_move = is_enpassant_move
        if self.is_enpassant_move:
            self.piece_captured = "wP" if self.piece_moved == "bP" else "bP" # basically it sets the piece captured to a white pawn but only sometimes...
        
        # castle moves
        self.is_castle_move = is_castle_move
    
    
    # ai sorting to find "good" paths to search first
    def get_value(self):
        value = 0
        if self.piece_captured != "--":
            value = eval_table[self.piece_captured[1]]
            if self.piece_moved[1] != "K":
                if self.piece_moved[0] == "w":
                    value -= eval_table[self.piece_moved[1]]//1.6
                elif self.piece_moved[0] == "b":
                    value -= eval_table[self.piece_moved[1]]//1.6
            else:
                value -= 50
        if self.piece_moved[0] == "w":
            value += white_squares[self.piece_moved[1]][self.end_row][self.end_col]
        else:
            value += black_squares[self.piece_moved[1]][self.end_row][self.end_col]
        return value

    # overriding equals operator
    def __eq__(self,other):
        if isinstance(other,Move) and self.move_id == other.move_id:
            return True
        else:
            return False
    
    # for nerds
    def get_chess_notation(self):
        return self.get_rank_file(self.start_row,self.start_col) + " to " + self.get_rank_file(self.end_row, self.end_col)
    
    # why does this exist? it is so pointless that i think i might just delete it but that might break another more important function tied to this so...
    def get_rank_file(self, row, col):
        return self.cols_to_files[col] + self.rows_to_ranks[row]

def load_piece_square_tables(black_squares):
    black_squares = {}
    for k in white_squares:
        new_square_list = white_squares[k]
        black_squares[k] = new_square_list[::-1]
    return black_squares

black_squares = {}
black_squares = load_piece_square_tables(black_squares)

"""
for when Ning is too lazy to open Chess_Main.py to run the actual code.

This just does it for him because he's a smart boy he doesn't have to work right? :D  (Both are lies)
"""

if __name__ == "__main__":
    print("\nYou ran the wrong file you moron!\n\n\n") # remind Ning about the truth before running
    Chess_Main.main()


# "Damn that's more lines of code than I thought" he says while adding an extra line just to write this

import Chess_FrameWork
from math import inf as infinity
from random import choice
import time

choices = [True,False]
positions = 0

# handles the Alpha-Beta search algorithm
def get_ai_move(game_state, time_amount):
    global positions
    positions = 0
    current_time = time.time()
    temp_castle_rights = Chess_FrameWork.castle_rights(
        game_state.current_castling_rights.wks, game_state.current_castling_rights.bks,
        game_state.current_castling_rights.wqs, game_state.current_castling_rights.bqs
    )
    move = AlphaBeta(game_state, 10, -infinity, infinity, False, time.time()+time_amount, 10)
    game_state.current_castling_rights = temp_castle_rights
    elapsed = time.time()
    time_taken = current_time-elapsed
    print("Moves analysed:  "+str(positions))
    print("Time Taken to Think:  "+str(round(abs(time_taken),3))+" seconds")
    return move


# the actual algorithm which searches for good moves optimally (mostly)
def AlphaBeta(game_state, depth, alpha, beta, is_max, time_out, max_depth, return_numeral=False):
    global positions
    if depth == 0 or (time.time() > time_out and depth < (max_depth - 2)) or game_state.check_mate or game_state.stale_mate:
        return game_state.eval_board(game_state.board)  # returns board evaluation if the game state is terminal or depth has exceeded maximum or timeout has occured
    
    possible_moves = game_state.get_valid_moves()
    possible_moves.sort(key=lambda move: move.get_value(), reverse=True) # sort the moves in a rough order to get better moves

    best_move = Chess_FrameWork.Move((0, 0),(0, 0),game_state.board)
    if is_max:
        best_score = -infinity
        for move in possible_moves:
            positions += 1
            game_state.make_move(move)
            old_score = best_score
            best_score = max(best_score, AlphaBeta(game_state, depth - 1, alpha, beta, False, time_out, max_depth, return_numeral=True))
            game_state.undo_move()
            if best_score != old_score:
                best_move = move
            alpha = max(alpha, best_score)
            if beta < alpha:
                break
        if return_numeral:
            return best_score
        else:
            return best_move
    else:
        best_score = infinity
        for move in possible_moves:
            positions += 1
            game_state.make_move(move)
            old_score = best_score
            best_score = min(best_score, AlphaBeta(game_state, depth - 1, alpha, beta, True, time_out, max_depth, return_numeral=True))
            game_state.undo_move()
            if best_score != old_score:
                best_move = move
            beta = min(beta, best_score)
            if beta < alpha:
                break

        if return_numeral:
            return best_score
        else:
            return best_move

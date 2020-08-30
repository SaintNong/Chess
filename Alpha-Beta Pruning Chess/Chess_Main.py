# why are u looking at my code?

# Imports my other files
import Chess_FrameWork, sys
from os import environ
environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1' # remove annoying pygame support prompt
import pygame as pg
from Chess_AI import get_ai_move

"""
This program mainly handles the rendering and mouse input while the other programs do the "thinking" if you know what i mean
"""


# setting all the constants
MAX_FPS = 30
WIDTH = HEIGHT = 544
DIMENSION = 8
SQ_SIZE = HEIGHT // DIMENSION
selected_color = pg.Color("yellow")
piece_selected_color = pg.Color(107,142,35)

# image handler
IMAGES = {}
def load_images():
    base_path = "/Users/ning/Desktop/Coding Stuff In General/General AI Stuff/Alpha-Beta Pruning Chess/resources/images/"
    colors = ["w","b"]
    pieces = ["P","R","N","B","Q","K"]
    for color in colors:
        for piece in pieces:
            IMAGES[color+piece] = pg.transform.scale(pg.image.load(base_path+color+piece+".png"),(SQ_SIZE,SQ_SIZE))

# the checkerboard pattern is rendered here
def render_board_background(screen):
    global colors
    colors = [pg.Color("white"),(160, 114, 79)]
    for y in range(DIMENSION):
        for x in range(DIMENSION):
            color = colors[((x+y) % 2)]
            pg.draw.rect(screen,color,pg.Rect(x*SQ_SIZE,y*SQ_SIZE,SQ_SIZE,SQ_SIZE))

# pieces are put on the board
def render_pieces(screen,game_state):
    board = game_state.board
    for y in range(DIMENSION):
        for x in range(DIMENSION):
            piece = board[x][y]
            if piece != "--":
                screen.blit(IMAGES[piece],pg.Rect(y*SQ_SIZE, x*SQ_SIZE, SQ_SIZE ,SQ_SIZE))

def draw_text(screen, text, font):
    text_object = font.render(text, 0, pg.Color("Black"))
    text_location = pg.Rect(0, 0, WIDTH, HEIGHT).move(WIDTH//2 - text_object.get_width()//2, HEIGHT//2 - text_object.get_height()//2)
    screen.blit(text_object, text_location)

# yay now my game looks sexy
def animate_move(move, screen, game_state, clock, frames_per_square):
    global colors

    dR = move.end_row - move.start_row
    dC = move.end_col - move.start_col
    frame_count = (abs(dR) + abs(dC)) * frames_per_square
    for frame in range(frame_count + 1):
        r, c = (move.start_row + dR*frame/frame_count, move.start_col + dC*frame/frame_count)

        # render the board before we draw our frame
        render_board_background(screen)
        render_pieces(screen, game_state)

        # erase the already moved piece while we're animating
        color = colors[(move.end_row + move.end_col)%2]
        end_square = pg.Rect(move.end_col*SQ_SIZE, move.end_row*SQ_SIZE, SQ_SIZE, SQ_SIZE)
        pg.draw.rect(screen, color, end_square)

        # draw the captured piece onto the rectangle
        if move.piece_captured != "--":
            screen.blit(IMAGES[move.piece_captured], end_square)
        
        # draw moving piece
        screen.blit(IMAGES[move.piece_moved], pg.Rect(c*SQ_SIZE, r*SQ_SIZE, SQ_SIZE, SQ_SIZE))
        pg.display.flip()
        clock.tick(60)


# really long piece of code that just highlights a piece and where it can move
def render_selected_square(screen, sq_selected, valid_moves, gs):
    if sq_selected != ():
        r, c = sq_selected
        if gs.board[r][c][0] == ("w" if gs.white_turn else "b"): # checks if the piece can be moved
            s = pg.Surface((SQ_SIZE, SQ_SIZE))
            s.fill(piece_selected_color)
            s.set_alpha(300)
            screen.blit(s, (c*SQ_SIZE,r*SQ_SIZE))
            s.set_alpha(100)
            s.fill(selected_color)
            for move in valid_moves:
                if move.start_row == r and move.start_col == c:
                    screen.blit(s, (move.end_col*SQ_SIZE,move.end_row*SQ_SIZE))

# activates the 3 functions shown above
def render_game_state(screen, game_state, sq_selected, valid_moves):
    render_board_background(screen)
    render_selected_square(screen, sq_selected, valid_moves, game_state)
    render_pieces(screen,game_state)

# the main game and game loop
def main():

    print("welcome to the command line input for Ning's Chess Algorithm!!!") # gotta be nice

    # makes sure that you can choose to be beaten by the AI
    single_player = True
    choice = int(input("Do you want to play against the AI or play 2 player mode? [1/2]\n\n      :"))
    if choice == 1:
        single_player = True
    else:
        single_player = False

    # set AI difficulty
    if single_player:
        time_amount = float(input("\n\nHow long should the AI think for on each move? [enter an answer in seconds]\n\n      :"))

    # pygame variables
    pg.init()
    screen = pg.display.set_mode((WIDTH,HEIGHT))
    screen.fill(pg.Color("white"))
    clock = pg.time.Clock()
    pg.display.set_caption("Chess")

    # flag variable for when to animate a move
    animate = False

    # initialise a game_state class
    game_state = Chess_FrameWork.game_state()

    # gotta do that or else you're gonna play chess blindly
    load_images()

    # pre-loading a font to reduce lag
    font = pg.font.SysFont("Helvetica", 32, True, False)

    # loading sounds
    base_path = "/Users/ning/Desktop/Coding Stuff In General/General AI Stuff/Alpha-Beta Pruning Chess/resources/sounds/"
    move_sound = pg.mixer.Sound(base_path+"move.wav")
    check_sound = pg.mixer.Sound(base_path+"check.wav")
    capture_sound = pg.mixer.Sound(base_path+"capture.wav")

    # this makes sure that you can close the game
    running = True

    # square selection variables
    sq_selected = ()
    player_clicks = []
    
    # move handling
    valid_moves = game_state.get_valid_moves()
    move_made = False

    game_over = False


    # game loop which handles input (clicks and stuff) output (a chess board)
    while running:
        # haha event handling go (System Exception: Type Error: Variable Fuck_You isn't defined)
        for event in pg.event.get():

            # quits the game when you click the X button at the top of the screen
            if event.type == pg.QUIT:
                running = False
                pg.quit()
                sys.exit()
            
            # mouse input detection
            elif event.type == pg.MOUSEBUTTONDOWN:
                if not game_over:
                    location = pg.mouse.get_pos()
                    # detects which square you clicked on
                    col = location[0]//SQ_SIZE
                    row = location[1]//SQ_SIZE
                    if sq_selected == (row,col):
                        sq_selected = ()
                        player_clicks = []
                    else:
                        sq_selected = (row,col)
                        player_clicks.append(sq_selected)
                    
                    # if you click twice, then stuff happens
                    if len(player_clicks) == 2:
                        move = Chess_FrameWork.Move(player_clicks[0],player_clicks[1],game_state.board)

                        # makes the game update the valid move list
                        for i in range(len(valid_moves)):
                            if move == valid_moves[i]:
                                game_state.make_move(valid_moves[i])
                                if game_state.in_check():
                                    check_sound.play()
                                else:
                                    if move.piece_captured != "--":
                                        capture_sound.play()
                                    else:
                                        move_sound.play()
                                move_made = True
                                animate = True
                                sq_selected = ()
                        if not move_made:
                            player_clicks = [sq_selected]
                        player_clicks = []
            
            # the "Undo Button" for when your opponent is too good
            elif event.type == pg.KEYDOWN:
                if event.key == pg.K_z or event.key == pg.K_LEFT:
                    game_state.undo_move()
                    if game_state.in_check():
                        check_sound.play()
                    else:
                        move_sound.play()
                    move_made = True
                    animate = False

                    if single_player:
                        game_state.undo_move()
            
                if event.key == pg.K_r: # resets the board
                    game_state = Chess_FrameWork.game_state()
                    valid_moves = game_state.get_valid_moves()
                    sq_selected = ()
                    player_clicks = []
                    move_made = False
                    animate = False

        # updates list of valid moves
        if move_made:
            if len(game_state.move_log) > 0 and animate:
                animate_move(game_state.move_log[-1], screen, game_state, clock, 3)
            valid_moves = game_state.get_valid_moves()
            move_made = False
            animate = False

            # scoring for the AIs to look at
            game_score = game_state.eval_board(game_state.board)
            print("Score:  "+str(game_score)+"\n")

        if game_state.check_mate:
            game_over = True
            if not game_state.white_turn:
                draw_text(screen, "White wins by Checkmate!!", font)
            else:
                draw_text(screen, "Black wins by Checkmate!!", font)
        elif game_state.stale_mate:
            game_over = True
            draw_text(screen, "It's a Stalemate!", font)

        # pygame rendering
        if not game_over:
            render_game_state(screen, game_state, sq_selected, valid_moves)
        

        # AI YESS
        if not game_state.white_turn and single_player:
            render_game_state(screen, game_state, sq_selected, valid_moves)
            clock.tick(MAX_FPS)
            pg.display.flip()
            if not game_state.check_mate:
                move = get_ai_move(game_state, time_amount - 0.1)
                game_state.make_move(move)
            if game_state.in_check():
                check_sound.play()
            else:
                if move.piece_captured != "--":
                    capture_sound.play()
                else:
                    move_sound.play()
            game_state.white_turn = True
            move_made = True
            animate = True
            valid_moves = game_state.get_valid_moves()

        clock.tick(MAX_FPS) 
        pg.display.flip()

# this makes my program look smarter than it actually is
if __name__ == "__main__":
    main()

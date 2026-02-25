"""
Tetris for Waveshare 128x128 LCD with GPIO buttons.
Renders directly to the display using PIL.
Press KEY1, KEY2, or KEY3 to exit and return to menu.
"""

import random 
import time 


COLORS =[
(0 ,0 ,0 ),
(120 ,37 ,179 ),
(100 ,179 ,179 ),
(80 ,134 ,22 ),
(180 ,134 ,22 ),
(180 ,34 ,22 ),
(180 ,34 ,122 ),
(80 ,80 ,200 ),
]


FIGURES =[
[[1 ,5 ,9 ,13 ],[4 ,5 ,6 ,7 ]],
[[4 ,5 ,9 ,10 ],[2 ,6 ,5 ,9 ]],
[[6 ,7 ,9 ,10 ],[1 ,5 ,6 ,10 ]],
[[1 ,2 ,5 ,9 ],[0 ,4 ,5 ,6 ],[1 ,5 ,9 ,8 ],[4 ,5 ,6 ,10 ]],
[[1 ,2 ,6 ,10 ],[5 ,6 ,7 ,9 ],[2 ,6 ,10 ,11 ],[3 ,5 ,6 ,7 ]],
[[1 ,4 ,5 ,6 ],[1 ,4 ,5 ,9 ],[4 ,5 ,6 ,9 ],[1 ,5 ,6 ,9 ]],
[[1 ,2 ,5 ,6 ]],
]


class Figure :
    def __init__ (self ,x ,y ):
        self .x =x 
        self .y =y 
        self .type =random .randint (0 ,len (FIGURES )-1 )
        self .color =random .randint (1 ,len (COLORS )-1 )
        self .rotation =0 

    def image (self ):
        return FIGURES [self .type ][self .rotation ]

    def rotate (self ):
        self .rotation =(self .rotation +1 )%len (FIGURES [self .type ])


class TetrisGame :
    def __init__ (self ,height =20 ,width =10 ):
        self .height =height 
        self .width =width 
        self .field =[[0 ]*width for _ in range (height )]
        self .score =0 
        self .level =1 
        self .state ="playing"
        self .figure =None 
        self .new_figure ()

    def new_figure (self ):
        self .figure =Figure (self .width //2 -2 ,0 )
        if self .intersects ():
            self .state ="gameover"

    def intersects (self ):
        for i in range (4 ):
            for j in range (4 ):
                if i *4 +j in self .figure .image ():
                    fx =j +self .figure .x 
                    fy =i +self .figure .y 
                    if fy >=self .height or fx <0 or fx >=self .width :
                        return True 
                    if fy >=0 and self .field [fy ][fx ]>0 :
                        return True 
        return False 

    def freeze (self ):
        for i in range (4 ):
            for j in range (4 ):
                if i *4 +j in self .figure .image ():
                    fy =i +self .figure .y 
                    fx =j +self .figure .x 
                    if 0 <=fy <self .height and 0 <=fx <self .width :
                        self .field [fy ][fx ]=self .figure .color 
        self .break_lines ()
        self .new_figure ()

    def break_lines (self ):
        lines =0 
        for i in range (self .height -1 ,0 ,-1 ):
            if 0 not in self .field [i ]:
                lines +=1 
                del self .field [i ]
                self .field .insert (0 ,[0 ]*self .width )
        self .score +=lines *lines *100 

        self .level =1 +self .score //500 

    def go_down (self ):
        self .figure .y +=1 
        if self .intersects ():
            self .figure .y -=1 
            self .freeze ()

    def go_side (self ,dx ):
        old_x =self .figure .x 
        self .figure .x +=dx 
        if self .intersects ():
            self .figure .x =old_x 

    def rotate (self ):
        old_rotation =self .figure .rotation 
        self .figure .rotate ()
        if self .intersects ():
            self .figure .rotation =old_rotation 

    def drop (self ):
        while not self .intersects ():
            self .figure .y +=1 
        self .figure .y -=1 
        self .freeze ()


class TetrisWaveshare :
    """Tetris game that renders to Waveshare 128x128 display."""

    def __init__ (self ,display ,input_handler ):
        self .display =display 
        self .input_handler =input_handler 
        self .running =False 





        self .cell_size =5 
        self .board_x =2 
        self .board_y =8 
        self .board_width =10 
        self .board_height =20 

        self .game =None 
        self .last_drop_time =0 
        self .drop_interval =0.5 

    def start (self ):
        """Start the Tetris game loop."""
        self .game =TetrisGame (self .board_height ,self .board_width )
        self .running =True 
        self .last_drop_time =time .time ()


        self .render ()

        while self .running :

            action =self .input_handler .get_input ()


            if action in ('key1','key2','key3'):
                self .running =False 
                return action 


            if self .game .state =="playing":
                if action =='left':
                    self .game .go_side (-1 )
                    self .render ()
                elif action =='right':
                    self .game .go_side (1 )
                    self .render ()
                elif action =='down':
                    self .game .go_down ()
                    self .render ()
                elif action =='up':
                    self .game .rotate ()
                    self .render ()
                elif action =='select':
                    self .game .drop ()
                    self .render ()


                current_time =time .time ()
                drop_speed =max (0.1 ,self .drop_interval -(self .game .level -1 )*0.05 )
                if current_time -self .last_drop_time >drop_speed :
                    self .game .go_down ()
                    self .last_drop_time =current_time 
                    self .render ()

            elif self .game .state =="gameover":

                if action =='select':
                    self .game =TetrisGame (self .board_height ,self .board_width )
                    self .render ()

            time .sleep (0.02 )

        return None 

    def render (self ):
        """Render the game to the Waveshare display."""

        self .display .clear ((20 ,20 ,30 ))
        draw =self .display .draw 


        score_text =f"Score: {self .game .score }"
        draw .text ((2 ,0 ),score_text ,font =self .display .font_tiny ,fill =(255 ,255 ,255 ))


        level_text =f"L{self .game .level }"
        draw .text ((100 ,0 ),level_text ,font =self .display .font_tiny ,fill =(200 ,200 ,100 ))


        border_x =self .board_x -1 
        border_y =self .board_y -1 
        border_w =self .board_width *self .cell_size +2 
        border_h =self .board_height *self .cell_size +2 
        draw .rectangle (
        (border_x ,border_y ,border_x +border_w ,border_y +border_h ),
        outline =(100 ,100 ,100 )
        )


        for row in range (self .board_height ):
            for col in range (self .board_width ):
                cell_val =self .game .field [row ][col ]
                if cell_val >0 :
                    self ._draw_cell (col ,row ,COLORS [cell_val ])


        if self .game .figure and self .game .state =="playing":
            for i in range (4 ):
                for j in range (4 ):
                    if i *4 +j in self .game .figure .image ():
                        fx =j +self .game .figure .x 
                        fy =i +self .game .figure .y 
                        if 0 <=fy <self .board_height and 0 <=fx <self .board_width :
                            self ._draw_cell (fx ,fy ,COLORS [self .game .figure .color ])


        if self .game .figure :
            self ._draw_next_preview ()


        hint ="^Rot <> vDn [O]Drop"
        draw .text ((2 ,118 ),hint ,font =self .display .font_tiny ,fill =(100 ,100 ,100 ))


        if self .game .state =="gameover":

            draw .rectangle ((10 ,40 ,118 ,90 ),fill =(40 ,40 ,40 ),outline =(255 ,100 ,100 ))
            draw .text ((20 ,50 ),"GAME OVER",font =self .display .font_medium ,fill =(255 ,100 ,100 ))
            draw .text ((18 ,68 ),f"Score: {self .game .score }",font =self .display .font_small ,fill =(255 ,255 ,255 ))
            draw .text ((22 ,80 ),"[O] Restart",font =self .display .font_tiny ,fill =(150 ,255 ,150 ))


        self .display ._render ()

    def _draw_cell (self ,col ,row ,color ):
        """Draw a single cell on the game board."""
        x =self .board_x +col *self .cell_size 
        y =self .board_y +row *self .cell_size 

        self .display .draw .rectangle (
        (x ,y ,x +self .cell_size -1 ,y +self .cell_size -1 ),
        fill =color ,
        outline =(min (255 ,color [0 ]+30 ),min (255 ,color [1 ]+30 ),min (255 ,color [2 ]+30 ))
        )

    def _draw_next_preview (self ):
        """Draw next piece indicator on the right side."""
        preview_x =70 
        preview_y =20 
        preview_size =3 

        self .display .draw .text ((preview_x ,10 ),"Next:",font =self .display .font_tiny ,fill =(150 ,150 ,150 ))




        self .display .draw .rectangle (
        (preview_x ,preview_y ,preview_x +20 ,preview_y +20 ),
        outline =(60 ,60 ,60 )
        )


def run_tetris (display ,input_handler ):
    """
    Run Tetris game on the Waveshare display.
    Returns the exit key pressed ('key1', 'key2', 'key3') or None.
    """
    game =TetrisWaveshare (display ,input_handler )
    return game .start ()

"""
Doom-style raycaster for Waveshare 128x128 LCD.
A proper Wolfenstein 3D / Doom-style first-person shooter experience.
Press KEY1, KEY2, or KEY3 to exit and return to menu.
"""

import math 
import time 
import random 


COLOR_CEILING =(30 ,30 ,50 )
COLOR_FLOOR =(50 ,50 ,40 )


WALL_COLORS ={
1 :((180 ,60 ,60 ),(140 ,40 ,40 )),
2 :((60 ,60 ,180 ),(40 ,40 ,140 )),
3 :((60 ,180 ,60 ),(40 ,140 ,40 )),
4 :((180 ,180 ,60 ),(140 ,140 ,40 )),
5 :((180 ,60 ,180 ),(140 ,40 ,140 )),
}


GAME_MAP =[
[1 ,1 ,1 ,1 ,1 ,1 ,1 ,1 ,1 ,1 ,1 ,1 ,1 ,1 ,1 ,1 ,1 ,1 ,1 ,1 ],
[1 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,1 ],
[1 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,1 ],
[1 ,0 ,0 ,2 ,2 ,2 ,0 ,0 ,0 ,0 ,0 ,0 ,3 ,3 ,3 ,0 ,0 ,0 ,0 ,1 ],
[1 ,0 ,0 ,2 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,3 ,0 ,0 ,0 ,0 ,1 ],
[1 ,0 ,0 ,2 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,3 ,0 ,0 ,0 ,0 ,1 ],
[1 ,0 ,0 ,0 ,0 ,0 ,0 ,4 ,4 ,4 ,4 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,1 ],
[1 ,0 ,0 ,0 ,0 ,0 ,0 ,4 ,0 ,0 ,4 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,1 ],
[1 ,0 ,0 ,0 ,0 ,0 ,0 ,4 ,0 ,0 ,4 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,1 ],
[1 ,0 ,0 ,0 ,0 ,0 ,0 ,4 ,4 ,0 ,4 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,1 ],
[1 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,1 ],
[1 ,0 ,0 ,5 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,5 ,5 ,5 ,0 ,0 ,1 ],
[1 ,0 ,0 ,5 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,5 ,0 ,0 ,1 ],
[1 ,0 ,0 ,5 ,5 ,5 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,5 ,0 ,0 ,1 ],
[1 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,1 ],
[1 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,1 ],
[1 ,0 ,0 ,0 ,0 ,2 ,2 ,2 ,2 ,2 ,2 ,2 ,2 ,0 ,0 ,0 ,0 ,0 ,0 ,1 ],
[1 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,1 ],
[1 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,0 ,1 ],
[1 ,1 ,1 ,1 ,1 ,1 ,1 ,1 ,1 ,1 ,1 ,1 ,1 ,1 ,1 ,1 ,1 ,1 ,1 ,1 ],
]

MAP_WIDTH =len (GAME_MAP [0 ])
MAP_HEIGHT =len (GAME_MAP )


DEMON_SPRITE =[
"  RRRR  ",
" RRRRRR ",
"RRRYYRRR",
"RRYYYRRR",
"RRRRRRRR",
"RWRRRWRR",
" RRRRRR ",
"  RRRR  ",
]

SPRITE_COLORS ={
'R':(200 ,50 ,50 ),
'Y':(255 ,255 ,100 ),
'W':(255 ,255 ,255 ),
' ':None ,
}


class Enemy :
    def __init__ (self ,x ,y ):
        self .x =x 
        self .y =y 
        self .alive =True 
        self .size =0.5 


class DoomGame :
    def __init__ (self ):

        self .player_x =2.0 
        self .player_y =2.0 
        self .player_angle =0.0 


        self .move_speed =0.12 
        self .rot_speed =0.1 


        self .fov =math .pi /3 
        self .render_width =128 
        self .render_height =100 


        self .enemies =[
        Enemy (10.5 ,10.5 ),
        Enemy (5.5 ,8.5 ),
        Enemy (15.5 ,5.5 ),
        Enemy (8.5 ,15.5 ),
        ]


        self .shooting =False 
        self .shoot_frame =0 
        self .health =100 
        self .ammo =50 
        self .kills =0 

    def move_forward (self ):
        new_x =self .player_x +math .cos (self .player_angle )*self .move_speed 
        new_y =self .player_y +math .sin (self .player_angle )*self .move_speed 
        if GAME_MAP [int (self .player_y )][int (new_x )]==0 :
            self .player_x =new_x 
        if GAME_MAP [int (new_y )][int (self .player_x )]==0 :
            self .player_y =new_y 

    def move_backward (self ):
        new_x =self .player_x -math .cos (self .player_angle )*self .move_speed 
        new_y =self .player_y -math .sin (self .player_angle )*self .move_speed 
        if GAME_MAP [int (self .player_y )][int (new_x )]==0 :
            self .player_x =new_x 
        if GAME_MAP [int (new_y )][int (self .player_x )]==0 :
            self .player_y =new_y 

    def turn_left (self ):
        self .player_angle -=self .rot_speed 

    def turn_right (self ):
        self .player_angle +=self .rot_speed 

    def shoot (self ):
        if self .ammo >0 and not self .shooting :
            self .shooting =True 
            self .shoot_frame =5 
            self .ammo -=1 


            for enemy in self .enemies :
                if enemy .alive :

                    dx =enemy .x -self .player_x 
                    dy =enemy .y -self .player_y 
                    dist =math .sqrt (dx *dx +dy *dy )
                    angle_to_enemy =math .atan2 (dy ,dx )


                    angle_diff =(angle_to_enemy -self .player_angle +math .pi )%(2 *math .pi )-math .pi 


                    if abs (angle_diff )<0.2 and dist <10 :
                        enemy .alive =False 
                        self .kills +=1 

    def update (self ):
        if self .shoot_frame >0 :
            self .shoot_frame -=1 
            if self .shoot_frame ==0 :
                self .shooting =False 

    def cast_ray (self ,angle ):
        """Cast a ray and return (distance, wall_type, side)."""
        ray_dir_x =math .cos (angle )
        ray_dir_y =math .sin (angle )

        map_x =int (self .player_x )
        map_y =int (self .player_y )

        delta_dist_x =abs (1 /ray_dir_x )if ray_dir_x !=0 else 1e30 
        delta_dist_y =abs (1 /ray_dir_y )if ray_dir_y !=0 else 1e30 

        if ray_dir_x <0 :
            step_x =-1 
            side_dist_x =(self .player_x -map_x )*delta_dist_x 
        else :
            step_x =1 
            side_dist_x =(map_x +1.0 -self .player_x )*delta_dist_x 

        if ray_dir_y <0 :
            step_y =-1 
            side_dist_y =(self .player_y -map_y )*delta_dist_y 
        else :
            step_y =1 
            side_dist_y =(map_y +1.0 -self .player_y )*delta_dist_y 

        hit =False 
        side =0 
        wall_type =1 

        for _ in range (64 ):
            if side_dist_x <side_dist_y :
                side_dist_x +=delta_dist_x 
                map_x +=step_x 
                side =0 
            else :
                side_dist_y +=delta_dist_y 
                map_y +=step_y 
                side =1 

            if 0 <=map_x <MAP_WIDTH and 0 <=map_y <MAP_HEIGHT :
                if GAME_MAP [map_y ][map_x ]>0 :
                    hit =True 
                    wall_type =GAME_MAP [map_y ][map_x ]
                    break 

        if not hit :
            return 64 ,1 ,side 

        if side ==0 :
            perp_dist =(map_x -self .player_x +(1 -step_x )/2 )/ray_dir_x if ray_dir_x !=0 else 64 
        else :
            perp_dist =(map_y -self .player_y +(1 -step_y )/2 )/ray_dir_y if ray_dir_y !=0 else 64 

        return abs (perp_dist ),wall_type ,side 


class DoomRenderer :
    """Renders the Doom game to the Waveshare display."""

    def __init__ (self ,display ,input_handler ):
        self .display =display 
        self .input_handler =input_handler 
        self .game =DoomGame ()
        self .running =False 

        self .z_buffer =[0 ]*128 

    def start (self ):
        """Main game loop."""
        self .running =True 
        last_time =time .time ()

        while self .running :

            action =self .input_handler .get_input ()

            if action in ('key1','key2','key3'):
                self .running =False 
                return action 

            if action =='up':
                self .game .move_forward ()
            elif action =='down':
                self .game .move_backward ()
            elif action =='left':
                self .game .turn_left ()
            elif action =='right':
                self .game .turn_right ()
            elif action =='select':
                self .game .shoot ()


            self .game .update ()


            self .render ()


            current_time =time .time ()
            frame_time =current_time -last_time 
            if frame_time <0.033 :
                time .sleep (0.033 -frame_time )
            last_time =time .time ()

        return None 

    def render (self ):
        """Render the game to display."""
        self .display .clear ((0 ,0 ,0 ))
        draw =self .display .draw 


        draw .rectangle ((0 ,0 ,128 ,50 ),fill =COLOR_CEILING )
        draw .rectangle ((0 ,50 ,128 ,100 ),fill =COLOR_FLOOR )


        for x in range (128 ):
            ray_angle =self .game .player_angle -self .game .fov /2 +(x /128 )*self .game .fov 
            dist ,wall_type ,side =self .game .cast_ray (ray_angle )

            self .z_buffer [x ]=dist 


            if dist >0.1 :
                wall_height =min (int (100 /dist ),100 )
            else :
                wall_height =100 

            wall_top =50 -wall_height //2 
            wall_bottom =50 +wall_height //2 


            colors =WALL_COLORS .get (wall_type ,WALL_COLORS [1 ])
            base_color =colors [side ]


            shade =max (0.2 ,1.0 -dist /15 )
            color =(
            int (base_color [0 ]*shade ),
            int (base_color [1 ]*shade ),
            int (base_color [2 ]*shade )
            )


            draw .line ((x ,wall_top ,x ,wall_bottom ),fill =color )


        self ._render_sprites ()


        self ._draw_weapon ()


        self ._draw_hud ()


        self .display ._render ()

    def _render_sprites (self ):
        """Render enemy sprites."""
        draw =self .display .draw 


        enemies_with_dist =[]
        for enemy in self .game .enemies :
            if enemy .alive :
                dx =enemy .x -self .game .player_x 
                dy =enemy .y -self .game .player_y 
                dist =math .sqrt (dx *dx +dy *dy )
                enemies_with_dist .append ((dist ,enemy ))

        enemies_with_dist .sort (reverse =True )

        for dist ,enemy in enemies_with_dist :

            dx =enemy .x -self .game .player_x 
            dy =enemy .y -self .game .player_y 


            angle =math .atan2 (dy ,dx )-self .game .player_angle 


            while angle >math .pi :
                angle -=2 *math .pi 
            while angle <-math .pi :
                angle +=2 *math .pi 


            if abs (angle )>self .game .fov /2 +0.2 :
                continue 


            screen_x =int (64 +angle *128 /self .game .fov )


            sprite_height =int (60 /dist )if dist >0.5 else 60 
            sprite_width =sprite_height 

            if sprite_height <4 :
                continue 


            half_w =sprite_width //2 
            half_h =sprite_height //2 

            x0 =screen_x -half_w 
            x1 =screen_x +half_w 
            y0 =50 -half_h 
            y1 =50 +half_h 


            for sx in range (max (0 ,x0 ),min (128 ,x1 )):
                if dist <self .z_buffer [sx ]:

                    shade =max (0.3 ,1.0 -dist /12 )
                    color =(int (200 *shade ),int (50 *shade ),int (50 *shade ))
                    draw .line ((sx ,max (0 ,y0 ),sx ,min (100 ,y1 )),fill =color )


            if sprite_width >10 and 0 <=screen_x <128 :
                eye_y =50 -sprite_height //4 
                eye_size =max (1 ,sprite_width //8 )
                left_eye =screen_x -sprite_width //4 
                right_eye =screen_x +sprite_width //4 

                if 0 <=left_eye <128 :
                    draw .ellipse ((left_eye -eye_size ,eye_y -eye_size ,
                    left_eye +eye_size ,eye_y +eye_size ),
                    fill =(255 ,255 ,0 ))
                if 0 <=right_eye <128 :
                    draw .ellipse ((right_eye -eye_size ,eye_y -eye_size ,
                    right_eye +eye_size ,eye_y +eye_size ),
                    fill =(255 ,255 ,0 ))

    def _draw_weapon (self ):
        """Draw weapon/gun sprite."""
        draw =self .display .draw 


        gun_x =50 
        gun_y =85 if not self .game .shooting else 80 


        draw .rectangle ((gun_x ,gun_y ,gun_x +28 ,gun_y +20 ),fill =(80 ,80 ,80 ))
        draw .rectangle ((gun_x +8 ,gun_y -15 ,gun_x +20 ,gun_y ),fill =(60 ,60 ,60 ))


        if self .game .shooting and self .game .shoot_frame >3 :
            draw .ellipse ((gun_x +5 ,gun_y -25 ,gun_x +23 ,gun_y -10 ),
            fill =(255 ,255 ,100 ))
            draw .ellipse ((gun_x +8 ,gun_y -22 ,gun_x +20 ,gun_y -13 ),
            fill =(255 ,200 ,50 ))


        draw .line ((62 ,48 ,66 ,48 ),fill =(0 ,255 ,0 ))
        draw .line ((64 ,46 ,64 ,50 ),fill =(0 ,255 ,0 ))

    def _draw_hud (self ):
        """Draw heads-up display."""
        draw =self .display .draw 


        draw .rectangle ((0 ,100 ,128 ,128 ),fill =(50 ,50 ,50 ))
        draw .line ((0 ,100 ,128 ,100 ),fill =(100 ,100 ,100 ))


        health_color =(0 ,255 ,0 )if self .game .health >50 else (255 ,255 ,0 )if self .game .health >25 else (255 ,0 ,0 )
        draw .text ((4 ,104 ),f"HP:{self .game .health }",font =self .display .font_tiny ,fill =health_color )


        draw .text ((4 ,116 ),f"AM:{self .game .ammo }",font =self .display .font_tiny ,fill =(200 ,200 ,100 ))


        draw .text ((80 ,104 ),f"KILLS",font =self .display .font_tiny ,fill =(200 ,200 ,200 ))
        draw .text ((90 ,116 ),f"{self .game .kills }",font =self .display .font_tiny ,fill =(255 ,100 ,100 ))


        face_x =54 
        face_y =108 

        draw .ellipse ((face_x ,face_y ,face_x +18 ,face_y +18 ),fill =(200 ,150 ,100 ))

        draw .ellipse ((face_x +3 ,face_y +5 ,face_x +7 ,face_y +9 ),fill =(255 ,255 ,255 ))
        draw .ellipse ((face_x +11 ,face_y +5 ,face_x +15 ,face_y +9 ),fill =(255 ,255 ,255 ))
        draw .ellipse ((face_x +4 ,face_y +6 ,face_x +6 ,face_y +8 ),fill =(0 ,0 ,0 ))
        draw .ellipse ((face_x +12 ,face_y +6 ,face_x +14 ,face_y +8 ),fill =(0 ,0 ,0 ))

        if self .game .health >50 :
            draw .arc ((face_x +4 ,face_y +10 ,face_x +14 ,face_y +16 ),0 ,180 ,fill =(100 ,50 ,50 ))
        else :
            draw .line ((face_x +5 ,face_y +13 ,face_x +13 ,face_y +13 ),fill =(100 ,50 ,50 ))


def run_raycaster (display ,input_handler ):
    """
    Run Doom-style raycaster on the Waveshare display.
    Returns the exit key pressed ('key1', 'key2', 'key3') or None.
    """
    renderer =DoomRenderer (display ,input_handler )
    return renderer .start ()



def run_doom (display ,input_handler ):
    return run_raycaster (display ,input_handler )

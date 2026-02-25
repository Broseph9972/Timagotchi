
import os 
import sys 
import importlib .util 
from PIL import Image ,ImageDraw ,ImageFont 
import time 
from font_manager import FontManager 


def _load_lcd_driver ():
    base_dir =os .path .dirname (__file__ )
    legacy_dir =os .path .join (base_dir ,"old code")

    candidates =[]
    if os .path .isdir (legacy_dir ):
        candidates .append (
        (
        os .path .join (legacy_dir ,"config.py"),
        os .path .join (legacy_dir ,"LCD_1in44.py"),
        None ,
        )
        )

    spec_pkg =importlib .util .find_spec ("LCD_1in44")
    if spec_pkg and spec_pkg .origin :
        driver_dir =os .path .dirname (spec_pkg .origin )
        candidates .append ((os .path .join (driver_dir ,"config.py"),spec_pkg .origin ,spec_pkg ))

    load_errors =[]
    for cfg_path ,lcd_path ,spec in candidates :
        if not (os .path .exists (cfg_path )and os .path .exists (lcd_path )):
            continue 

        orig_config =sys .modules .get ("config")
        try :
            spec_cfg =importlib .util .spec_from_file_location ("_lcd_hat_config",cfg_path )
            lcd_hat_config =importlib .util .module_from_spec (spec_cfg )
            spec_cfg .loader .exec_module (lcd_hat_config )
            sys .modules ["config"]=lcd_hat_config 

            spec_lcd =spec or importlib .util .spec_from_file_location ("LCD_1in44",lcd_path )
            if spec_lcd is None or spec_lcd .loader is None :
                load_errors .append (f"Missing loader for {lcd_path }")
                continue 
            lcd_module =importlib .util .module_from_spec (spec_lcd )
            sys .modules ["LCD_1in44"]=lcd_module 
            spec_lcd .loader .exec_module (lcd_module )
            return lcd_module 
        except Exception as exc :
            load_errors .append (f"{lcd_path }: {exc }")
        finally :
            if orig_config is not None :
                sys .modules ["config"]=orig_config 
            else :
                sys .modules .pop ("config",None )

    error_detail ="; ".join (load_errors )if load_errors else "driver files not found"
    raise FileNotFoundError (
    "Could not load Waveshare LCD driver (LCD_1in44). "
    "Re-run install.sh to reinstall the driver or restore the legacy 'old code' folder. "
    f"Details: {error_detail }"
    )


LCD_1in44 =_load_lcd_driver ()

class WaveshareDisplay :
    def __init__ (self ,theme_manager =None ):

        self .disp =LCD_1in44 .LCD ()
        scan_dir =LCD_1in44 .SCAN_DIR_DFT 
        self .disp .LCD_Init (scan_dir )
        self .disp .LCD_Clear ()

        self .width =self .disp .width 
        self .height =self .disp .height 


        self .theme_manager =theme_manager 


        try :
            self ._backlight_level =100 

            self .disp .bl_DutyCycle (self ._backlight_level )
        except Exception :
            self ._backlight_level =None 

        self .image =Image .new ('RGB',(self .width ,self .height ),color =(0 ,0 ,0 ))
        self .draw =ImageDraw .Draw (self .image )


        self .font_manager =FontManager ()


        self ._load_fonts ()


        self .icon_cache ={}
        self ._load_icons ()


        self .faces ={
        "look_r":"( ⚆_⚆)",
        "look_l":"(☉_☉ )",
        "look_r_happy":"( ◕‿◕)",
        "look_l_happy":"(◕‿◕ )",
        "sleep":"(⇀‿‿↼)",
        "sleep2":"(≖‿‿≖)",
        "awake":"(◕‿‿◕)",
        "bored":"(-__-)",
        "intense":"(°▃▃°)",
        "cool":"(⌐■_■)",
        "happy":"(•‿‿•)",
        "excited":"(ᵔ◡◡ᵔ)",
        "grateful":"(^‿‿^)",
        "motivated":"(☼‿‿☼)",
        "demotivated":"(≖__≖)",
        "smart":"(✜‿‿✜)",
        "lonely":"(ب__ب)",
        "sad":"(╥☁╥ )",
        "angry":"(-_-')",
        "friend":"(♥‿‿♥)",
        "broken":"(☓‿‿☓)",
        "debug":"(#__#)",
        "upload":"(1__0)",
        "upload1":"(1__1)",
        "upload2":"(0__1)",
        }

    def _load_icons (self ):
        """Load icons from the Icons folder and cache them."""
        icons_dir =os .path .join (os .path .dirname (__file__ ),'Icons')
        icon_files ={
        'home':'home.png',
        'icon':'Icon.png',
        'settings':'settings.png',
        'grades':'grades.png',
        'textbox':'textbox.png',
        'speechbubble':'speechbubble.png',
        'thoughtbubble':'Thoughtbubble.png'
        }

        for key ,filename in icon_files .items ():
            icon_path =os .path .join (icons_dir ,filename )
            try :
                if os .path .exists (icon_path ):
                    img =Image .open (icon_path )

                    if img .mode !='RGBA':
                        img =img .convert ('RGBA')
                    self .icon_cache [key ]=img 
            except Exception as e :
                pass 

    def _load_fonts (self ):
        """Load fonts using font manager with fallback to defaults"""
        try :

            regular_path =self .font_manager .get_font_path ('regular')
            bold_path =self .font_manager .get_font_path ('bold')


            self .font_large =ImageFont .truetype (bold_path ,16 )
            self .font_medium =ImageFont .truetype (regular_path ,14 )
            self .font_small =ImageFont .truetype (regular_path ,12 )
            self .font_tiny =ImageFont .truetype (regular_path ,10 )
            self .font_micro =ImageFont .truetype (regular_path ,8 )
        except Exception as e :
            print (f"Error loading custom fonts: {e }")

            try :
                self .font_large =ImageFont .truetype ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",16 )
                self .font_medium =ImageFont .truetype ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",14 )
                self .font_small =ImageFont .truetype ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",12 )
                self .font_tiny =ImageFont .truetype ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",10 )
                self .font_micro =ImageFont .truetype ("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",8 )
            except :

                self .font_large =ImageFont .load_default ()
                self .font_medium =ImageFont .load_default ()
                self .font_small =ImageFont .load_default ()
                self .font_tiny =ImageFont .load_default ()
                self .font_micro =ImageFont .load_default ()

    def _measure_text_width (self ,text ,font ):
        try :
            bbox =self .draw .textbbox ((0 ,0 ),text ,font =font )
            return bbox [2 ]-bbox [0 ]
        except Exception :
            try :
                return font .getsize (text )[0 ]
            except Exception :
                return len (text )*6 

    def _wrap_text_to_width (self ,text ,font ,max_width ):
        """Wrap one text line to fit within max_width in pixels."""
        text =(text or "")
        if text =="":
            return [""]

        words =text .split ()
        if not words :
            return [""]

        wrapped =[]
        current =""

        for word in words :
            candidate =f"{current } {word }".strip ()if current else word 
            if self ._measure_text_width (candidate ,font )<=max_width :
                current =candidate 
                continue 

            if current :
                wrapped .append (current )


            if self ._measure_text_width (word ,font )<=max_width :
                current =word 
            else :
                chunk =""
                for ch in word :
                    trial =chunk +ch 
                    if self ._measure_text_width (trial ,font )<=max_width :
                        chunk =trial 
                    else :
                        if chunk :
                            wrapped .append (chunk )
                        chunk =ch 
                current =chunk 

        if current :
            wrapped .append (current )

        return wrapped 

    def reload_fonts (self ):
        """Reload fonts after font selection change"""

        self .font_manager .load_fonts ()

        self ._load_fonts ()

    def _get_icon (self ,icon_name ):
        """Get a cached icon by name."""
        return self .icon_cache .get (icon_name )

    def _get_nav_item_icon_name (self ,nav_item ):
        """Map nav item name to icon name."""
        nav_map ={
        "Main Page":"home",
        "Grades":"grades",
        "Tools":"tools",
        "Settings":"settings"
        }
        return nav_map .get (nav_item ,None )

    def _get_face (self ,name :str ):
        if not name :
            return self .faces .get ("awake","(◕‿‿◕)")
        return self .faces .get (name ,self .faces .get ("awake","(◕‿‿◕)"))

    def _render (self ):
        """Push the PIL image to the LCD."""
        self .disp .LCD_ShowImage (self .image ,0 ,0 )

    def clear (self ,color =(0 ,0 ,0 )):
        self .draw .rectangle ((0 ,0 ,self .width ,self .height ),fill =color )


    SIDEBAR_WIDTH =10 
    PROGRESS_BAR_HEIGHT =8 
    WIFI_BOX_SIZE =0 

    def _render_sidebar (self ,nav_items ,selected_index ):
        """Draw the right-side vertical navigation with letter labels from nav items."""
        if not nav_items or len (nav_items )==0 :
            return 

        bg =self ._get_bg_color ()
        box_fill =self .theme_manager .get_sidebar_box ()if self .theme_manager else (30 ,30 ,30 )
        box_fill_sel =self .theme_manager .get_sidebar_box_selected ()if self .theme_manager else (60 ,60 ,40 )
        indicator_color =self .theme_manager .get_sidebar_indicator ()if self .theme_manager else (255 ,255 ,0 )


        sidebar_x =self .width -self .SIDEBAR_WIDTH 


        self .draw .rectangle ((sidebar_x ,0 ,self .width ,self .height ),fill =bg )


        num_items =min (len (nav_items ),3 )
        chunk_height =(self .height -(num_items -1 ))//num_items 


        labels =[]
        for item in nav_items [:num_items ]:
            label =(str (item ).strip ()[:1 ]or "").upper ()
            labels .append (label )
        while len (labels )<num_items :
            labels .append ("")

        for i in range (num_items ):
            y_start =i *(chunk_height +1 )
            y_end =y_start +chunk_height 


            fill =box_fill_sel if i ==selected_index else box_fill 


            self .draw .rectangle ((sidebar_x ,y_start ,self .width -1 ,y_end -1 ),fill =fill )


            label =labels [i ]if i <len (labels )else ""
            text_color =self ._get_text_primary_color ()


            text_bbox =self .draw .textbbox ((0 ,0 ),label ,font =self .font_small )
            text_width =text_bbox [2 ]-text_bbox [0 ]
            text_height =text_bbox [3 ]-text_bbox [1 ]

            text_x =sidebar_x +(self .SIDEBAR_WIDTH -text_width )//2 
            text_y =y_start +(chunk_height -text_height )//2 

            self .draw .text ((text_x ,text_y ),label ,font =self .font_small ,fill =text_color )


            if i ==selected_index :
                bar_x =sidebar_x -2 
                self .draw .line ((bar_x ,y_start ,bar_x ,y_end -1 ),fill =indicator_color ,width =2 )

    def _render_wifi_indicator (self ,wifi_connected ):
        """Wifi indicator removed - no longer displayed."""
        pass 

    def show_schedule (self ,period ,period_name ,time_remaining ,lunch_time ,end_time ,current_time_str ,nav_items =None ,selected_index =0 ,wifi_connected =False ,minutes_remaining =0 ):
        self .clear (self ._get_bg_color ())

        y_offset =2 
        self .draw .text ((2 ,y_offset ),current_time_str ,font =self .font_medium ,fill =self ._get_accent_color ())
        y_offset +=18 

        if period =="LUNCH":
            self .draw .text ((2 ,y_offset ),"LUNCH",font =self .font_large ,fill =(255 ,200 ,0 ))
            y_offset +=20 
            self .draw .text ((2 ,y_offset ),f"{minutes_remaining }m",font =self .font_small ,fill =(100 ,255 ,100 ))
        elif period =="ADVISORY":
            self .draw .text ((2 ,y_offset ),"ADVISORY",font =self .font_large ,fill =(0 ,255 ,150 ))
            y_offset +=20 
            self .draw .text ((2 ,y_offset ),f"{minutes_remaining }m",font =self .font_small ,fill =(100 ,255 ,100 ))
        elif period =="FREETIME":
            self .draw .text ((2 ,y_offset ),"FREE TIME",font =self .font_medium ,fill =(150 ,255 ,150 ))
            y_offset +=20 
            self .draw .text ((2 ,y_offset ),f"{minutes_remaining }m",font =self .font_small ,fill =(100 ,255 ,100 ))
        elif period is not None :
            self .draw .text ((2 ,y_offset ),f"Period {period }",font =self .font_large ,fill =self ._get_text_primary_color ())
            y_offset +=20 
            self .draw .text ((2 ,y_offset ),f"{minutes_remaining }m",font =self .font_small ,fill =(100 ,255 ,100 ))
            y_offset +=12 
            self .draw .text ((2 ,y_offset ),period_name ,font =self .font_small ,fill =self ._get_text_secondary_color ())
        else :
            self .draw .text ((2 ,y_offset ),"Passing",font =self .font_large ,fill =self ._get_text_secondary_color ())

        y_offset +=25 

        if time_remaining :
            self .draw .text ((2 ,y_offset ),f"Left: {time_remaining }",font =self .font_small ,fill =(100 ,255 ,100 ))
            y_offset +=16 

        if lunch_time :
            self .draw .text ((2 ,y_offset ),f"Lunch: {lunch_time }",font =self .font_small ,fill =(255 ,200 ,100 ))
            y_offset +=16 

        if end_time :
            self .draw .text ((2 ,y_offset ),f"Ends: {end_time }",font =self .font_small ,fill =(255 ,100 ,100 ))


        self ._render_sidebar (nav_items or [],selected_index )
        self ._render_wifi_indicator (wifi_connected )
        self ._render ()

    def show_menu (self ,menu_items ,selected_index ,title ="Menu",progress_label ="",progress_value =0 ,nav_items =None ,nav_selected_index =0 ,start_index =0 ,max_visible =5 ,wifi_connected =False ):
        self .clear (self ._get_bg_color ())


        title_color =self ._get_accent_color ()
        selected_color =(255 ,255 ,0 )
        unselected_color =self ._get_text_secondary_color ()


        content_width =self .width -self .SIDEBAR_WIDTH -4 

        y_offset =4 
        self .draw .text ((4 ,y_offset ),title ,font =self .font_medium ,fill =title_color )
        y_offset +=18 

        visible_items =menu_items [start_index :start_index +max_visible ]
        for i ,item in enumerate (visible_items ):
            absolute_index =start_index +i 

            display_item =item [:14 ]if len (item )>14 else item 
            if absolute_index ==selected_index :
                self .draw .rectangle ((2 ,y_offset -1 ,content_width ,y_offset +13 ),outline =selected_color ,width =1 )
                self .draw .text ((6 ,y_offset ),f">{display_item }",font =self .font_small ,fill =selected_color )
            else :
                self .draw .text ((6 ,y_offset ),f" {display_item }",font =self .font_small ,fill =unselected_color )
            y_offset +=16 


        if start_index >0 :
            self .draw .text ((content_width -10 ,18 ),"^",font =self .font_tiny ,fill =unselected_color )
        if start_index +max_visible <len (menu_items ):
            self .draw .text ((content_width -10 ,y_offset -4 ),"v",font =self .font_tiny ,fill =unselected_color )


        self ._render_sidebar (nav_items or [],nav_selected_index )
        self ._render_wifi_indicator (wifi_connected )
        self ._render ()

    def show_message (self ,title ,message ,color =(255 ,255 ,255 ),nav_items =None ,nav_selected_index =0 ,wifi_connected =False ):
        self .clear (self ._get_bg_color ())

        content_width =self .width -self .SIDEBAR_WIDTH -6 
        title_font =self .font_small 


        self .draw .text ((3 ,4 ),title ,font =title_font ,fill =color if color else self ._get_accent_color ())


        raw_lines =(message or "").split ("\n")
        candidate_fonts =[self .font_tiny ,self .font_micro ]
        top_y =18 
        bottom_margin =2 
        available_height =self .height -top_y -bottom_margin 

        chosen_font =candidate_fonts [-1 ]
        chosen_lines =[]
        chosen_line_height =10 

        for font in candidate_fonts :
            wrapped_lines =[]
            for raw in raw_lines :
                wrapped_lines .extend (self ._wrap_text_to_width (raw ,font ,content_width ))

            line_height =11 if font ==self .font_tiny else 9 
            max_lines =max (1 ,available_height //line_height )
            if len (wrapped_lines )<=max_lines :
                chosen_font =font 
                chosen_lines =wrapped_lines 
                chosen_line_height =line_height 
                break 


            chosen_font =font 
            chosen_lines =wrapped_lines [:max_lines ]
            chosen_line_height =line_height 

        y_offset =top_y 
        for line in chosen_lines :
            self .draw .text ((3 ,y_offset ),line ,font =chosen_font ,fill =self ._get_text_secondary_color ())
            y_offset +=chosen_line_height 


        self ._render_sidebar (nav_items or [],nav_selected_index )
        self ._render_wifi_indicator (wifi_connected )
        self ._render ()

    def show_clock (self ,time_str ,date_str ,nav_items =None ,nav_selected_index =0 ,wifi_connected =False ):
        self .clear (self ._get_bg_color ())

        content_width =self .width -self .SIDEBAR_WIDTH -4 


        self .draw .text ((10 ,40 ),time_str ,font =self .font_large ,fill =self ._get_accent_color ())
        self .draw .text ((10 ,65 ),date_str ,font =self .font_small ,fill =self ._get_text_secondary_color ())


        self ._render_sidebar (nav_items or [],nav_selected_index )
        self ._render_wifi_indicator (wifi_connected )
        self ._render ()

    def show_face_message (self ,title ,message ,face_name ="awake",color =(255 ,255 ,255 ),nav_items =None ,nav_selected_index =0 ,wifi_connected =False ):
        """Display a message with a large ASCII face centered."""
        self .clear (self ._get_bg_color ())


        self .draw .text ((4 ,6 ),title ,font =self .font_medium ,fill =color if color else self ._get_accent_color ())


        face_text =self ._get_face (face_name )
        face_font =self .font_large 
        try :
            bbox =self .draw .textbbox ((0 ,0 ),face_text ,font =face_font )
            face_w =bbox [2 ]-bbox [0 ]
            face_h =bbox [3 ]-bbox [1 ]
        except Exception :
            face_w ,face_h =face_font .getsize (face_text )

        content_width =self .width -self .SIDEBAR_WIDTH -4 
        face_x =(content_width -face_w )//2 
        face_y =28 
        self .draw .text ((face_x ,face_y ),face_text ,font =face_font ,fill =color if color else self ._get_text_primary_color ())


        y_offset =face_y +face_h +6 
        for line in (message or "").split ("\n"):
            self .draw .text ((4 ,y_offset ),line [:18 ],font =self .font_tiny ,fill =self ._get_text_secondary_color ())
            y_offset +=12 


        self ._render_sidebar (nav_items or [],nav_selected_index )
        self ._render_wifi_indicator (wifi_connected )
        self ._render ()

    def show_main_page (self ,progress_label ,progress_value ,time_str ,date_str ,schedule_summary ,wifi_connected ,nav_items ,selected_index ,face_name ="awake",speech_lines =None ):
        """Render the main page with an ASCII face, optional speech lines, progress bar, clock, sidebar, wifi."""
        self .clear (self ._get_bg_color ())

        accent =self ._get_accent_color ()
        secondary =self ._get_text_secondary_color ()
        primary =self ._get_text_primary_color ()

        content_width =self .width -self .SIDEBAR_WIDTH 


        bar_x =0 
        bar_y =0 
        bar_w =content_width 
        bar_h =self .PROGRESS_BAR_HEIGHT 

        progress_bg =self .theme_manager .get_progress_bg ()if self .theme_manager else (40 ,40 ,40 )
        self .draw .rectangle ((bar_x ,bar_y ,bar_x +bar_w ,bar_y +bar_h ),fill =progress_bg )

        if progress_value >0 :
            fill_w =int ((progress_value /100.0 )*bar_w )
            self .draw .rectangle ((bar_x ,bar_y ,bar_x +fill_w ,bar_y +bar_h ),fill =accent )

        self .draw .text ((4 ,bar_h +2 ),progress_label ,font =self .font_tiny ,fill =secondary )



        clock_bottom_y =self .height -(self .WIFI_BOX_SIZE +26 )
        face_text =self ._get_face (face_name )
        face_font =self .font_large 
        try :
            bbox =self .draw .textbbox ((0 ,0 ),face_text ,font =face_font )
            face_w =bbox [2 ]-bbox [0 ]
            face_h =bbox [3 ]-bbox [1 ]
        except Exception :
            face_w ,face_h =face_font .getsize (face_text )

        face_x =6 
        face_y =max (bar_h +12 ,clock_bottom_y -face_h -12 )
        self .draw .text ((face_x ,face_y ),face_text ,font =face_font ,fill =primary )


        speech_lines =speech_lines or []
        if speech_lines :
            line =speech_lines [0 ]


            display_lines =[]
            if len (line )>22 :

                truncated =line [:22 ]
                last_space =truncated .rfind (' ')
                if last_space >0 :
                    display_lines .append (line [:last_space ])
                    display_lines .append (line [last_space +1 :])
                else :
                    display_lines .append (truncated )
                    display_lines .append (line [22 :])
            else :
                display_lines .append (line )


            total_msg_h =0 
            msg_widths =[]
            for text_line in display_lines :
                try :
                    tb =self .draw .textbbox ((0 ,0 ),text_line ,font =self .font_tiny )
                    msg_w =tb [2 ]-tb [0 ]
                    msg_h =tb [3 ]-tb [1 ]
                except Exception :
                    msg_w ,msg_h =self .font_tiny .getsize (text_line )
                msg_widths .append (msg_w )
                total_msg_h +=msg_h +2 

            text_y =max (bar_h +8 ,face_y -total_msg_h -12 )
            content_w =self .width -self .SIDEBAR_WIDTH 


            for idx ,text_line in enumerate (display_lines ):
                text_x =max (0 ,(content_w -msg_widths [idx ])//2 )
                self .draw .text ((text_x ,text_y ),text_line ,font =self .font_tiny ,fill =primary )
                try :
                    tb =self .draw .textbbox ((0 ,0 ),text_line ,font =self .font_tiny )
                    line_h =tb [3 ]-tb [1 ]
                except Exception :
                    line_h =self .font_tiny .getsize (text_line )[1 ]
                text_y +=line_h +2 


            arrow ="<┛"
            try :
                ab =self .draw .textbbox ((0 ,0 ),arrow ,font =self .font_tiny )
                arrow_h =ab [3 ]-ab [1 ]
            except Exception :
                arrow_h =self .font_tiny .getsize (arrow )[1 ]
            arrow_x =face_x +face_w +2 
            arrow_y =face_y +max (0 ,(face_h -arrow_h )//2 )
            self .draw .text ((arrow_x ,arrow_y ),arrow ,font =self .font_tiny ,fill =primary )



        bottom_y =self .height -(self .WIFI_BOX_SIZE +26 )
        self .draw .text ((4 ,bottom_y -2 ),time_str ,font =self .font_small ,fill =accent )
        self .draw .text ((4 ,bottom_y +10 ),date_str ,font =self .font_tiny ,fill =secondary )


        self ._render_sidebar (nav_items or [],selected_index )


        self ._render_wifi_indicator (wifi_connected )

        self ._render ()

    def show_grades_menu (self ,menu_items ,selected_index ,title ="Grades",nav_items =None ,nav_selected_index =0 ,start_index =0 ,max_visible =5 ,wifi_connected =False ):
        """Display grades menu with menu items."""
        self .clear (self ._get_bg_color ())


        title_color =self ._get_accent_color ()
        selected_color =(255 ,255 ,0 )
        unselected_color =self ._get_text_secondary_color ()


        content_width =self .width -self .SIDEBAR_WIDTH -4 

        y_offset =4 
        self .draw .text ((4 ,y_offset ),title ,font =self .font_medium ,fill =title_color )
        y_offset +=18 

        visible_items =menu_items [start_index :start_index +max_visible ]
        for i ,item in enumerate (visible_items ):
            absolute_index =start_index +i 

            display_item =item [:14 ]if len (item )>14 else item 
            if absolute_index ==selected_index :
                self .draw .rectangle ((2 ,y_offset -1 ,content_width ,y_offset +13 ),outline =selected_color ,width =1 )
                self .draw .text ((6 ,y_offset ),f">{display_item }",font =self .font_small ,fill =selected_color )
            else :
                self .draw .text ((6 ,y_offset ),f" {display_item }",font =self .font_small ,fill =unselected_color )
            y_offset +=16 


        if start_index >0 :
            self .draw .text ((content_width -10 ,18 ),"^",font =self .font_tiny ,fill =unselected_color )
        if start_index +max_visible <len (menu_items ):
            self .draw .text ((content_width -10 ,y_offset -4 ),"v",font =self .font_tiny ,fill =unselected_color )


        self ._render_sidebar (nav_items or [],nav_selected_index )
        self ._render_wifi_indicator (wifi_connected )
        self ._render ()


    def _get_bg_color (self ):
        """Get background color from theme"""
        if self .theme_manager :
            return self .theme_manager .get_background ()
        return (0 ,0 ,0 )

    def _get_text_primary_color (self ):
        """Get primary text color from theme"""
        if self .theme_manager :
            return self .theme_manager .get_text_primary ()
        return (255 ,255 ,255 )

    def _get_text_secondary_color (self ):
        """Get secondary text color from theme"""
        if self .theme_manager :
            return self .theme_manager .get_text_secondary ()
        return (200 ,200 ,200 )

    def _get_accent_color (self ):
        """Get accent color from theme"""
        if self .theme_manager :
            return self .theme_manager .get_text_accent ()
        return (100 ,200 ,255 )


    def set_backlight (self ,level :int ):
        """Set backlight brightness percentage (0-100)."""
        try :
            level =max (0 ,min (100 ,int (level )))
            self .disp .bl_DutyCycle (level )
            self ._backlight_level =level 
        except Exception :
            pass 

    def get_backlight (self ):
        """Return last set backlight percentage or None if unknown."""
        return self ._backlight_level 

    def restore_backlight (self ,fallback :int =100 ):
        """Restore backlight to previous level or fallback."""
        if self ._backlight_level is None :
            self .set_backlight (fallback )
        else :

            self .set_backlight (self ._backlight_level )

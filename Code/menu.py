import datetime 
import random 
import subprocess 
import time 
import json 
import os 
import sys 
import threading 
from config_loader import (
PERIODS ,SCHOOL_START ,SCHOOL_END ,LUNCH_START ,LUNCH_END ,
PERIOD_LENGTH ,PASSING_TIME ,A_DAY_PERIODS ,B_DAY_PERIODS ,
freetimedaus ,USE_24_HOUR ,
AB_DAY_MODE ,MANUAL_AB_DAY ,abday ,PROGRESS_BAR_MODE ,
ADVISORY_START ,ADVISORY_PERIOD ,advisory ,advisorylength ,advisorydays ,
WIFI_NETWORKS 
)
from input_handler import InputHandler 
from theme_manager import ThemeManager 
from font_manager import FontManager 
import json as _json 
import requests 
from urllib .parse import urljoin 
from games_config import get_game_command 


try :
    from config_loader import DAY_PRESETS ,NUM_DAY_PRESETS 
except ImportError :

    DAY_PRESETS ={"A":A_DAY_PERIODS ,"B":B_DAY_PERIODS }
    NUM_DAY_PRESETS =2 

class Menu :
    def __init__ (self ,display ,input_handler ):
        self .display =display 
        self .input_handler =input_handler 
        self .current_screen ="main"
        self .selected_index =0 
        self .running =True 


        self .theme_manager =ThemeManager ()


        self .font_manager =FontManager ()


        self .nav_items =["Main Page","Tools","Settings"]
        self .nav_selected_index =0 



        self ._wifi_state =False 
        self ._wifi_checked_at =0.0 

        try :
            result =subprocess .run (['nmcli','-t','-f','STATE','g'],capture_output =True ,text =True ,timeout =1 )
            state =result .stdout .strip ().lower ()
            self ._wifi_state ='connected'in state 
        except Exception :
            pass 
        finally :
            self ._wifi_checked_at =time .time ()

        self .settings_menu_items =[]
        if abday .lower ()=="true":

            if NUM_DAY_PRESETS >2 :
                self .settings_menu_items .append ("Day Presets")
            else :
                self .settings_menu_items .append ("A/B Day")
        self .settings_menu_items .extend (["WiFi","Appearance","Brightness","Progress Bar","Set Time","Developer","Version","Update","Restart"])
        self .settings_scroll_offset =0 
        self .tools_menu_items =["Grades","Stopwatch","Developer"]
        self .tools_scroll_offset =0 
        self .set_time_menu_items =["Manual Set","Sync Now"]
        self .appearance_menu_items =["Colors","Fonts"]
        self .version_menu_items =["Recent Changes","Switch to Stable","Switch to Beta"]
        self .theme_menu_items =self .theme_manager .get_theme_names ()
        self .theme_scroll_offset =0 
        self .font_menu_items =self .font_manager .get_font_names ()
        self .font_scroll_offset =0 
        self .adjust_hour =0 
        self .adjust_minute =0 
        self .ab_day_mode =AB_DAY_MODE 
        self .manual_ab_day =MANUAL_AB_DAY 
        self .last_sync_error =None 
        self .progress_bar_modes =["time_in_class","time_in_day","lunch_day"]
        self .progress_bar_mode =PROGRESS_BAR_MODE 
        self .progress_bar_mode_index =self .progress_bar_modes .index (self .progress_bar_mode )if self .progress_bar_mode in self .progress_bar_modes else 0 


        self .state_path =os .path .join (os .path .dirname (__file__ ),'schedule_state.json')
        self .presets_count =NUM_DAY_PRESETS 
        self .current_preset_index =0 
        self .last_advance_date =None 

        try :
            self .backlight =int (self .display .get_backlight ()or 100 )
        except Exception :
            self .backlight =100 
        self ._load_state ()

        try :
            self .display .set_backlight (int (max (0 ,min (100 ,self .backlight ))))
        except Exception :
            pass 

        self .power_saver_enabled =getattr (self ,'power_saver_enabled',False )
        self .power_saver_timeout =getattr (self ,'power_saver_timeout',45 )
        self .power_saver_dim =getattr (self ,'power_saver_dim',5 )
        self ._power_saver_active =False 
        self ._prev_backlight_before_ps =self .backlight 
        self ._last_input_time =time .time ()
        self ._advance_preset_if_new_day ()

        self .canvas_config_path =os .path .join (os .path .dirname (__file__ ),'canvas_config.json')
        self .canvas_cache_path =os .path .join (os .path .dirname (__file__ ),'canvas_cache.json')

        try :
            if os .path .exists (self .canvas_cache_path ):
                os .remove (self .canvas_cache_path )
        except Exception :
            pass 
        self .current_course_id =None 
        self .grades_selected_index =0 
        self .assign_selected_index =0 
        self .assign_scroll_offset =0 
        self .grades_scroll_offset =0 

        self .stopwatch_running =False 
        self .stopwatch_start_ts =0.0 
        self .stopwatch_elapsed =0.0 


        self .wifi_password =""
        self .wifi_password_ssid =""
        self .wifi_keyboard_chars ="abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()"
        self .wifi_keyboard_index =0 


        self .phrases =self ._load_phrases ()

        self ._konami_code =['up','up','down','down','left','right','left','right']
        self ._konami_index =0 
        self .secret_menu_items =["Start Tetris","Doom","Shitty Doom","Run Custom Script"]

    def _load_phrases (self ):
        """Load phrases from Phrases.json file."""
        default_phrases ={
        "passing":[],
        "advisory":[],
        "lunch":[],
        "period1":[],
        "period2":[],
        "period3":[],
        "period4":[],
        "period5":[],
        "period6":[],
        "period7":[],
        "period8":[]
        }
        try :
            phrases_path =os .path .join (os .path .dirname (__file__ ),'Phrases.json')
            if os .path .exists (phrases_path ):
                with open (phrases_path ,'r')as f :
                    return json .load (f )
        except Exception :
            pass 

        return default_phrases 

    def is_freetime_day (self ):
        today =datetime .datetime .now ().strftime ('%a').lower ()
        return today [0 ]in freetimedaus .lower ().split (',')

    def get_current_ab_day (self ):
        """Return 'a' or 'b' based on preset index when presets_count==2; otherwise 'a'."""
        if self .presets_count ==2 :
            return 'a'if self .current_preset_index ==0 else 'b'
        return 'a'

    def _load_state (self ):
        try :
            if os .path .exists (self .state_path ):
                with open (self .state_path ,'r')as f :
                    data =json .load (f )
                self .presets_count =int (data .get ('presets_count',2 ))
                self .current_preset_index =int (data .get ('current_preset_index',0 ))
                self .last_advance_date =data .get ('last_advance_date')

                bl =data .get ('backlight')
                if bl is not None :
                    try :
                        self .backlight =int (bl )
                    except Exception :
                        pass 

                self .power_saver_enabled =bool (data .get ('power_saver_enabled',False ))
                self .power_saver_timeout =int (data .get ('power_saver_timeout',45 ))
                self .power_saver_dim =int (data .get ('power_saver_dim',5 ))
        except Exception :
            pass 

    def _save_state (self ):
        try :
            data ={
            'presets_count':self .presets_count ,
            'current_preset_index':self .current_preset_index ,
            'last_advance_date':self .last_advance_date ,
            'backlight':int (self .backlight )if hasattr (self ,'backlight')else 100 ,
            'power_saver_enabled':bool (getattr (self ,'power_saver_enabled',False )),
            'power_saver_timeout':int (getattr (self ,'power_saver_timeout',45 )),
            'power_saver_dim':int (getattr (self ,'power_saver_dim',5 )),
            }
            with open (self .state_path ,'w')as f :
                json .dump (data ,f )
        except Exception :
            pass 

    def _advance_preset_if_new_day (self ):
        """Auto-advance preset once per calendar day when presets_count==2."""
        try :
            today_str =datetime .date .today ().isoformat ()
            if self .presets_count ==2 :
                if self .last_advance_date !=today_str :

                    self .current_preset_index =(self .current_preset_index +1 )%2 
                    self .last_advance_date =today_str 
                    self ._save_state ()
            else :

                if self .current_preset_index !=0 :
                    self .current_preset_index =0 
                    self ._save_state ()
        except Exception :
            pass 

    def get_current_period (self ,current_time ):
        """
        Determine current period. Now handles PERIODS dict with special string keys:
        - 'advisory': Advisory/homeroom period
        - 'lunch': Lunch period  
        - 1, 2, 3, etc.: Regular numbered class periods
        
        Returns: (period_identifier, time_remaining, is_lunch)
        """

        if 'advisory'in PERIODS and advisory .lower ()=="true":

            weekday_abbr ={0 :'m',1 :'t',2 :'w',3 :'th',4 :'f',5 :'sat',6 :'sun'}
            today_abbr =weekday_abbr .get (datetime .date .today ().weekday (),'')
            advisory_day_list =[d .strip ()for d in advisorydays .split (',')]

            if today_abbr in advisory_day_list :
                advisory_start =datetime .datetime .strptime (PERIODS ['advisory'],"%H:%M").time ()
                advisory_start_dt =datetime .datetime .combine (datetime .date .today (),advisory_start )
                advisory_len =int (advisorylength )
                advisory_end =advisory_start_dt +datetime .timedelta (minutes =advisory_len )

                if advisory_start_dt <=current_time <advisory_end :
                    time_remaining =advisory_end -current_time 
                    return "ADVISORY",time_remaining ,False 


        lunch_start =datetime .datetime .strptime (LUNCH_START ,"%H:%M").time ()
        lunch_start_dt =datetime .datetime .combine (datetime .date .today (),lunch_start )
        lunch_end =datetime .datetime .strptime (LUNCH_END ,"%H:%M").time ()
        lunch_end_dt =datetime .datetime .combine (datetime .date .today (),lunch_end )

        if lunch_start_dt <=current_time <lunch_end_dt :
            time_remaining =lunch_end_dt -current_time 
            return "LUNCH",time_remaining ,True 


        numbered_periods =sorted ([p for p in PERIODS .keys ()if isinstance (p ,int )])

        for i ,period in enumerate (numbered_periods ):
            period_start_time =datetime .datetime .strptime (PERIODS [period ],"%H:%M").time ()
            period_start =datetime .datetime .combine (datetime .date .today (),period_start_time )

            if i +1 <len (numbered_periods ):
                next_period =numbered_periods [i +1 ]
                next_period_time =datetime .datetime .strptime (PERIODS [next_period ],"%H:%M").time ()
                next_period_start =datetime .datetime .combine (datetime .date .today (),next_period_time )
                # Cap at class time + passing to avoid spanning across lunch
                max_end =period_start +datetime .timedelta (minutes =PERIOD_LENGTH +PASSING_TIME )
                period_end =min (next_period_start ,max_end )
            else :
                period_end =period_start +datetime .timedelta (minutes =PERIOD_LENGTH )


            if period_start <=current_time <period_end :
                time_remaining =period_end -current_time 
                return period ,time_remaining ,False 

        return None ,None ,False 

    def get_time_until (self ,target_time ,current_time ):
        target =datetime .datetime .strptime (target_time ,"%H:%M").time ()
        target =datetime .datetime .combine (datetime .date .today (),target )
        if target <current_time :
            return None 
        return target -current_time 

    def format_timedelta (self ,td ):
        if td is None :
            return "N/A"
        total_seconds =int (td .total_seconds ())
        hours =total_seconds //3600 
        minutes =(total_seconds %3600 )//60 
        if hours >0 :
            return f"{hours }h {minutes }m"
        else :
            return f"{minutes }m"

    def get_next_period (self ,current_time ):
        """Get the next period after current time. Returns (period_num, period_name, time_until) or (None, None, None)"""

        numbered_periods =sorted ([p for p in PERIODS .keys ()if isinstance (p ,int )])

        for period in numbered_periods :
            period_start_time =datetime .datetime .strptime (PERIODS [period ],"%H:%M").time ()
            period_start =datetime .datetime .combine (datetime .date .today (),period_start_time )

            if period_start >current_time :

                time_until =period_start -current_time 


                if abday .lower ()=="true":
                    preset_key =list (DAY_PRESETS .keys ())[self .current_preset_index %len (DAY_PRESETS )]
                    current_preset =DAY_PRESETS .get (preset_key ,{})
                    period_name =current_preset .get (period ,f"Period {period }")
                else :
                    period_name =A_DAY_PERIODS .get (period ,f"Period {period }")

                return period ,period_name ,time_until 

        return None ,None ,None 

    def show_schedule_screen (self ):
        current_time =datetime .datetime .now ()
        period ,time_remaining ,is_lunch =self .get_current_period (current_time )
        wifi_connected =self ._get_wifi_connected ()

        school_start =datetime .datetime .strptime (SCHOOL_START ,"%H:%M").time ()
        school_start =datetime .datetime .combine (datetime .date .today (),school_start )
        school_end =datetime .datetime .strptime (SCHOOL_END ,"%H:%M").time ()
        school_end =datetime .datetime .combine (datetime .date .today (),school_end )

        if USE_24_HOUR :
            current_time_str =current_time .strftime ("%H:%M")
        else :
            current_time_str =current_time .strftime ("%I:%M %p")

        if current_time <school_start :
            time_until_start =self .get_time_until (SCHOOL_START ,current_time )
            time_until_str =self .format_timedelta (time_until_start )
            self .display .show_message ("School Hasn't Started",f"Starts in {time_until_str }\nSchool @ {SCHOOL_START }",(200 ,200 ,200 ),self .nav_items ,self .nav_selected_index ,wifi_connected )
            return 
        elif current_time >school_end :
            self .display .show_message ("After School","School day has ended",(200 ,200 ,200 ),self .nav_items ,self .nav_selected_index ,wifi_connected )
            return 

        period_name =""
        if period =="ADVISORY":
            period_name ="Advisory"
        elif period =="LUNCH":
            period_name ="Lunch"
        elif period is not None and isinstance (period ,int ):

            preset_key =list (DAY_PRESETS .keys ())[self .current_preset_index %len (DAY_PRESETS )]
            current_preset =DAY_PRESETS .get (preset_key ,{})
            period_name =current_preset .get (period ,f"Period {period }")

        lunch_time_str =None 
        lunch_start_dt =datetime .datetime .strptime (LUNCH_START ,"%H:%M").time ()
        lunch_start_dt =datetime .datetime .combine (datetime .date .today (),lunch_start_dt )
        if current_time <lunch_start_dt :
            time_until_lunch =self .get_time_until (LUNCH_START ,current_time )
            lunch_time_str =self .format_timedelta (time_until_lunch )

        end_time_str =None 
        if current_time <school_end :
            time_until_end =self .get_time_until (SCHOOL_END ,current_time )
            end_time_str =self .format_timedelta (time_until_end )

        time_remaining_str =self .format_timedelta (time_remaining )if time_remaining else None 


        minutes_remaining =0 
        if time_remaining :
            minutes_remaining =int (time_remaining .total_seconds ()//60 )

        self .display .show_schedule (period ,period_name ,time_remaining_str ,lunch_time_str ,end_time_str ,current_time_str ,self .nav_items ,self .nav_selected_index ,wifi_connected ,minutes_remaining )

    def show_clock_screen (self ):
        now =datetime .datetime .now ()
        wifi_connected =self ._get_wifi_connected ()
        if USE_24_HOUR :
            time_str =now .strftime ("%H:%M:%S")
        else :
            time_str =now .strftime ("%I:%M:%S %p")
        date_str =now .strftime ("%A, %B %d")
        self .display .show_clock (time_str ,date_str ,self .nav_items ,self .nav_selected_index ,wifi_connected )

    def _get_wifi_connected (self ):
        """Return cached WiFi state.

        This only queries nmcli at most once every 10 seconds to avoid
        blocking the input loop. The cached state is also updated on boot
        (initial check) and immediately after a successful connection.
        """
        now =time .time ()

        if now -self ._wifi_checked_at <10 :
            return self ._wifi_state 

        try :

            result =subprocess .run (
            ['nmcli','-t','-f','STATE','g'],
            capture_output =True ,
            text =True ,
            timeout =0.5 
            )
            state =result .stdout .strip ().lower ()
            self ._wifi_state ='connected'in state 
            self ._wifi_checked_at =now 
        except subprocess .TimeoutExpired :

            self ._wifi_checked_at =now 
        except Exception :

            self ._wifi_checked_at =now 
        return self ._wifi_state 

    def _get_schedule_summary (self ):
        now =datetime .datetime .now ()

        try :
            lunch_start_dt =datetime .datetime .combine (
            datetime .date .today (),datetime .datetime .strptime (LUNCH_START ,"%H:%M").time ()
            )
            lunch_end_dt =datetime .datetime .combine (
            datetime .date .today (),datetime .datetime .strptime (LUNCH_END ,"%H:%M").time ()
            )
            if lunch_start_dt <=now <lunch_end_dt :
                return "Lunch"
        except Exception :
            pass 
        period ,time_remaining ,is_lunch =self .get_current_period (now )
        if period =="LUNCH":
            return "Lunch"
        if period =="ADVISORY":
            return "Advisory"
        if period is None :

            next_period ,next_name ,time_until =self .get_next_period (now )
            if next_period is not None :
                return f"Passing • Next: {next_name }"
            return "Passing"

        if isinstance (period ,int ):
            if abday .lower ()=="true":

                preset_key =list (DAY_PRESETS .keys ())[self .current_preset_index %len (DAY_PRESETS )]
                current_preset =DAY_PRESETS .get (preset_key ,{})
                name =current_preset .get (period ,f"Period {period }")
            else :
                name =A_DAY_PERIODS .get (period ,f"Period {period }")
            rem =self .format_timedelta (time_remaining )if time_remaining else ""
            return f"{name } • {rem }"
        return ""

    def show_main_menu (self ):
        label ,progress =self .get_progress_bar ()
        now =datetime .datetime .now ()
        time_str =now .strftime ("%H:%M")if USE_24_HOUR else now .strftime ("%I:%M %p")
        date_str =now .strftime ("%a %b %d")
        schedule_summary =self ._get_schedule_summary ()
        wifi_connected =self ._get_wifi_connected ()

        face_name ="awake"
        summary_lower =(schedule_summary or "").lower ()
        speech_lines =[]
        if "lunch"in summary_lower :
            face_name ="happy"
        elif "passing"in summary_lower :

            try :

                tick =int ((now .timestamp ()*2 )%2 )
            except Exception :
                tick =0 
            face_name ="look_r_happy"if tick ==0 else "look_l_happy"
        elif "advisory"in summary_lower :
            face_name ="smart"
        elif not schedule_summary :
            face_name ="bored"


        period ,time_remaining ,is_lunch =self .get_current_period (now )
        phrase_key =None 

        if "passing"in summary_lower :
            phrase_key ="passing"
        elif period =="ADVISORY":
            phrase_key ="advisory"
        elif period =="LUNCH":
            phrase_key ="lunch"
        elif isinstance (period ,int ):
            phrase_key =f"period{period }"


        if phrase_key :
            period_phrases =self .phrases .get (phrase_key ,[])
            if period_phrases :
                bucket =int (now .timestamp ()//300 )
                rng =random .Random (bucket )
                speech_lines =[rng .choice (period_phrases )]

        self .display .show_main_page (label ,progress ,time_str ,date_str ,None ,wifi_connected ,self .nav_items ,self .nav_selected_index ,face_name ,speech_lines )

    def get_progress_bar (self ):
        """Calculate progress bar based on current mode."""
        try :
            now =datetime .datetime .now ()

            def _minutes_left_label (label ,end_dt ):
                seconds_left =max (0 ,int ((end_dt -now ).total_seconds ()))
                minutes_left =(seconds_left +59 )//60 
                return f"{label }: {minutes_left } min left"


            school_start_dt =datetime .datetime .combine (
            datetime .date .today (),datetime .datetime .strptime (SCHOOL_START ,"%H:%M").time ()
            )
            school_end_dt =datetime .datetime .combine (
            datetime .date .today (),datetime .datetime .strptime (SCHOOL_END ,"%H:%M").time ()
            )
            lunch_start_dt =datetime .datetime .combine (
            datetime .date .today (),datetime .datetime .strptime (LUNCH_START ,"%H:%M").time ()
            )
            lunch_end_dt =datetime .datetime .combine (
            datetime .date .today (),datetime .datetime .strptime (LUNCH_END ,"%H:%M").time ()
            )


            actual_school_end =school_end_dt 
            if PERIODS :

                numbered_periods =[p for p in PERIODS .keys ()if isinstance (p ,int )]
                if numbered_periods :
                    last_period =max (numbered_periods )
                    last_start_dt =datetime .datetime .combine (
                    datetime .date .today (),datetime .datetime .strptime (PERIODS [last_period ],"%H:%M").time ()
                    )
                    actual_school_end =last_start_dt +datetime .timedelta (minutes =PERIOD_LENGTH )

            mode =self .progress_bar_modes [self .progress_bar_mode_index ]
            if mode =="time_in_class":

                if lunch_start_dt <=now <lunch_end_dt :
                    elapsed =(now -lunch_start_dt ).total_seconds ()
                    total =(lunch_end_dt -lunch_start_dt ).total_seconds ()
                    progress =int ((elapsed /total )*100 )if total >0 else 0 
                    return _minutes_left_label ("Lunch",lunch_end_dt ),progress 


                numbered_periods =sorted ([p for p in PERIODS .keys ()if isinstance (p ,int )])
                for i ,p in enumerate (numbered_periods ):
                    start_dt =datetime .datetime .combine (
                    datetime .date .today (),datetime .datetime .strptime (PERIODS [p ],"%H:%M").time ()
                    )

                    if i +1 <len (numbered_periods ):
                        next_start_dt =datetime .datetime .combine (
                        datetime .date .today (),datetime .datetime .strptime (PERIODS [numbered_periods [i +1 ]],"%H:%M").time ()
                        )
                        end_dt =min (start_dt +datetime .timedelta (minutes =PERIOD_LENGTH ),next_start_dt )
                    else :
                        end_dt =start_dt +datetime .timedelta (minutes =PERIOD_LENGTH )

                    if start_dt <=now <end_dt :
                        elapsed =(now -start_dt ).total_seconds ()

                        overlap_start =max (start_dt ,lunch_start_dt )
                        overlap_end =min (now ,lunch_end_dt )
                        if overlap_start <overlap_end :
                            elapsed -=(overlap_end -overlap_start ).total_seconds ()
                            if elapsed <0 :
                                elapsed =0 

                        total =(end_dt -start_dt ).total_seconds ()
                        progress =int ((elapsed /total )*100 )if total >0 else 0 
                        if progress <0 :
                            progress =0 
                        if progress >100 :
                            progress =100 

                        preset_key =list (DAY_PRESETS .keys ())[self .current_preset_index %len (DAY_PRESETS )]
                        current_preset =DAY_PRESETS .get (preset_key ,{})
                        class_name =current_preset .get (p ,f"Period {p }")
                        return _minutes_left_label (class_name ,end_dt ),progress 


                if 'advisory'in PERIODS and advisory .lower ()=="true":
                    advisory_start_dt =datetime .datetime .combine (
                    datetime .date .today (),datetime .datetime .strptime (PERIODS ['advisory'],"%H:%M").time ()
                    )
                    advisory_end_dt =advisory_start_dt +datetime .timedelta (minutes =int (advisorylength ))
                    if advisory_start_dt <=now <advisory_end_dt :
                        elapsed =(now -advisory_start_dt ).total_seconds ()
                        total =(advisory_end_dt -advisory_start_dt ).total_seconds ()
                        progress =int ((elapsed /total )*100 )if total >0 else 0 
                        return _minutes_left_label ("Advisory",advisory_end_dt ),progress 


                if now <school_start_dt :
                    return "Before school",0 


                if numbered_periods :
                    last_start_dt =datetime .datetime .combine (
                    datetime .date .today (),datetime .datetime .strptime (PERIODS [numbered_periods [-1 ]],"%H:%M").time ()
                    )
                    actual_class_end =last_start_dt +datetime .timedelta (minutes =PERIOD_LENGTH )
                else :
                    actual_class_end =school_end_dt 

                if now >=actual_class_end :
                    return "After school",100 


                for i in range (len (numbered_periods )-1 ):
                    p_curr =numbered_periods [i ]
                    p_next =numbered_periods [i +1 ]
                    curr_start =datetime .datetime .combine (
                    datetime .date .today (),datetime .datetime .strptime (PERIODS [p_curr ],"%H:%M").time ()
                    )
                    curr_end =curr_start +datetime .timedelta (minutes =PERIOD_LENGTH )
                    next_start =datetime .datetime .combine (
                    datetime .date .today (),datetime .datetime .strptime (PERIODS [p_next ],"%H:%M").time ()
                    )

                    passing_end =min (next_start ,curr_end +datetime .timedelta (minutes =PASSING_TIME ))
                    if curr_end <=now <passing_end :
                        return "Passing",0 


                return "Passing",0 

            if mode =="time_in_day":
                if now <school_start_dt :
                    return "Before school",0 
                if now >=actual_school_end :
                    return "After school",100 
                elapsed =(now -school_start_dt ).total_seconds ()
                total =(actual_school_end -school_start_dt ).total_seconds ()
                progress =int ((elapsed /total )*100 )if total >0 else 0 
                return _minutes_left_label ("Day",actual_school_end ),progress 

            if mode =="lunch_day":
                if now <lunch_start_dt :
                    elapsed =(now -school_start_dt ).total_seconds ()
                    total =(lunch_start_dt -school_start_dt ).total_seconds ()
                    progress =int ((elapsed /total )*100 )if total >0 else 0 
                    return _minutes_left_label ("Until Lunch",lunch_start_dt ),progress 
                if now <lunch_end_dt :
                    elapsed =(now -lunch_start_dt ).total_seconds ()
                    total =(lunch_end_dt -lunch_start_dt ).total_seconds ()
                    progress =int ((elapsed /total )*100 )if total >0 else 0 
                    return _minutes_left_label ("Lunch",lunch_end_dt ),progress 
                if now >=actual_school_end :
                    return "After school",100 
                elapsed =(now -lunch_end_dt ).total_seconds ()
                total =(actual_school_end -lunch_end_dt ).total_seconds ()
                progress =int ((elapsed /total )*100 )if total >0 else 0 
                return _minutes_left_label ("Day Left",actual_school_end ),progress 

            return "Unknown",0 
        except Exception :
            return "Error",0 

    def show_settings_menu (self ):

        max_visible =6 
        wifi_connected =self ._get_wifi_connected ()
        if self .selected_index <self .settings_scroll_offset :
            self .settings_scroll_offset =self .selected_index 
        elif self .selected_index >=self .settings_scroll_offset +max_visible :
            self .settings_scroll_offset =self .selected_index -max_visible +1 
        self .display .show_menu (self .settings_menu_items ,self .selected_index ,"Settings",nav_items =self .nav_items ,nav_selected_index =self .nav_selected_index ,start_index =self .settings_scroll_offset ,max_visible =max_visible ,wifi_connected =wifi_connected )

    def show_tools_menu (self ):

        max_visible =6 
        wifi_connected =self ._get_wifi_connected ()
        if self .selected_index <self .tools_scroll_offset :
            self .tools_scroll_offset =self .selected_index 
        elif self .selected_index >=self .tools_scroll_offset +max_visible :
            self .tools_scroll_offset =self .selected_index -max_visible +1 
        self .display .show_menu (self .tools_menu_items ,self .selected_index ,"Tools",nav_items =self .nav_items ,nav_selected_index =self .nav_selected_index ,start_index =self .tools_scroll_offset ,max_visible =max_visible ,wifi_connected =wifi_connected )

    def _show_presets_menu (self ):
        msg =f"Presets: {self .presets_count }\nUp/Down: 1 or 2\nSelect: Save"
        wifi_connected =self ._get_wifi_connected ()
        self .display .show_message ("Schedule Presets",msg ,(150 ,200 ,255 ),self .nav_items ,self .nav_selected_index ,wifi_connected )

    def _handle_presets_input (self ,action ):
        if action =='up':
            self .presets_count =1 
            self ._show_presets_menu ()
        elif action =='down':
            self .presets_count =2 
            self ._show_presets_menu ()
        elif action in ('select','right','left'):
            if self .presets_count ==1 :
                self .current_preset_index =0 
            self ._save_state ()
            self .current_screen ='settings'
            self .selected_index =self .settings_menu_items .index ("Schedule Presets")
            self .show_settings_menu ()
    def _show_set_today_preset (self ):
        label ='A'if self .current_preset_index ==0 else 'B'
        msg =f"Today Preset: {label }\nUp/Down: Toggle\nSelect: Set & Auto-advance daily"
        wifi_connected =self ._get_wifi_connected ()
        self .display .show_message ("Set Today",msg ,(150 ,255 ,200 ),self .nav_items ,self .nav_selected_index ,wifi_connected )

    def _handle_set_today_input (self ,action ):
        if action in ('up','down'):

            self .current_preset_index =0 if self .current_preset_index ==1 else 1 
            self ._show_set_today_preset ()
        elif action in ('select','right','left'):

            self .last_advance_date =datetime .date .today ().isoformat ()
            self ._save_state ()
            self .current_screen ='settings'
            self .selected_index =self .settings_menu_items .index ("Set Today Preset")
            self .show_settings_menu ()

    def show_wifi_menu (self ):
        """Show WiFi networks available with color-coding for known/open vs unknown/secured."""
        wifi_connected =self ._get_wifi_connected ()
        message ="Scanning WiFi...\nPlease wait."
        self .display .show_message ("WiFi",message ,(100 ,200 ,255 ),self .nav_items ,self .nav_selected_index ,wifi_connected )


        known_networks ={ssid for ssid ,pwd in WIFI_NETWORKS }


        try :
            result =subprocess .run (
            ['nmcli','-t','-f','SSID,SIGNAL,SECURITY','device','wifi','list'],
            capture_output =True ,
            text =True ,
            timeout =5 
            )
            lines =[l for l in result .stdout .strip ().split ('\n')if l .strip ()]

            self .wifi_networks =[]
            for line in lines :


                parts =line .rsplit (':',2 )
                if len (parts )==3 :
                    ssid ,signal ,security =parts 
                elif len (parts )==2 :
                    ssid =parts [0 ]
                    signal =parts [1 ]
                    security =""
                else :
                    continue 

                ssid =ssid if ssid else "<hidden>"
                security =security if security else ""


                is_known =ssid in known_networks 
                is_open =security ==""


                if is_known or is_open :
                    color ="green"
                else :
                    color ="red"

                self .wifi_networks .append ((ssid ,signal ,security ,color ))

            if not self .wifi_networks :
                self .display .show_message ("WiFi","No networks found.\nMake sure WiFi is enabled.",(200 ,100 ,100 ),self .nav_items ,self .nav_selected_index ,wifi_connected )
                return 

            self .wifi_selected =0 
            self ._draw_wifi_list ()
        except Exception as e :
            self .display .show_message ("WiFi",f"Error: {str (e )[:50 ]}\nMake sure nmcli\nis installed",(200 ,100 ,100 ),self .nav_items ,self .nav_selected_index ,wifi_connected )

    def _draw_wifi_list (self ):
        """Draw the WiFi network list with color-coded security."""
        wifi_connected =self ._get_wifi_connected ()
        if not hasattr (self ,'wifi_networks')or not self .wifi_networks :
            self .display .show_message ("WiFi","No networks",(200 ,100 ,100 ),self .nav_items ,self .nav_selected_index ,wifi_connected )
            return 


        if self .wifi_selected <len (self .wifi_networks ):
            ssid ,signal ,security ,color =self .wifi_networks [self .wifi_selected ]

            color_rgb =(0 ,255 ,0 )if color =="green"else (255 ,0 ,0 )
            security_label ="Open"if security ==""else "Locked"
            message =f"SSID: {ssid }\nSignal: {signal }\n{security_label }\n\nSelect to connect"
            self .display .show_message ("WiFi",message ,color_rgb ,self .nav_items ,self .nav_selected_index ,wifi_connected )
        else :
            message ="No selection"
            self .display .show_message ("WiFi",message ,(100 ,200 ,255 ),self .nav_items ,self .nav_selected_index ,wifi_connected )

    def handle_wifi_input (self ,action ):
        """Handle WiFi menu navigation and connection."""
        if not hasattr (self ,'wifi_networks'):
            self .wifi_networks =[]

        if action =='up':
            self .wifi_selected =(self .wifi_selected -1 )%len (self .wifi_networks )if self .wifi_networks else 0 
            self ._draw_wifi_list ()
        elif action =='down':
            self .wifi_selected =(self .wifi_selected +1 )%len (self .wifi_networks )if self .wifi_networks else 0 
            self ._draw_wifi_list ()
        elif action in ('select','right'):
            if self .wifi_networks and self .wifi_selected <len (self .wifi_networks ):
                ssid ,_ ,security ,_ =self .wifi_networks [self .wifi_selected ]
                self ._connect_to_wifi (ssid ,security )
        elif action =='left':
            self .current_screen ="settings"
            self .selected_index =0 
            self .show_settings_menu ()

    def _connect_to_wifi (self ,ssid ,security =""):
        """Initiate WiFi connection. If secured, prompt for password."""
        if security and security !="":

            self .wifi_password =""
            self .wifi_password_ssid =ssid 
            self .wifi_keyboard_index =0 
            self .current_screen ="wifi_password"
            self .show_wifi_keyboard ()
        else :

            self ._attempt_wifi_connect (ssid ,"")

    def show_wifi_keyboard (self ):
        """Display WiFi password keyboard."""
        wifi_connected =self ._get_wifi_connected ()
        current_char =self .wifi_keyboard_chars [self .wifi_keyboard_index ]
        masked_password ="*"*len (self .wifi_password )
        message =(
        f"Enter password:\n{masked_password }\n\n"
        f"Char: {current_char }\n\n"
        "Up/Dn: Select\nSel: Add\n"
        "Key1: Del  Key2: Try\nKey3: Back"
        )
        self .display .show_message ("WiFi Password",message ,(150 ,200 ,255 ),self .nav_items ,self .nav_selected_index ,wifi_connected )

    def handle_wifi_password_input (self ,action ):
        """Handle WiFi password keyboard input."""
        if action =='up':
            self .wifi_keyboard_index =(self .wifi_keyboard_index -1 )%len (self .wifi_keyboard_chars )
            self .show_wifi_keyboard ()
        elif action =='down':
            self .wifi_keyboard_index =(self .wifi_keyboard_index +1 )%len (self .wifi_keyboard_chars )
            self .show_wifi_keyboard ()
        elif action in ('select','right'):

            self .wifi_password +=self .wifi_keyboard_chars [self .wifi_keyboard_index ]
            self .show_wifi_keyboard ()
        elif action =='key1':

            if self .wifi_password :
                self .wifi_password =self .wifi_password [:-1 ]
            self .show_wifi_keyboard ()
        elif action =='key2':

            self ._attempt_wifi_connect (self .wifi_password_ssid ,self .wifi_password )
        elif action =='key3'or action =='left':

            self .current_screen ="wifi"
            self .show_wifi_menu ()

    def _attempt_wifi_connect (self ,ssid ,password ):
        """Attempt actual connection to WiFi network."""
        self .display .show_message ("WiFi",f"Connecting to\n{ssid }...",(100 ,200 ,255 ),self .nav_items ,self .nav_selected_index ,self ._get_wifi_connected ())

        try :
            if password :

                result =subprocess .run (
                ['nmcli','device','wifi','connect',ssid ,'password',password ],
                capture_output =True ,
                text =True ,
                timeout =10 
                )
            else :

                result =subprocess .run (
                ['nmcli','device','wifi','connect',ssid ],
                capture_output =True ,
                text =True ,
                timeout =10 
                )

            if result .returncode ==0 :

                self ._wifi_state =True 
                self ._wifi_checked_at =time .time ()
                time .sleep (1 )
                self .display .show_message ("WiFi",f"Connected to\n{ssid }!",(100 ,255 ,100 ),self .nav_items ,self .nav_selected_index ,True )
                time .sleep (2 )
            else :
                error_msg =result .stderr .strip ()[:50 ]if result .stderr else "Connection failed"
                self .display .show_message ("WiFi",f"Error:\n{error_msg }",(255 ,100 ,100 ),self .nav_items ,self .nav_selected_index ,self ._get_wifi_connected ())
                time .sleep (2 )
        except Exception as e :
            self .display .show_message ("WiFi",f"Error: {str (e )[:40 ]}",(255 ,100 ,100 ),self .nav_items ,self .nav_selected_index ,self ._get_wifi_connected ())
            time .sleep (2 )


        self .current_screen ="wifi"
        self .show_wifi_menu ()

    def show_ab_day_menu (self ):
        preset_keys =list (DAY_PRESETS .keys ())
        current_label =preset_keys [self .current_preset_index %len (preset_keys )]

        if len (preset_keys )>2 :
            message =f"Day Preset: {current_label }\n\nUp/Down: Change\nSelect: Done"
            title ="Day Preset"
        else :
            message =f"A/B Day: {current_label }\n\nUp/Down: Toggle\nSelect: Done"
            title ="A/B Day"

        wifi_connected =self ._get_wifi_connected ()
        self .display .show_message (title ,message ,(200 ,150 ,255 ),self .nav_items ,self .nav_selected_index ,wifi_connected )

    def show_set_time_menu (self ):
        wifi_connected =self ._get_wifi_connected ()
        self .display .show_menu (self .set_time_menu_items ,self .selected_index ,"Set Time",nav_items =self .nav_items ,nav_selected_index =self .nav_selected_index ,wifi_connected =wifi_connected )

    def show_set_time_screen (self ):
        if USE_24_HOUR :
            hour_str =f"{self .adjust_hour :02d}"
            minute_str =f"{self .adjust_minute :02d}"
            message =f"Set Time:\n{hour_str }:{minute_str }\n\nKey1: Hour+\nKey2: Min+\nKey3: Done"
        else :

            display_hour =self .adjust_hour %12 
            if display_hour ==0 :
                display_hour =12 
            am_pm ="AM"if self .adjust_hour <12 else "PM"
            hour_str =f"{display_hour :02d}"
            minute_str =f"{self .adjust_minute :02d}"
            message =f"Set Time:\n{hour_str }:{minute_str } {am_pm }\n\nKey1: Hour+\nKey2: Min+\nKey3: Done"
        wifi_connected =self ._get_wifi_connected ()
        self .display .show_message ("Set Time",message ,(255 ,200 ,100 ),self .nav_items ,self .nav_selected_index ,wifi_connected )

    def handle_set_time_input (self ,action ):
        if action =='key1':
            self .adjust_hour =(self .adjust_hour +1 )%24 
            self .show_set_time_screen ()
        elif action =='key2':
            self .adjust_minute =(self .adjust_minute +1 )%60 
            self .show_set_time_screen ()
        elif action =='key3':
            self .apply_manual_time ()
            self .current_screen ="set_time_menu"
            self .selected_index =0 
            self .show_set_time_menu ()
        elif action =='select'or action =='left':
            self .current_screen ="set_time_menu"
            self .selected_index =0 
            self .show_set_time_menu ()

    def handle_set_time_menu_input (self ,action ):
        if action =='up':
            self .selected_index =(self .selected_index -1 )%len (self .set_time_menu_items )
            self .show_set_time_menu ()
        elif action =='down':
            self .selected_index =(self .selected_index +1 )%len (self .set_time_menu_items )
            self .show_set_time_menu ()
        elif action =='select'or action =='right':
            selected_item =self .set_time_menu_items [self .selected_index ]
            if selected_item =="Manual Set":
                self .current_screen ="set_time"
                now =datetime .datetime .now ()
                self .adjust_hour =now .hour 
                self .adjust_minute =now .minute 
                self .show_set_time_screen ()
            elif selected_item =="Sync Now":

                self .sync_time_now ()

                self .show_set_time_menu ()
        elif action =='left':
            self .current_screen ="settings"
            self .selected_index =0 
            self .show_settings_menu ()

    def handle_ab_day_input (self ,action ):
        preset_keys =list (DAY_PRESETS .keys ())
        num_presets =len (preset_keys )

        if action in ('up','down'):
            if action =='up':
                self .current_preset_index =(self .current_preset_index -1 )%num_presets 
            else :
                self .current_preset_index =(self .current_preset_index +1 )%num_presets 
            self .last_advance_date =datetime .date .today ().isoformat ()
            self ._save_state ()
            self .show_ab_day_menu ()
        elif action in ('select','right','left'):
            self .current_screen ="settings"
            self .selected_index =0 
            self .show_settings_menu ()

    def handle_main_menu_input (self ,action ):

        if action =='select'or action =='right':
            selected_item =self .nav_items [self .nav_selected_index ]
            if selected_item =="Main Page":
                self .current_screen ="main"
                self .show_main_menu ()
            elif selected_item =="Tools":
                self .current_screen ="tools"
                self .selected_index =0 
                self .tools_scroll_offset =0 
                self .nav_selected_index =self .nav_items .index ("Tools")if "Tools"in self .nav_items else 1 
                self .show_tools_menu ()
            elif selected_item =="Settings":
                self .current_screen ="settings"
                self .selected_index =0 
                self .show_settings_menu ()

    def handle_tools_input (self ,action ):
        if action =='up':
            self .selected_index =(self .selected_index -1 )%len (self .tools_menu_items )
            self .show_tools_menu ()
        elif action =='down':
            self .selected_index =(self .selected_index +1 )%len (self .tools_menu_items )
            self .show_tools_menu ()
        elif action =='select'or action =='right':
            selected_item =self .tools_menu_items [self .selected_index ]
            if selected_item =="Grades":
                self .current_screen ="grades"
                self .show_grades_menu ()
            elif selected_item =="Stopwatch":
                self .current_screen ='stopwatch'
                self .show_stopwatch ()
            elif selected_item =="Developer":
                self .current_screen ='developer'
                self ._konami_index =0 
                self .show_developer_menu ()
        elif action =='left':
            self .current_screen ="main"
            self .selected_index =0 
            self .nav_selected_index =self .nav_items .index ("Main Page")if "Main Page"in self .nav_items else 0 
            self .show_main_menu ()

    def handle_schedule_input (self ,action ):
        if action =='left':
            self .current_screen ="main"
            self .selected_index =0 
            self .show_main_menu ()

    def handle_clock_input (self ,action ):
        if action =='left':
            self .current_screen ="main"
            self .selected_index =0 
            self .show_main_menu ()

    def handle_settings_input (self ,action ):
        if action =='up':
            self .selected_index =(self .selected_index -1 )%len (self .settings_menu_items )
            self .show_settings_menu ()
        elif action =='down':
            self .selected_index =(self .selected_index +1 )%len (self .settings_menu_items )
            self .show_settings_menu ()
        elif action =='select'or action =='right':
            selected_item =self .settings_menu_items [self .selected_index ]
            if selected_item =="WiFi":
                self .current_screen ="wifi"
                self .show_wifi_menu ()
            elif selected_item in ("A/B Day","Day Presets"):
                self .current_screen ="ab_day"
                self .show_ab_day_menu ()
            elif selected_item =="Appearance":
                self .current_screen ="appearance"
                self .selected_index =0 
                self .theme_scroll_offset =0 
                self .font_scroll_offset =0 
                self .show_appearance_menu ()
            elif selected_item =="Brightness":
                self .current_screen ="backlight"
                self .show_backlight_menu ()
            elif selected_item =="Progress Bar":
                self .current_screen ="progress_bar"
                self .show_progress_bar_menu ()
            elif selected_item =="Set Time":
                self .current_screen ="set_time_menu"
                self .selected_index =0 
                self .show_set_time_menu ()
            elif selected_item =="Developer":
                self .current_screen ='developer'
                self ._konami_index =0 
                self .show_developer_menu ()
            elif selected_item =="Version":
                self .current_screen ="version"
                self .selected_index =0 
                self .show_version_menu ()
            elif selected_item =="Update":
                self ._run_update ()
            elif selected_item =="Restart":
                self .restart_program ()
        elif action =='left':
            self .current_screen ="main"
            self .selected_index =0 
            self .show_main_menu ()

    def _format_stopwatch_time (self ):
        total =self .stopwatch_elapsed 
        if self .stopwatch_running :
            total +=time .time ()-self .stopwatch_start_ts 
        minutes =int (total //60 )
        seconds =int (total %60 )
        tenths =int ((total -int (total ))*10 )
        return f"{minutes :02d}:{seconds :02d}.{tenths }"

    def show_stopwatch (self ):
        wifi_connected =self ._get_wifi_connected ()
        status ="Stop"if self .stopwatch_running else "Start"
        elapsed_txt =self ._format_stopwatch_time ()
        msg =f"{elapsed_txt }\nUp: Reset\nSelect: {status }"
        self .display .show_message ("Stopwatch",msg ,(150 ,200 ,255 ),self .nav_items ,self .nav_selected_index ,wifi_connected )

    def handle_stopwatch_input (self ,action ):
        if action =='up':

            self .stopwatch_elapsed =0.0 
            if self .stopwatch_running :
                self .stopwatch_start_ts =time .time ()
            self .show_stopwatch ()
        elif action in ('select','right'):

            if self .stopwatch_running :
                self .stopwatch_elapsed +=time .time ()-self .stopwatch_start_ts 
                self .stopwatch_running =False 
            else :
                self .stopwatch_start_ts =time .time ()
                self .stopwatch_running =True 
            self .show_stopwatch ()
        elif action =='left':
            self .current_screen ='tools'
            self .selected_index =self .tools_menu_items .index ("Stopwatch")if "Stopwatch"in self .tools_menu_items else 0 
            self .nav_selected_index =self .nav_items .index ("Tools")if "Tools"in self .nav_items else 1 
            self .show_tools_menu ()

    def _get_repo_dir (self ):
        code_dir =os .path .dirname (os .path .abspath (__file__ ))
        repo_dir =os .path .abspath (os .path .join (code_dir ,'..'))
        if os .path .isdir (os .path .join (repo_dir ,'.git')):
            return repo_dir 
        fallback ='/home/pi/Timagotchi'
        if os .path .isdir (os .path .join (fallback ,'.git'))or os .path .isdir (fallback ):
            return fallback 
        return repo_dir 

    def _git_run (self ,args ,repo_dir =None ,timeout =8 ):
        repo_dir =repo_dir or self ._get_repo_dir ()
        base_args =list (args )
        commands =[
        ['git','-C',repo_dir ]+base_args ,
        ]
        if os .name !='nt':
            commands .append (['sudo','-n','git','-C',repo_dir ]+base_args )

        last_result =None 
        for cmd in commands :
            try :
                result =subprocess .run (cmd ,capture_output =True ,text =True ,timeout =timeout )
            except Exception as exc :
                result =subprocess .CompletedProcess (cmd ,1 ,'',str (exc ))
            if result .returncode ==0 :
                return result 
            last_result =result 
        return last_result 

    def _get_current_branch (self ):
        result =self ._git_run (['rev-parse','--abbrev-ref','HEAD'])
        if not result or result .returncode !=0 :
            return None 
        branch =(result .stdout or '').strip ()
        if branch in ('','HEAD'):
            return None 
        return branch 

    def _get_recent_commits (self ,limit =3 ):
        try :
            limit =max (1 ,int (limit ))
        except Exception :
            limit =3 
        result =self ._git_run (['log',f'-{limit }','--pretty=format:%h %s'])
        if not result or result .returncode !=0 :
            return []
        commits =[]
        for line in (result .stdout or '').splitlines ():
            text =line .strip ()
            if text :
                commits .append (text )
        return commits 

    def _pick_stable_branch (self ):
        for candidate in ('stable','main'):
            local_ref =self ._git_run (['show-ref','--verify','--quiet',f'refs/heads/{candidate }'])
            if local_ref and local_ref .returncode ==0 :
                return candidate 
            remote_ref =self ._git_run (['show-ref','--verify','--quiet',f'refs/remotes/origin/{candidate }'])
            if remote_ref and remote_ref .returncode ==0 :
                return candidate 
        return 'main'

    def show_version_menu (self ):
        branch =self ._get_current_branch ()
        title =f"Version ({branch })"if branch else "Version"
        wifi_connected =self ._get_wifi_connected ()
        self .display .show_menu (
        self .version_menu_items ,
        self .selected_index ,
        title ,
        nav_items =self .nav_items ,
        nav_selected_index =self .nav_selected_index ,
        start_index =0 ,
        max_visible =6 ,
        wifi_connected =wifi_connected ,
        )

    def handle_version_input (self ,action ):
        if action =='up':
            self .selected_index =(self .selected_index -1 )%len (self .version_menu_items )
            self .show_version_menu ()
        elif action =='down':
            self .selected_index =(self .selected_index +1 )%len (self .version_menu_items )
            self .show_version_menu ()
        elif action in ('select','right'):
            selected_item =self .version_menu_items [self .selected_index ]
            if selected_item =='Recent Changes':
                self .current_screen ='version_info'
                self .show_version_info ()
            elif selected_item =='Switch to Stable':
                target =self ._pick_stable_branch ()
                self ._switch_to_branch (target )
            elif selected_item =='Switch to Beta':
                self ._switch_to_branch ('beta')
        elif action =='left':
            self .current_screen ='settings'
            self .selected_index =self .settings_menu_items .index ("Version")if "Version"in self .settings_menu_items else 0 
            self .show_settings_menu ()

    def show_version_info (self ):
        wifi_connected =self ._get_wifi_connected ()
        branch =self ._get_current_branch ()or "Unknown"
        commits =self ._get_recent_commits (limit =3 )

        if commits :
            short_commits =[line [:26 ]for line in commits ]
            message =f"Branch: {branch }\n"+"\n".join (short_commits )
        else :
            message =f"Branch: {branch }\nNo recent changes found."

        self .display .show_message ("Recent Changes",message ,(180 ,220 ,255 ),self .nav_items ,self .nav_selected_index ,wifi_connected )

    def handle_version_info_input (self ,action ):
        if action in ('left','select','right'):
            self .current_screen ='version'
            self .selected_index =0 
            self .show_version_menu ()

    def _switch_to_branch (self ,target ):
        try :
            target =(target or '').strip ()
            if not target :
                self .display .show_face_message ("Version","Invalid branch","broken",(255 ,100 ,100 ),self .nav_items ,self .nav_selected_index ,self ._get_wifi_connected ())
                time .sleep (1.2 )
                self .show_version_menu ()
                return 

            repo_dir =self ._get_repo_dir ()
            self .display .show_face_message ("Version",f"Switching to {target }","upload",(180 ,220 ,255 ),self .nav_items ,self .nav_selected_index ,self ._get_wifi_connected ())

            fetch_result =self ._git_run (['fetch','--all','--prune'],repo_dir =repo_dir ,timeout =20 )
            if not fetch_result or fetch_result .returncode !=0 :
                err =(fetch_result .stderr .strip ()if fetch_result and fetch_result .stderr else 'Fetch failed')[:80 ]
                self .display .show_face_message ("Version",err ,"broken",(255 ,100 ,100 ),self .nav_items ,self .nav_selected_index ,self ._get_wifi_connected ())
                time .sleep (1.5 )
                self .show_version_menu ()
                return 

            local_ref =self ._git_run (['show-ref','--verify','--quiet',f'refs/heads/{target }'],repo_dir =repo_dir )
            remote_ref =self ._git_run (['show-ref','--verify','--quiet',f'refs/remotes/origin/{target }'],repo_dir =repo_dir )
            has_local =local_ref and local_ref .returncode ==0 
            has_remote =remote_ref and remote_ref .returncode ==0 

            if not has_local and not has_remote :
                self .display .show_face_message ("Version",f"Branch '{target }' not found","broken",(255 ,100 ,100 ),self .nav_items ,self .nav_selected_index ,self ._get_wifi_connected ())
                time .sleep (1.5 )
                self .show_version_menu ()
                return 

            if has_local :
                checkout_result =self ._git_run (['checkout',target ],repo_dir =repo_dir ,timeout =15 )
            else :
                checkout_result =self ._git_run (['checkout','-b',target ,'--track',f'origin/{target }'],repo_dir =repo_dir ,timeout =15 )

            if not checkout_result or checkout_result .returncode !=0 :
                err =(checkout_result .stderr .strip ()if checkout_result and checkout_result .stderr else 'Checkout failed')[:80 ]
                self .display .show_face_message ("Version",err ,"broken",(255 ,100 ,100 ),self .nav_items ,self .nav_selected_index ,self ._get_wifi_connected ())
                time .sleep (1.5 )
                self .show_version_menu ()
                return 

            pull_result =self ._git_run (['pull','--ff-only','origin',target ],repo_dir =repo_dir ,timeout =30 )
            if not pull_result or pull_result .returncode !=0 :
                err =(pull_result .stderr .strip ()if pull_result and pull_result .stderr else 'Pull failed')[:80 ]
                self .display .show_face_message ("Version",err ,"broken",(255 ,100 ,100 ),self .nav_items ,self .nav_selected_index ,self ._get_wifi_connected ())
                time .sleep (1.5 )
                self .show_version_menu ()
                return 

            self .display .show_face_message ("Version",f"Switched to {target }","happy",(100 ,255 ,100 ),self .nav_items ,self .nav_selected_index ,self ._get_wifi_connected ())
            time .sleep (1.0 )
            self .restart_program ()
        except Exception as exc :
            self .display .show_face_message ("Version",(str (exc )or "Switch failed")[:80 ],"broken",(255 ,100 ,100 ),self .nav_items ,self .nav_selected_index ,self ._get_wifi_connected ())
            time .sleep (1.5 )
            if self .running :
                self .show_version_menu ()

    def _run_update (self ):
        """Run sudo git pull (ff-only) and show face on completion."""
        try :
            repo_dir ="/home/pi/Timagotchi"


            git_check =subprocess .run (['git','--version'],capture_output =True ,text =True ,timeout =5 )
            if git_check .returncode !=0 :
                self .display .show_face_message ("Update","git not installed","broken",(255 ,100 ,100 ),self .nav_items ,self .nav_selected_index )
                return 


            try :
                subprocess .run (['git','config','--global','--add','safe.directory',repo_dir ],capture_output =True ,text =True ,timeout =5 )
            except Exception :
                pass 


            remote =subprocess .run (['git','-C',repo_dir ,'config','--get','remote.origin.url'],capture_output =True ,text =True ,timeout =5 )
            if remote .returncode !=0 or not remote .stdout .strip ():
                origin_url ='https://github.com/broseph9972/Timagotchi'
                add_remote =subprocess .run (['git','-C',repo_dir ,'remote','add','origin',origin_url ],capture_output =True ,text =True ,timeout =10 )
                if add_remote .returncode !=0 and 'already exists'not in (add_remote .stderr or '').lower ():
                    err =add_remote .stderr .strip ()[:80 ]or "Failed to add origin"
                    self .display .show_face_message ("Update",err ,"broken",(255 ,100 ,100 ),self .nav_items ,self .nav_selected_index )
                    return 


            branch =subprocess .run (['git','-C',repo_dir ,'rev-parse','--abbrev-ref','HEAD'],capture_output =True ,text =True ,timeout =5 )
            current_branch =branch .stdout .strip ()or 'main'
            if current_branch in ('HEAD',''):
                current_branch ='main'


            subprocess .run (['sudo','-n','git','-C',repo_dir ,'fetch','--all','--prune'],capture_output =True ,text =True ,timeout =20 )
            result =subprocess .run (['sudo','-n','git','-C',repo_dir ,'pull','--ff-only','origin',current_branch ],capture_output =True ,text =True ,timeout =30 )

            if result .returncode ==0 :
                stdout_msg =result .stdout .strip ()or "Up to date"
                updated ="already up to date"not in stdout_msg .lower ()
                self .display .show_face_message ("Update",stdout_msg [:60 ],"happy",(100 ,255 ,100 ),self .nav_items ,self .nav_selected_index )
                time .sleep (1.0 )
                if updated :
                    self .restart_program ()
                    return 
            else :
                full_err =result .stderr .strip ()or result .stdout .strip ()or "Pull failed"
                self .display .show_message ("Update Error",full_err ,(255 ,100 ,100 ),self .nav_items ,self .nav_selected_index )
                time .sleep (2.0 )
                self .display .show_face_message ("Update","Forcing pull...","upload",(180 ,220 ,255 ),self .nav_items ,self .nav_selected_index )
                
                config_path =os .path .join (repo_dir ,'Code','config.py')
                config_backup =None 
                if os .path .exists (config_path ):
                    try :
                        with open (config_path ,'r')as f :
                            config_backup =f .read ()
                    except Exception :
                        config_backup =None 
                
                force_result =subprocess .run (['sudo','-n','git','-C',repo_dir ,'pull','-X','ours','origin',current_branch ],capture_output =True ,text =True ,timeout =30 )
                
                if config_backup is not None :
                    try :
                        with open (config_path ,'w')as f :
                            f .write (config_backup )
                    except Exception :
                        pass 
                
                if force_result .returncode ==0 :
                    self .display .show_face_message ("Update","Force pull succeeded","happy",(100 ,255 ,100 ),self .nav_items ,self .nav_selected_index )
                    time .sleep (1.0 )
                    self .restart_program ()
                    return 
                else :
                    force_err =force_result .stderr .strip ()or force_result .stdout .strip ()or "Force pull failed"
                    self .display .show_message ("Force Pull Error",force_err ,(255 ,100 ,100 ),self .nav_items ,self .nav_selected_index )
        except Exception as e :
            self .display .show_face_message ("Update",(str (e )or "error")[:80 ],"broken",(255 ,100 ,100 ),self .nav_items ,self .nav_selected_index )
        finally :

            if self .running :
                time .sleep (1.5 )
                self .current_screen ='settings'
                self .selected_index =self .settings_menu_items .index ("Update")if "Update"in self .settings_menu_items else 0 
                self .show_settings_menu ()

    def check_updates_on_boot (self ):
        """Check for updates on boot (silent, non-blocking). Returns True if update was applied and restart is needed."""
        try :
            repo_dir ="/home/pi/Timagotchi"


            git_check =subprocess .run (['git','--version'],capture_output =True ,text =True ,timeout =5 )
            if git_check .returncode !=0 :
                return False 


            try :
                subprocess .run (['git','config','--global','--add','safe.directory',repo_dir ],
                capture_output =True ,text =True ,timeout =5 )
            except Exception :
                pass 


            remote =subprocess .run (['git','-C',repo_dir ,'config','--get','remote.origin.url'],
            capture_output =True ,text =True ,timeout =5 )
            if remote .returncode !=0 or not remote .stdout .strip ():
                origin_url ='https://github.com/broseph9972/Timagotchi'
                subprocess .run (['git','-C',repo_dir ,'remote','add','origin',origin_url ],
                capture_output =True ,text =True ,timeout =10 )


            branch =subprocess .run (['git','-C',repo_dir ,'rev-parse','--abbrev-ref','HEAD'],
            capture_output =True ,text =True ,timeout =5 )
            current_branch =branch .stdout .strip ()or 'main'
            if current_branch in ('HEAD',''):
                current_branch ='main'


            subprocess .run (['sudo','-n','git','-C',repo_dir ,'fetch','--all','--prune'],
            capture_output =True ,text =True ,timeout =10 )


            result =subprocess .run (['sudo','-n','git','-C',repo_dir ,'pull','--ff-only','origin',current_branch ],
            capture_output =True ,text =True ,timeout =15 )

            if result .returncode ==0 :
                stdout_msg =result .stdout .strip ().lower ()or "up to date"

                if "already up to date"not in stdout_msg :
                    print ("[Boot Update] Updates found and applied. Restart recommended.")
                    return True 

            return False 
        except subprocess .TimeoutExpired :

            return False 
        except Exception as e :

            return False 

    def start_boot_git_maintenance_background (self ):
        """Start repo integrity check + auto-repair in a daemon thread."""
        try :
            worker =threading .Thread (target =self ._boot_git_maintenance_worker ,daemon =True )
            worker .start ()
        except Exception as exc :
            print (f"[Boot Git] Failed to start background maintenance: {exc }")

    def _boot_git_maintenance_worker (self ):
        """Background worker: check for git corruption and auto-repair if needed."""
        try :
            repo_dir =self ._get_repo_dir ()

            git_check =subprocess .run (['git','--version'],capture_output =True ,text =True ,timeout =5 )
            if git_check .returncode !=0 :
                print ("[Boot Git] git not installed; skipping integrity check.")
                return 

            try :
                subprocess .run (['git','config','--global','--add','safe.directory',repo_dir ],capture_output =True ,text =True ,timeout =5 )
            except Exception :
                pass 

            fsck_result =self ._git_run (['fsck','--full','--no-progress'],repo_dir =repo_dir ,timeout =45 )
            fsck_output =((fsck_result .stdout or '')+'\n'+(fsck_result .stderr or '')).lower ()if fsck_result else ''

            if self ._git_output_indicates_corruption (fsck_output ):
                print ("[Boot Git] Repository corruption detected. Running background auto-repair...")
                repaired =self ._repair_repo_in_background (repo_dir )
                if repaired :
                    print ("[Boot Git] Auto-repair completed successfully.")
                else :
                    print ("[Boot Git] Auto-repair failed. Manual re-clone may be required.")
            else :
                print ("[Boot Git] Repository integrity check passed.")
        except subprocess .TimeoutExpired :
            print ("[Boot Git] Integrity check timed out; skipping this boot.")
        except Exception as exc :
            print (f"[Boot Git] Background maintenance error: {exc }")

    def _git_output_indicates_corruption (self ,output_text ):
        text =(output_text or '').lower ()
        corruption_signatures =[
        'object file',
        'is empty',
        'bad object',
        'missing blob',
        'missing tree',
        'missing commit',
        'corrupt',
        'unable to read',
        'fatal: loose object',
        'error: object file',
        ]
        return any (sig in text for sig in corruption_signatures )

    def _repair_repo_in_background (self ,repo_dir ):
        """Attempt non-interactive repair for common object corruption cases."""
        try :
            branch =self ._get_current_branch ()or 'main'

            fetch_result =self ._git_run (['fetch','--all','--prune'],repo_dir =repo_dir ,timeout =45 )
            if not fetch_result or fetch_result .returncode !=0 :
                return False 

            reset_result =self ._git_run (['reset','--hard',f'origin/{branch }'],repo_dir =repo_dir ,timeout =45 )
            if not reset_result or reset_result .returncode !=0 :
                return False 

            clean_result =self ._git_run (['clean','-fd'],repo_dir =repo_dir ,timeout =30 )
            if clean_result and clean_result .returncode !=0 :
                return False 

            post_fsck =self ._git_run (['fsck','--full','--no-progress'],repo_dir =repo_dir ,timeout =45 )
            post_output =((post_fsck .stdout or '')+'\n'+(post_fsck .stderr or '')).lower ()if post_fsck else ''
            if self ._git_output_indicates_corruption (post_output ):
                return False 

            return True 
        except Exception :
            return False 

    def show_grades_menu (self ,fetch =True ):
        """Display grades menu. fetch=True to fetch from API, False to redraw cached list."""
        if fetch :
            cfg =self ._canvas_load_config ()
            if not cfg :
                self .display .show_message ("Canvas","Set URL & API key",(255 ,150 ,100 ),self .nav_items ,self .nav_selected_index ,self ._get_wifi_connected ())
                return 
            self .display .show_message ("Canvas","Loading courses...",(100 ,200 ,255 ),self .nav_items ,self .nav_selected_index ,self ._get_wifi_connected ())
            courses =self ._canvas_fetch_courses (cfg )
            if courses is None :
                self .display .show_message ("Canvas","Fetch failed",(255 ,100 ,100 ),self .nav_items ,self .nav_selected_index ,self ._get_wifi_connected ())
                return 
            if not courses :
                self .display .show_message ("Canvas","No courses",(200 ,200 ,200 ),self .nav_items ,self .nav_selected_index ,self ._get_wifi_connected ())
                return 
            self ._courses_list =courses 


        if not hasattr (self ,'_courses_list')or not self ._courses_list :
            self .display .show_message ("Canvas","No courses",(200 ,200 ,200 ),self .nav_items ,self .nav_selected_index ,self ._get_wifi_connected ())
            return 

        max_visible =6 
        if self .grades_selected_index <self .grades_scroll_offset :
            self .grades_scroll_offset =self .grades_selected_index 
        elif self .grades_selected_index >=self .grades_scroll_offset +max_visible :
            self .grades_scroll_offset =self .grades_selected_index -max_visible +1 

        items =[self ._format_course_item (c ,max_len =14 )for c in self ._courses_list ]
        self .display .show_grades_menu (items ,self .grades_selected_index ,title ="Grades",nav_items =self .nav_items ,nav_selected_index =self .nav_selected_index ,start_index =self .grades_scroll_offset ,max_visible =max_visible ,wifi_connected =self ._get_wifi_connected ())

    def handle_grades_input (self ,action ):
        if not hasattr (self ,'_courses_list')or not self ._courses_list :
            self .show_grades_menu (fetch =True )
            return 
        if action =='up':
            self .grades_selected_index =(self .grades_selected_index -1 )%len (self ._courses_list )
            self .show_grades_menu (fetch =False )
        elif action =='down':
            self .grades_selected_index =(self .grades_selected_index +1 )%len (self ._courses_list )
            self .show_grades_menu (fetch =False )
        elif action in ('select','right'):
            course =self ._courses_list [self .grades_selected_index ]
            self .current_course_id =course ['id']
            self .current_screen ='assignments'
            self .assign_selected_index =0 
            self .show_assignments_menu ()
        elif action =='left':
            self .current_screen ='tools'
            self .selected_index =self .tools_menu_items .index ("Grades")if "Grades"in self .tools_menu_items else 0 
            self .nav_selected_index =self .nav_items .index ("Tools")if "Tools"in self .nav_items else 1 
            self .show_tools_menu ()

    def show_secret_menu (self ):
        wifi_connected =self ._get_wifi_connected ()
        self .display .show_menu (self .secret_menu_items ,self .selected_index ,"Secret Menu",nav_items =self .nav_items ,nav_selected_index =self .nav_selected_index ,wifi_connected =wifi_connected )

    def handle_secret_menu_input (self ,action ):
        if action =='up':
            self .selected_index =(self .selected_index -1 )%len (self .secret_menu_items )
            self .show_secret_menu ()
        elif action =='down':
            self .selected_index =(self .selected_index +1 )%len (self .secret_menu_items )
            self .show_secret_menu ()
        elif action in ('select','right'):
            choice =self .secret_menu_items [self .selected_index ]
            if choice =="Start Tetris":
                self .launch_tetris_pygame ()
            elif choice =="Doom":
                self .launch_doom_pydoom ()
            elif choice =="Shitty Doom":
                self .launch_shitty_doom ()
            elif choice =="Run Custom Script":
                self .launch_custom_script ()
        elif action =='left':
            self .current_screen ='tools'
            self .selected_index =0 
            self .nav_selected_index =self .nav_items .index ("Tools")if "Tools"in self .nav_items else 1 
            self .show_tools_menu ()

    def show_developer_menu (self ):
        wifi_connected =self ._get_wifi_connected ()
        message =""
        self .display .show_message ("Developer",message ,(150 ,100 ,200 ),self .nav_items ,self .nav_selected_index ,wifi_connected )

    def handle_developer_input (self ,action ):

        if action in ('key1','key2','key3'):
            self ._konami_index =0 
            if action =='key1':
                self .current_screen ='main'
                self .nav_selected_index =self .nav_items .index ('Main Page')if 'Main Page'in self .nav_items else 0 
                self .show_main_menu ()
            elif action =='key2':
                self .current_screen ='tools'
                self .nav_selected_index =self .nav_items .index ('Tools')if 'Tools'in self .nav_items else 1 
                self .selected_index =0 
                self .tools_scroll_offset =0 
                self .show_tools_menu ()
            elif action =='key3':
                self .current_screen ='settings'
                self .nav_selected_index =self .nav_items .index ('Settings')if 'Settings'in self .nav_items else 2 
                self .selected_index =0 
                self .show_settings_menu ()
            return 


        if action :
            expected =self ._konami_code [self ._konami_index ]if self ._konami_index <len (self ._konami_code )else None 
            if action ==expected :
                self ._konami_index +=1 
                if self ._konami_index ==len (self ._konami_code ):
                    self ._konami_index =0 
                    self .current_screen ='secret_menu'
                    self .selected_index =0 
                    self .show_secret_menu ()
                    return 
            else :
                self ._konami_index =1 if action ==self ._konami_code [0 ]else 0 

    def launch_tetris_pygame (self ):
        """Launch Tetris directly on the Waveshare display."""
        self .display .show_message ("Tetris","Starting...",(100 ,200 ,255 ),self .nav_items ,self .nav_selected_index ,self ._get_wifi_connected ())
        time .sleep (0.3 )

        try :
            from tetris_waveshare import run_tetris 


            exit_key =run_tetris (self .display ,self .input_handler )


            if exit_key =='key1':
                self .current_screen ='main'
                self .nav_selected_index =self .nav_items .index ('Main Page')if 'Main Page'in self .nav_items else 0 
                self .show_main_menu ()
            elif exit_key =='key2':
                self .current_screen ='tools'
                self .nav_selected_index =self .nav_items .index ('Tools')if 'Tools'in self .nav_items else 1 
                self .selected_index =0 
                self .tools_scroll_offset =0 
                self .show_tools_menu ()
            elif exit_key =='key3':
                self .current_screen ='settings'
                self .nav_selected_index =self .nav_items .index ('Settings')if 'Settings'in self .nav_items else 2 
                self .selected_index =0 
                self .show_settings_menu ()
            else :
                self .current_screen ='main'
                self .nav_selected_index =self .nav_items .index ('Main Page')if 'Main Page'in self .nav_items else 0 
                self .show_main_menu ()

        except Exception as e :
            self .display .show_message ("Tetris",f"Error: {str (e )[:50 ]}",(255 ,100 ,100 ),self .nav_items ,self .nav_selected_index ,self ._get_wifi_connected ())
            time .sleep (2 )
            self .current_screen ='main'
            self .show_main_menu ()

    def launch_doom_pydoom (self ):
        """Launch Doom via PyDoom if available; otherwise show guidance."""
        self .display .show_message ("Doom","Starting...",(255 ,100 ,100 ),self .nav_items ,self .nav_selected_index ,self ._get_wifi_connected ())
        time .sleep (0.3 )

        try :

            pydoom_dir =os .path .join (os .path .dirname (__file__ ),'pydoom')
            if os .path .isdir (pydoom_dir )and pydoom_dir not in sys .path :
                sys .path .insert (0 ,pydoom_dir )


            try :
                import pydoom 
                pydoom_available =True 
            except Exception :
                pydoom_available =False 

            if not pydoom_available :
                msg ="PyDoom not found.\nRun install.sh to install PyDoom\nor place in Code/pydoom/"
                self .display .show_message ("Doom",msg ,(255 ,100 ,100 ),self .nav_items ,self .nav_selected_index ,self ._get_wifi_connected ())
                time .sleep (3 )
                self .current_screen ='secret_menu'
                self .show_secret_menu ()
                return 


            wad_candidates =[
            os .path .join (os .path .dirname (__file__ ),'doom1.wad'),
            os .path .join (os .path .dirname (__file__ ),'doom.wad'),
            os .path .join (pydoom_dir ,'doom1.wad'),
            os .path .join (pydoom_dir ,'doom.wad'),
            os .path .expanduser ('~/timagotchi/roms/doom1.wad'),
            os .path .expanduser ('~/timagotchi/roms/doom.wad'),
            ]
            wad_path =next ((p for p in wad_candidates if os .path .exists (p )),None )
            if wad_path is None :
                self .display .show_message ("Doom","doom1.wad missing\n(put in Code/ or Code/pydoom/)",(255 ,100 ,100 ),self .nav_items ,self .nav_selected_index ,self ._get_wifi_connected ())
                time .sleep (2 )
                self .current_screen ='secret_menu'
                self .show_secret_menu ()
                return 


            try :
                env =os .environ .copy ()
                if pydoom_dir not in env .get ('PYTHONPATH',''):
                    env ['PYTHONPATH']=pydoom_dir +':'+env .get ('PYTHONPATH','')
                subprocess .run ([sys .executable ,'-c',f"import sys; sys.path.insert(0, '{pydoom_dir }'); import pydoom; pydoom.run('{wad_path }')"],
                check =False ,env =env )
            except Exception as exc :
                self .display .show_message ("Doom",f"PyDoom error: {str (exc )[:60 ]}",(255 ,100 ,100 ),self .nav_items ,self .nav_selected_index ,self ._get_wifi_connected ())
                time .sleep (3 )

            self .current_screen ='secret_menu'
            self .show_secret_menu ()

        except Exception as e :
            self .display .show_message ("Doom",f"Error: {str (e )[:50 ]}",(255 ,100 ,100 ),self .nav_items ,self .nav_selected_index ,self ._get_wifi_connected ())
            time .sleep (2 )
            self .current_screen ='secret_menu'
            self .show_secret_menu ()

    def launch_shitty_doom (self ):
        """Run the built-in raycaster (fast, works on LCD)."""
        self .display .show_message ("Shitty Doom","Starting...",(255 ,150 ,100 ),self .nav_items ,self .nav_selected_index ,self ._get_wifi_connected ())
        time .sleep (0.2 )
        try :
            from doom_raycaster import run_raycaster 
            exit_key =run_raycaster (self .display ,self .input_handler )

            if exit_key =='key1':
                self .current_screen ='main'
                self .nav_selected_index =self .nav_items .index ('Main Page')if 'Main Page'in self .nav_items else 0 
                self .show_main_menu ()
            elif exit_key =='key2':
                self .current_screen ='tools'
                self .nav_selected_index =self .nav_items .index ('Tools')if 'Tools'in self .nav_items else 1 
                self .selected_index =0 
                self .tools_scroll_offset =0 
                self .show_tools_menu ()
            elif exit_key =='key3':
                self .current_screen ='settings'
                self .nav_selected_index =self .nav_items .index ('Settings')if 'Settings'in self .nav_items else 2 
                self .selected_index =0 
                self .show_settings_menu ()
            else :
                self .current_screen ='secret_menu'
                self .show_secret_menu ()
        except Exception as e :
            self .display .show_message ("Shitty Doom",f"Error: {str (e )[:60 ]}",(255 ,100 ,100 ),self .nav_items ,self .nav_selected_index ,self ._get_wifi_connected ())
            time .sleep (2 )
            self .current_screen ='secret_menu'
            self .show_secret_menu ()

    def launch_custom_script (self ):
        """
        Run custom_script.py directly with access to display and input.
        The script should have a run(display, input_handler) function.
        It should return 'key1', 'key2', or 'key3' to navigate on exit.
        """
        path =os .path .join (os .path .dirname (__file__ ),'custom_script.py')
        if not os .path .exists (path ):
            self .display .show_message ("Custom Script","Place custom_script.py in Code/",(255 ,150 ,100 ),self .nav_items ,self .nav_selected_index ,self ._get_wifi_connected ())
            time .sleep (2 )
            return 

        self .display .show_message ("Custom Script","Starting...",(100 ,200 ,255 ),self .nav_items ,self .nav_selected_index ,self ._get_wifi_connected ())
        time .sleep (0.3 )

        try :
            import importlib .util 
            spec =importlib .util .spec_from_file_location ("custom_script",path )
            custom_module =importlib .util .module_from_spec (spec )
            spec .loader .exec_module (custom_module )


            if hasattr (custom_module ,'run'):
                exit_key =custom_module .run (self .display ,self .input_handler )
            else :
                self .display .show_message ("Custom Script","No run() function found",(255 ,150 ,100 ),self .nav_items ,self .nav_selected_index ,self ._get_wifi_connected ())
                time .sleep (2 )
                exit_key =None 


            if exit_key =='key1':
                self .current_screen ='main'
                self .nav_selected_index =self .nav_items .index ('Main Page')if 'Main Page'in self .nav_items else 0 
                self .show_main_menu ()
            elif exit_key =='key2':
                self .current_screen ='tools'
                self .nav_selected_index =self .nav_items .index ('Tools')if 'Tools'in self .nav_items else 1 
                self .selected_index =0 
                self .tools_scroll_offset =0 
                self .show_tools_menu ()
            elif exit_key =='key3':
                self .current_screen ='settings'
                self .nav_selected_index =self .nav_items .index ('Settings')if 'Settings'in self .nav_items else 2 
                self .selected_index =0 
                self .show_settings_menu ()
            else :
                self .current_screen ='main'
                self .nav_selected_index =self .nav_items .index ('Main Page')if 'Main Page'in self .nav_items else 0 
                self .show_main_menu ()

        except Exception as e :
            self .display .show_message ("Custom Script",f"Error: {str (e )[:50 ]}",(255 ,100 ,100 ),self .nav_items ,self .nav_selected_index ,self ._get_wifi_connected ())
            time .sleep (2 )
            self .current_screen ='main'
            self .show_main_menu ()

    def show_assignments_menu (self ,fetch =True ):
        """Display assignments menu. fetch=True to fetch from API, False to redraw cached list."""
        if fetch :
            cfg =self ._canvas_load_config ()
            if not cfg or self .current_course_id is None :
                self .display .show_message ("Canvas","Missing course/config",(255 ,100 ,100 ),self .nav_items ,self .nav_selected_index ,self ._get_wifi_connected ())
                return 
            self .display .show_message ("Canvas","Loading assigns...",(100 ,200 ,255 ),self .nav_items ,self .nav_selected_index ,self ._get_wifi_connected ())
            assigns =self ._canvas_fetch_assignments (cfg ,self .current_course_id )
            if assigns is None :
                self .display .show_message ("Canvas","Fetch failed",(255 ,100 ,100 ),self .nav_items ,self .nav_selected_index ,self ._get_wifi_connected ())
                return 
            if not assigns :
                self .display .show_message ("Canvas","No assignments",(200 ,200 ,200 ),self .nav_items ,self .nav_selected_index ,self ._get_wifi_connected ())
                return 
            self ._assign_list =assigns 


        if not hasattr (self ,'_assign_list')or not self ._assign_list :
            self .display .show_message ("Canvas","No assignments",(200 ,200 ,200 ),self .nav_items ,self .nav_selected_index ,self ._get_wifi_connected ())
            return 

        max_visible =6 
        if self .assign_selected_index <self .assign_scroll_offset :
            self .assign_scroll_offset =self .assign_selected_index 
        elif self .assign_selected_index >=self .assign_scroll_offset +max_visible :
            self .assign_scroll_offset =self .assign_selected_index -max_visible +1 

        self ._assign_list =self ._sort_assignments_by_quarter_and_recency (self ._assign_list )
        items =[self ._format_assignment_item (a ,max_len =14 )for a in self ._assign_list ]
        course =next ((c for c in getattr (self ,'_courses_list',[])if c ['id']==self .current_course_id ),None )
        course_title =(course ['name']if course else 'Assignments')
        title =f"{course_title [:10 ]} {self ._format_percent (course .get ('percent')if course else None )}"
        self .display .show_menu (items ,self .assign_selected_index ,title =title ,nav_items =self .nav_items ,nav_selected_index =self .nav_selected_index ,start_index =self .assign_scroll_offset ,max_visible =max_visible ,wifi_connected =self ._get_wifi_connected ())

    def handle_assignments_input (self ,action ):
        if not hasattr (self ,'_assign_list')or not self ._assign_list :
            self .show_assignments_menu (fetch =True )
            return 
        if action =='up':
            self .assign_selected_index =(self .assign_selected_index -1 )%len (self ._assign_list )
            self .show_assignments_menu (fetch =False )
        elif action =='down':
            self .assign_selected_index =(self .assign_selected_index +1 )%len (self ._assign_list )
            self .show_assignments_menu (fetch =False )
        elif action in ('select','right'):
            a =self ._assign_list [self .assign_selected_index ]
            msg =f"Score: {self ._format_score (a )}\nStatus: {a .get ('status','--')}\nDue: {a .get ('due','--')}"
            self .display .show_message ("Assignment",msg ,(150 ,200 ,255 ),self .nav_items ,self .nav_selected_index ,self ._get_wifi_connected ())
        elif action =='left':
            self .current_screen ='grades'
            self .show_grades_menu (fetch =False )

    def _format_percent (self ,p ):
        try :
            if p is None :
                return "--"
            return f"{int (round (float (p )))}%"
        except Exception :
            return str (p )[:6 ]if p else "--"

    def _format_course_item (self ,c ,max_len =14 ):
        name =c .get ('name')or 'Course'
        score =self ._format_percent (c .get ('percent'))
        return self ._trim_name_with_score (name ,score ,max_len )

    def _format_assignment_item (self ,a ,max_len =14 ):
        name =a .get ('name')or 'Assignment'
        score =self ._format_score (a )
        return self ._trim_name_with_score (name ,score ,max_len )

    def _trim_name_with_score (self ,name ,score ,max_len ):
        score_text =score or "--"
        if max_len <=0 :
            return score_text [:max_len ]
        max_name_len =max_len -(len (score_text )+1 )
        if max_name_len <1 :
            return score_text [:max_len ]
        name_trim =str (name )[:max_name_len ]
        return f"{name_trim } {score_text }"

    def _parse_canvas_datetime (self ,value ):
        if not value :
            return None 
        try :
            text =str (value ).replace ('Z','+00:00')
            return datetime .datetime .fromisoformat (text )
        except Exception :
            return None 

    def _assignment_recency_ts (self ,a ):
        for key in ('graded_at','submitted_at','due','updated_at','created_at'):
            dt =self ._parse_canvas_datetime (a .get (key ))
            if dt is not None :
                return dt .timestamp ()
        return 0 

    def _grading_period_number (self ,name ):
        if not name :
            return None 
        text =str (name ).upper ()
        for token in ('Q1','Q2','Q3','Q4'):
            if token in text :
                return int (token [1 ])
        for num in range (1 ,5 ):
            if f"QUARTER {num }"in text or f"QTR {num }"in text :
                return num 
        for ch in text :
            if ch in "1234":
                return int (ch )
        return None 

    def _sort_assignments_by_quarter_and_recency (self ,assigns ):
        def sort_key (a ):
            period_name =a .get ('grading_period')or a .get ('grading_period_name')
            period_num =self ._grading_period_number (period_name )
            bucket =0 if period_num is not None else 1 
            period_order =-period_num if period_num is not None else 0 
            return (bucket ,period_order ,-self ._assignment_recency_ts (a ))

        return sorted (assigns ,key =sort_key )

    def _format_score (self ,a ):
        score =a .get ('score')
        points =a .get ('points')
        if score is None or points is None :
            entered =a .get ('entered')
            return entered [:6 ]if entered else "--"
        try :
            return f"{int (round (score ))}/{int (round (points ))}"
        except Exception :
            return f"{score }/{points }"

    def _canvas_load_config (self ):
        try :
            if not os .path .exists (self .canvas_config_path ):
                return None 
            with open (self .canvas_config_path ,'r')as f :
                cfg =_json .load (f )
            base =cfg .get ('base_url')
            token =cfg .get ('api_token')
            if not base or not token :
                return None 
            if not base .startswith ('http'):
                base ='https://'+base 
            return {'base_url':base .rstrip ('/'),'api_token':token }
        except Exception :
            return None 

    def _canvas_request (self ,cfg ,path ,params =None ):
        try :
            s =requests .Session ()
            s .headers .update ({'Authorization':f"Bearer {cfg ['api_token']}",'Accept':'application/json'})
            url =urljoin (cfg ['base_url']+'/','api/v1/'+path .lstrip ('/'))
            results =[]
            while url :
                r =s .get (url ,params =params ,timeout =5 )
                if r .status_code ==429 :
                    time .sleep (1 )
                    r =s .get (url ,params =params ,timeout =5 )
                if r .status_code >=400 :
                    return None 
                data =r .json ()
                if isinstance (data ,list ):
                    results .extend (data )
                else :
                    results .append (data )

                link =r .headers .get ('Link','')
                next_url =None 
                for part in link .split (','):
                    if 'rel="next"'in part :
                        next_url =part [part .find ('<')+1 :part .find ('>')]
                        break 
                url =next_url 
                params =None 
            return results 
        except Exception :
            return None 

    def _read_cache (self ):
        try :
            if os .path .exists (self .canvas_cache_path ):
                with open (self .canvas_cache_path ,'r')as f :
                    return _json .load (f )
        except Exception :
            pass 
        return {}

    def _write_cache (self ,data ):
        try :
            with open (self .canvas_cache_path ,'w')as f :
                _json .dump (data ,f )
        except Exception :
            pass 

    def _canvas_fetch_courses (self ,cfg ):
        cache =self ._read_cache ()
        now_ts =time .time ()
        c_entry =cache .get ('courses')
        if c_entry and now_ts <c_entry .get ('expires',0 ):
            return c_entry .get ('data',[])
        data =self ._canvas_request (cfg ,'users/self/courses',params ={'include[]':['enrollments','total_scores'],'enrollment_state':'active','per_page':50 })
        if data is None :
            return None 
        courses =[]
        for c in data :
            name =c .get ('name')or c .get ('course_code')or 'Course'
            percent =None 
            grade_text =None 


            for e in c .get ('enrollments',[]):
                if e .get ('computed_current_period_score')is not None :
                    percent =e ['computed_current_period_score']
                    break 
                if e .get ('current_period_score')is not None :
                    percent =e ['current_period_score']
                    break 
                if e .get ('computed_current_score')is not None :
                    percent =e ['computed_current_score']
                    break 
                if e .get ('current_score')is not None :
                    percent =e ['current_score']
                    break 
                if e .get ('computed_final_score')is not None :
                    percent =e ['computed_final_score']
                    break 
                if e .get ('final_score')is not None :
                    percent =e ['final_score']
                    break 

                if grade_text is None :
                    grade_text =e .get ('computed_current_period_grade')or e .get ('current_period_grade')or e .get ('computed_current_grade')or e .get ('current_grade')or e .get ('computed_final_grade')or e .get ('final_grade')


            if percent is None :
                g =c .get ('grades')or {}
                percent =g .get ('current_period_score')or g .get ('current_score')or g .get ('final_score')
                if grade_text is None :
                    grade_text =g .get ('current_period_grade')or g .get ('current_grade')or g .get ('final_grade')

            courses .append ({'id':c .get ('id'),'name':name ,'percent':percent if percent is not None else grade_text })
        cache ['courses']={'data':courses ,'expires':now_ts +600 }
        self ._write_cache (cache )
        return courses 

    def _canvas_fetch_assignments (self ,cfg ,course_id ):
        cache =self ._read_cache ()
        now_ts =time .time ()
        a_key =f'assigns_{course_id }'
        a_entry =cache .get (a_key )
        if a_entry and now_ts <a_entry .get ('expires',0 ):
            return a_entry .get ('data',[])
        data =self ._canvas_request (cfg ,f'courses/{course_id }/assignments',params ={'include[]':'submission','per_page':50 })
        if data is None :
            return None 
        grading_periods =self ._canvas_fetch_grading_periods (cfg ,course_id )
        assigns =[]
        for a in data :
            sub =a .get ('submission')or {}
            period_id =a .get ('grading_period_id')
            period_name =grading_periods .get (period_id )if grading_periods else None 
            assigns .append ({
            'id':a .get ('id'),
            'name':a .get ('name')or 'Assignment',
            'points':a .get ('points_possible'),
            'score':sub .get ('score'),
            'entered':sub .get ('entered_grade'),
            'status':sub .get ('workflow_state'),
            'due':a .get ('due_at'),
            'submitted_at':sub .get ('submitted_at'),
            'graded_at':sub .get ('graded_at'),
            'updated_at':a .get ('updated_at'),
            'created_at':a .get ('created_at'),
            'grading_period_id':period_id ,
            'grading_period':period_name ,
            })
        cache [a_key ]={'data':assigns ,'expires':now_ts +300 }
        self ._write_cache (cache )
        return assigns 

    def _canvas_fetch_grading_periods (self ,cfg ,course_id ):
        cache =self ._read_cache ()
        now_ts =time .time ()
        p_key =f'grading_periods_{course_id }'
        p_entry =cache .get (p_key )
        if p_entry and now_ts <p_entry .get ('expires',0 ):
            return p_entry .get ('data',{})
        data =self ._canvas_request (cfg ,f'courses/{course_id }/grading_periods')
        if data is None :
            return {}
        periods_data =[]
        for item in data :
            if isinstance (item ,dict )and item .get ('grading_periods'):
                periods_data .extend (item .get ('grading_periods')or [])
            elif isinstance (item ,dict ):
                periods_data .append (item )
        periods ={}
        for period in periods_data :
            pid =period .get ('id')if isinstance (period ,dict )else None 
            title =period .get ('title')if isinstance (period ,dict )else None 
            if pid is not None and title :
                periods [pid ]=title 
        cache [p_key ]={'data':periods ,'expires':now_ts +1800 }
        self ._write_cache (cache )
        return periods 

    def show_theme_menu (self ):
        wifi_connected =self ._get_wifi_connected ()
        max_visible =6 

        if self .selected_index <self .theme_scroll_offset :
            self .theme_scroll_offset =self .selected_index 
        elif self .selected_index >=self .theme_scroll_offset +max_visible :
            self .theme_scroll_offset =self .selected_index -max_visible +1 
        self .display .show_menu (self .theme_menu_items ,self .selected_index ,"Theme",
        nav_items =self .nav_items ,nav_selected_index =self .nav_selected_index ,
        start_index =self .theme_scroll_offset ,max_visible =max_visible ,
        wifi_connected =wifi_connected )

    def handle_theme_input (self ,action ):
        if action =='up':
            self .selected_index =(self .selected_index -1 )%len (self .theme_menu_items )
            self .show_theme_menu ()
        elif action =='down':
            self .selected_index =(self .selected_index +1 )%len (self .theme_menu_items )
            self .show_theme_menu ()
        elif action =='select'or action =='right':
            selected_theme =self .theme_menu_items [self .selected_index ]
            self .theme_manager .set_theme (selected_theme )
            wifi_connected =self ._get_wifi_connected ()
            self .display .show_message ("Theme Set",f"Changed to\n{selected_theme .title ()}",
            self .theme_manager .get_success (),self .nav_items ,self .nav_selected_index ,wifi_connected )
            time .sleep (1 )
            self .current_screen ="appearance"

            self .selected_index =0 
            self .theme_scroll_offset =0 
            self .show_appearance_menu ()
        elif action =='left':
            self .current_screen ="appearance"
            self .selected_index =0 
            self .theme_scroll_offset =0 
            self .show_appearance_menu ()

    def show_appearance_menu (self ):
        """Display appearance submenu with Colors and Fonts options"""
        wifi_connected =self ._get_wifi_connected ()
        self .display .show_menu (self .appearance_menu_items ,self .selected_index ,"Appearance",
        nav_items =self .nav_items ,nav_selected_index =self .nav_selected_index ,
        wifi_connected =wifi_connected )

    def handle_appearance_input (self ,action ):
        """Handle input for appearance submenu"""
        if action =='up':
            self .selected_index =(self .selected_index -1 )%len (self .appearance_menu_items )
            self .show_appearance_menu ()
        elif action =='down':
            self .selected_index =(self .selected_index +1 )%len (self .appearance_menu_items )
            self .show_appearance_menu ()
        elif action =='select'or action =='right':
            selected_item =self .appearance_menu_items [self .selected_index ]
            if selected_item =="Colors":
                self .current_screen ="theme"
                self .selected_index =0 
                self .theme_scroll_offset =0 
                self .show_theme_menu ()
            elif selected_item =="Fonts":
                self .current_screen ="fonts"
                self .selected_index =0 
                self .font_scroll_offset =0 
                self .show_font_menu ()
        elif action =='left':
            self .current_screen ="settings"
            self .selected_index =self .settings_menu_items .index ("Appearance")if "Appearance"in self .settings_menu_items else 2 
            self .show_settings_menu ()

    def show_font_menu (self ):
        """Display font selection menu"""
        wifi_connected =self ._get_wifi_connected ()

        self .font_menu_items =self .font_manager .get_font_names ()
        max_visible =6 
        if self .selected_index <self .font_scroll_offset :
            self .font_scroll_offset =self .selected_index 
        elif self .selected_index >=self .font_scroll_offset +max_visible :
            self .font_scroll_offset =self .selected_index -max_visible +1 
        self .display .show_menu (self .font_menu_items ,self .selected_index ,"Fonts",
        nav_items =self .nav_items ,nav_selected_index =self .nav_selected_index ,
        start_index =self .font_scroll_offset ,max_visible =max_visible ,
        wifi_connected =wifi_connected )

    def handle_font_input (self ,action ):
        """Handle input for font selection menu"""
        if action =='up':
            self .selected_index =(self .selected_index -1 )%len (self .font_menu_items )
            self .show_font_menu ()
        elif action =='down':
            self .selected_index =(self .selected_index +1 )%len (self .font_menu_items )
            self .show_font_menu ()
        elif action =='select'or action =='right':
            selected_font =self .font_menu_items [self .selected_index ]
            self .font_manager .set_font (selected_font )

            self .display .reload_fonts ()
            wifi_connected =self ._get_wifi_connected ()
            self .display .show_message ("Font Set",f"Changed to\\n{selected_font }",
            self .theme_manager .get_success (),self .nav_items ,
            self .nav_selected_index ,wifi_connected )
            time .sleep (1 )
            self .current_screen ="appearance"

            self .selected_index =1 
            self .font_scroll_offset =0 
            self .show_appearance_menu ()
        elif action =='left':
            self .current_screen ="appearance"
            self .selected_index =1 
            self .font_scroll_offset =0 
            self .show_appearance_menu ()

    def show_progress_bar_menu (self ):
        """Display progress bar mode selection"""
        current_mode =self .progress_bar_modes [self .progress_bar_mode_index ]
        if current_mode =="time_in_class":
            mode_display ="In Class"
        elif current_mode =="time_in_day":
            mode_display ="In Day"
        elif current_mode =="lunch_day":
            mode_display ="Lunch/Day"
        else :
            mode_display =current_mode .replace ("_"," ").title ()
        message =f"Progress Bar:\n{mode_display }\n\nUp/Down: Change\nSelect: Confirm"
        self .display .show_message ("Progress Bar",message ,(100 ,150 ,255 ),self .nav_items ,self .nav_selected_index )

    def handle_progress_bar_input (self ,action ):
        if action =='up':
            self .progress_bar_mode_index =(self .progress_bar_mode_index -1 )%len (self .progress_bar_modes )
            self .progress_bar_mode =self .progress_bar_modes [self .progress_bar_mode_index ]
            self .show_progress_bar_menu ()
        elif action =='down':
            self .progress_bar_mode_index =(self .progress_bar_mode_index +1 )%len (self .progress_bar_modes )
            self .progress_bar_mode =self .progress_bar_modes [self .progress_bar_mode_index ]
            self .show_progress_bar_menu ()
        elif action =='select'or action =='right':
            self .current_screen ="settings"
            self .selected_index =self .settings_menu_items .index ("Progress Bar")if "Progress Bar"in self .settings_menu_items else 3 
            self .show_settings_menu ()
        elif action =='left':
            self .current_screen ="settings"
            self .selected_index =self .settings_menu_items .index ("Progress Bar")if "Progress Bar"in self .settings_menu_items else 3 
            self .show_settings_menu ()

    def show_backlight_menu (self ):
        """Display and adjust backlight brightness percentage."""
        try :
            bl =int (max (5 ,min (100 ,getattr (self ,'backlight',100 ))))
        except Exception :
            bl =100 
        msg =f"Brightness: {bl }%\nMay cause flickering\n\nUp/Down: +/-5%\nSelect: Done"
        wifi_connected =self ._get_wifi_connected ()
        self .display .show_message ("Brightness",msg ,(150 ,200 ,255 ),self .nav_items ,self .nav_selected_index ,wifi_connected )

    def handle_backlight_input (self ,action ):
        changed =False 
        if action =='up':
            self .backlight =int (min (100 ,(self .backlight if hasattr (self ,'backlight')else 100 )+5 ))
            changed =True 
        elif action =='down':
            self .backlight =int (max (5 ,(self .backlight if hasattr (self ,'backlight')else 100 )-5 ))
            changed =True 
        elif action in ('select','right','left'):

            try :
                self ._save_state ()
            except Exception :
                pass 
            self .current_screen ='settings'

            try :
                self .selected_index =self .settings_menu_items .index ('Brightness')
            except Exception :
                self .selected_index =0 
            self .show_settings_menu ()
            return 

        if changed :

            try :
                self .display .set_backlight (int (self .backlight ))
            except Exception :
                pass 
            self .show_backlight_menu ()

    def restart_program (self ):
        """Restart the Timagotchi program"""
        try :
            self .display .show_message ("Restarting","Program restarting...",(100 ,200 ,255 ),self .nav_items ,self .nav_selected_index )
            time .sleep (1 )
            self .input_handler .cleanup ()
            self .running =False 

            os .execv (sys .executable ,[sys .executable ]+sys .argv )
        except Exception as e :
            self .display .show_message ("Error",f"Restart failed: {str (e )[:30 ]}",(255 ,100 ,100 ),self .nav_items ,self .nav_selected_index )
            time .sleep (2 )
            self .current_screen ="settings"
            self .selected_index =self .settings_menu_items .index ("Restart")if "Restart"in self .settings_menu_items else 2 
            self .show_settings_menu ()

    def apply_manual_time (self ):
        """Apply the manually set time"""
        try :

            ntp_check =subprocess .run (['timedatectl','show','-p','NTP'],
            capture_output =True ,text =True ,timeout =5 )
            ntp_enabled ="yes"in ntp_check .stdout .lower ()

            if ntp_enabled :

                subprocess .run (['sudo','timedatectl','set-ntp','off'],
                capture_output =True ,text =True ,timeout =5 ,check =False )
                time .sleep (1 )


            time_str =f"{self .adjust_hour :02d}:{self .adjust_minute :02d}:00"

            result =subprocess .run (['sudo','timedatectl','set-time',time_str ],
            capture_output =True ,text =True ,timeout =10 )

            if result .returncode !=0 :
                error_msg =result .stderr .strip ()
                if "ntp"in error_msg .lower ()or "synchronized"in error_msg .lower ():
                    self .last_sync_error ="Run: sudo timedatectl\nset-ntp false"
                    self .display .show_message ("Failed",self .last_sync_error ,(255 ,100 ,100 ),self .nav_items ,self .nav_selected_index )
                else :
                    self .last_sync_error =error_msg if error_msg else "Failed to set time"
                    self .display .show_message ("Failed",self .last_sync_error [:40 ],(255 ,100 ,100 ),self .nav_items ,self .nav_selected_index )
            else :
                self .last_sync_error =None 

                if USE_24_HOUR :
                    display_time =time_str 
                else :
                    display_hour =self .adjust_hour %12 
                    if display_hour ==0 :
                        display_hour =12 
                    am_pm ="AM"if self .adjust_hour <12 else "PM"
                    display_time =f"{display_hour :02d}:{self .adjust_minute :02d} {am_pm }"
                self .display .show_message ("Time Set",f"Set to {display_time }",(100 ,255 ,100 ),self .nav_items ,self .nav_selected_index )


            time .sleep (2 )

            current_time =time .time ()
            for pin in self .input_handler .pins :
                self .input_handler .last_press [pin ]=current_time 
        except subprocess .TimeoutExpired :
            self .last_sync_error ="Operation timed out"
            self .display .show_message ("Failed","Timeout",(255 ,100 ,100 ),self .nav_items ,self .nav_selected_index )
            time .sleep (2 )

            current_time =time .time ()
            for pin in self .input_handler .pins :
                self .input_handler .last_press [pin ]=current_time 
        except Exception as e :
            self .last_sync_error =str (e )
            self .display .show_message ("Error",str (e )[:40 ],(255 ,100 ,100 ),self .nav_items ,self .nav_selected_index )
            time .sleep (2 )

            current_time =time .time ()
            for pin in self .input_handler .pins :
                self .input_handler .last_press [pin ]=current_time 

    def sync_time_now (self ):
        """Enable NTP sync now and report status."""
        try :

            result =subprocess .run (['sudo','timedatectl','set-ntp','true'],capture_output =True ,text =True ,timeout =10 )
            if result .returncode !=0 :
                err =result .stderr .strip ()or result .stdout .strip ()
                self .display .show_message ("Sync Failed",err [:40 ],(255 ,100 ,100 ),self .nav_items ,self .nav_selected_index )
                time .sleep (2 )
                return 

            time .sleep (2 )

            check =subprocess .run (['timedatectl','show','-p','NTPSynchronized','-p','NTP'],capture_output =True ,text =True ,timeout =5 )
            out =check .stdout .strip ()
            if 'NTPSynchronized=yes'in out or 'NTPSynchronized=true'in out :
                self .display .show_message ("Synced","Time synchronized",(100 ,255 ,100 ),self .nav_items ,self .nav_selected_index )
            else :
                self .display .show_message ("Sync","NTP enabled. Syncing...",(150 ,200 ,255 ),self .nav_items ,self .nav_selected_index )
            time .sleep (2 )
        except Exception as e :
            self .display .show_message ("Sync Error",str (e )[:40 ],(255 ,100 ,100 ),self .nav_items ,self .nav_selected_index )
            time .sleep (2 )

    def _update_wifi_state (self ):
        """Force an immediate wifi state refresh (used on boot).

        This does a single quick nmcli query and updates the cached state and timestamp.
        """
        try :
            result =subprocess .run (['nmcli','-t','-f','STATE','g'],capture_output =True ,text =True ,timeout =1 )
            state =result .stdout .strip ().lower ()
            self ._wifi_state ='connected'in state 
        except Exception :
            pass 
        finally :
            self ._wifi_checked_at =time .time ()

    def run (self ):
        import time 
        self .show_main_menu ()

        last_update =time .time ()
        update_interval =1.0 

        while self .running :
            action =self .input_handler .get_input ()
            now_ts =time .time ()
            if action :
                self ._last_input_time =now_ts 

            if action :


                if action in ('key1','key2','key3')and self .current_screen not in (
                'developer',
                'secret_menu',
                'wifi_password',
                'set_time'
                ):
                    if action =='key1':
                        self .current_screen ='main'
                        self .nav_selected_index =self .nav_items .index ('Main Page')if 'Main Page'in self .nav_items else 0 
                        self .show_main_menu ()
                        continue 
                    elif action =='key2':
                        self .current_screen ='tools'
                        self .nav_selected_index =self .nav_items .index ('Tools')if 'Tools'in self .nav_items else 1 
                        self .selected_index =0 
                        self .tools_scroll_offset =0 
                        self .show_tools_menu ()
                        continue 
                    elif action =='key3':
                        self .current_screen ='settings'
                        self .nav_selected_index =self .nav_items .index ('Settings')if 'Settings'in self .nav_items else 2 
                        self .selected_index =0 
                        self .show_settings_menu ()
                        continue 
                if self .current_screen =="main":
                    self .handle_main_menu_input (action )
                elif self .current_screen =="schedule":
                    self .handle_schedule_input (action )
                elif self .current_screen =="clock":
                    self .handle_clock_input (action )
                elif self .current_screen =="tools":
                    self .handle_tools_input (action )
                elif self .current_screen =="settings":
                    self .handle_settings_input (action )
                elif self .current_screen =="wifi":
                    self .handle_wifi_input (action )
                elif self .current_screen =="wifi_password":
                    self .handle_wifi_password_input (action )
                elif self .current_screen =="ab_day":
                    self .handle_ab_day_input (action )
                elif self .current_screen =="appearance":
                    self .handle_appearance_input (action )
                elif self .current_screen =="theme":
                    self .handle_theme_input (action )
                elif self .current_screen =="fonts":
                    self .handle_font_input (action )
                elif self .current_screen =="progress_bar":
                    self .handle_progress_bar_input (action )
                elif self .current_screen =="backlight":
                    self .handle_backlight_input (action )
                elif self .current_screen =="set_time_menu":
                    self .handle_set_time_menu_input (action )
                elif self .current_screen =="set_time":
                    self .handle_set_time_input (action )
                elif self .current_screen =="grades":
                    self .handle_grades_input (action )
                elif self .current_screen =="assignments":
                    self .handle_assignments_input (action )
                elif self .current_screen =="stopwatch":
                    self .handle_stopwatch_input (action )
                elif self .current_screen =="version":
                    self .handle_version_input (action )
                elif self .current_screen =="version_info":
                    self .handle_version_info_input (action )
                elif self .current_screen =="developer":
                    self .handle_developer_input (action )
                elif self .current_screen =="secret_menu":
                    self .handle_secret_menu_input (action )

            current_time =time .time ()
            if current_time -last_update >update_interval :
                if self .current_screen =="schedule":
                    self .show_schedule_screen ()
                elif self .current_screen =="clock":
                    self .show_clock_screen ()
                elif self .current_screen =="main":
                    self .show_main_menu ()
                elif self .current_screen =="stopwatch":
                    self .show_stopwatch ()
                last_update =current_time 

            time .sleep (0.05 )

        self .input_handler .cleanup ()
